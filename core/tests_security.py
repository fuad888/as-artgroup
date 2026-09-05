from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, override_settings

from contact.models import ContactMessage
from core.models import SiteSettings
from core.testing import BaseTestCase
from projects.models import Project, ProjectCategory

XSS_SCRIPT = "<script>alert(1)</script>"
XSS_IMG = "<img src=x onerror=alert(1)>"


class XssTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.category = ProjectCategory.objects.create(name=XSS_SCRIPT, slug="xss-probe")
        Project.objects.create(title=XSS_IMG, category=self.category, is_featured=True)

    def test_admin_entered_content_is_escaped_in_templates(self):
        html = self.client.get("/az/").content.decode()
        self.assertNotIn(XSS_IMG, html)
        self.assertNotIn(XSS_SCRIPT, html)
        self.assertIn("&lt;img", html)

    def test_json_ld_cannot_break_out_of_its_script_tag(self):
        site_settings = SiteSettings.load()
        site_settings.site_name = "</script><script>alert(document.cookie)</script>"
        site_settings.save()

        html = self.client.get("/az/").content.decode()
        self.assertNotIn("</script><script>alert", html)
        self.assertIn("\\u003C", html)

    def test_project_detail_escapes_untrusted_content(self):
        project = Project.objects.get(title=XSS_IMG)
        html = self.client.get(project.get_absolute_url()).content.decode()
        self.assertNotIn(XSS_IMG, html)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CONTACT_NOTIFY_EMAIL="office@as-artgroup.az",
)
class EmailHeaderInjectionTests(BaseTestCase):
    def _submit(self, **overrides):
        payload = {
            "name": "Test",
            "email": "attacker@example.com",
            "phone": "+994 50 123 45 67",
            "message": "test",
            **overrides,
        }
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                "/api/v1/contact/messages/", payload, content_type="application/json"
            )

    def test_newline_in_name_cannot_add_mail_headers(self):
        """The payload may appear as text; what matters is that it never becomes
        a header or an extra recipient."""
        self._submit(name="Hacker\nBcc: victim@evil.com")

        for message in mail.outbox:
            self.assertEqual(message.recipients(), ["office@as-artgroup.az"])
            self.assertEqual(message.cc, [])
            self.assertEqual(message.bcc, [])
            headers = {k.lower() for k in message.message().keys()}
            self.assertNotIn("bcc", headers)
            self.assertNotIn("cc", headers)

    def test_newline_in_name_does_not_crash_the_endpoint(self):
        response = self._submit(name="Hacker\nBcc: victim@evil.com")
        self.assertIn(response.status_code, (201, 400))

    def test_reply_to_only_ever_holds_a_validated_address(self):
        self._submit()
        self.assertEqual(mail.outbox[0].reply_to, ["attacker@example.com"])

    def test_notification_still_sends_when_the_name_holds_a_newline(self):
        """Sanitising the subject beats dropping the mail: the team still gets told."""
        self._submit(name="Hacker\nBcc: victim@evil.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("\n", mail.outbox[0].subject)
        self.assertIn("Bcc: victim@evil.com", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["office@as-artgroup.az"])

    def test_message_body_newlines_are_preserved(self):
        self._submit(message="Birinci sətir\nİkinci sətir")
        self.assertIn("Birinci sətir\nİkinci sətir", mail.outbox[0].body)


class ApiExposureTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        ContactMessage.objects.create(
            name="Gizli Müştəri", email="lead@example.com",
            phone="+994501234567", message="Məxfi sorğu",
        )

    def test_contact_endpoint_refuses_to_list_leads(self):
        self.assertEqual(self.client.get("/api/v1/contact/messages/").status_code, 405)

    def test_no_public_endpoint_returns_lead_data(self):
        for path in self.client.get("/api/v1/").json().values():
            with self.subTest(path=path):
                response = self.client.get(path)
                if response.status_code == 200:
                    self.assertNotIn("Gizli Müştəri", response.content.decode())
                    self.assertNotIn("lead@example.com", response.content.decode())

    def test_site_settings_endpoint_exposes_no_credentials(self):
        data = self.client.get("/api/v1/core/site-settings/").json()
        leaked = [k for k in data if any(w in k.lower() for w in ("password", "secret", "token"))]
        self.assertEqual(leaked, [])


class AccessControlTests(BaseTestCase):
    def test_admin_is_closed_to_anonymous_visitors(self):
        for path in ["/admin/", "/admin/contact/contactmessage/", "/admin/auth/user/"]:
            with self.subTest(path=path):
                self.assertIn(self.client.get(path).status_code, (302, 403))

    def test_staff_flag_alone_does_not_grant_lead_access(self):
        user = get_user_model().objects.create_user(
            username="staffer", password="x8Kd!2mQvz", is_staff=True
        )
        self.client.force_login(user)
        self.assertIn(self.client.get("/admin/contact/contactmessage/").status_code, (302, 403))

    def test_csrf_is_enforced_on_the_no_js_form(self):
        strict = Client(enforce_csrf_checks=True)
        response = strict.post(
            "/az/elaqe/submit/",
            {"name": "X", "email": "x@example.com", "phone": "+994501234567", "message": "y"},
        )
        self.assertEqual(response.status_code, 403)


class RequestHardeningTests(BaseTestCase):
    @override_settings(ALLOWED_HOSTS=["localhost"])
    def test_unknown_host_header_is_rejected(self):
        response = Client(headers={"host": "evil.com"}).get("/az/")
        self.assertEqual(response.status_code, 400)

    def test_security_headers_are_present(self):
        response = self.client.get("/az/")
        self.assertIsNotNone(response.get("X-Frame-Options"))
        self.assertEqual(response.get("X-Content-Type-Options"), "nosniff")

    def test_error_pages_do_not_leak_a_traceback(self):
        response = self.client.get("/az/movcud-olmayan-sehife-12345/")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"Traceback", response.content)

    def test_contact_endpoint_is_rate_limited(self):
        codes = []
        for i in range(7):
            codes.append(
                self.client.post(
                    "/api/v1/contact/messages/",
                    {"name": f"T{i}", "email": f"t{i}@example.com",
                     "phone": "+994501234567", "message": "test"},
                    content_type="application/json",
                ).status_code
            )
        self.assertIn(429, codes)


class SecretsTests(BaseTestCase):
    def test_secret_key_is_not_a_django_placeholder(self):
        from django.conf import settings

        self.assertNotIn("django-insecure", settings.SECRET_KEY)
        self.assertGreaterEqual(len(settings.SECRET_KEY), 40)

    @override_settings(
        DEBUG=False,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31536000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
    )
    def test_production_configuration_passes_djangos_deploy_checks(self):
        """Same checks `manage.py check --deploy` runs, asserted in CI."""
        from django.core.checks import Tags, registry

        issues = [
            str(m)
            for m in registry.run_checks(tags=[Tags.security], include_deployment_checks=True)
            if m.is_serious()
        ]
        self.assertEqual(issues, [])
