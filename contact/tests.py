from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import override_settings

from core.models import SiteSettings
from core.testing import BaseTestCase

from contact.models import ContactMessage
from contact.notifications import notification_recipients
from contact.validators import validate_phone

VALID_PAYLOAD = {
    "name": "Test İstifadəçi",
    "email": "test@example.com",
    "phone": "+994 50 123 45 67",
    "message": "Salam, test mesajı.",
}


class PhoneValidatorTests(BaseTestCase):
    def test_accepts_formats_the_original_js_accepted(self):
        for value in ["+994 50 123 45 67", "0501234567", "(012) 000-00-00", "+994.50.123.45.67"]:
            validate_phone(value)

    def test_rejects_too_few_digits(self):
        with self.assertRaises(ValidationError):
            validate_phone("12345")

    def test_rejects_too_many_digits(self):
        with self.assertRaises(ValidationError):
            validate_phone("1234567890123456")

    def test_rejects_letters(self):
        with self.assertRaises(ValidationError):
            validate_phone("+994 50 ABC 45 67")

    def test_rejects_empty(self):
        with self.assertRaises(ValidationError):
            validate_phone("")


class ContactAPITests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_valid_payload_creates_message(self):
        response = self.client.post(
            "/api/v1/contact/messages/", VALID_PAYLOAD, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_invalid_email_and_phone_return_field_errors(self):
        response = self.client.post(
            "/api/v1/contact/messages/",
            {**VALID_PAYLOAD, "email": "not-an-email", "phone": "123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())
        self.assertIn("phone", response.json())
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_missing_fields_are_rejected(self):
        response = self.client.post(
            "/api/v1/contact/messages/", {"name": "Only name"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_endpoint_does_not_expose_lead_list(self):
        response = self.client.get("/api/v1/contact/messages/")
        self.assertEqual(response.status_code, 405)

    def test_throttle_blocks_after_five_submissions(self):
        for _ in range(5):
            response = self.client.post(
                "/api/v1/contact/messages/", VALID_PAYLOAD, content_type="application/json"
            )
            self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/api/v1/contact/messages/", VALID_PAYLOAD, content_type="application/json"
        )
        self.assertEqual(response.status_code, 429)


class ContactNotificationTests(BaseTestCase):
    def test_signal_calls_notification_hook_on_create_only(self):
        with patch("contact.signals.notify_new_contact_message") as notify:
            # on_commit callbacks need capturing: TestCase never commits.
            with self.captureOnCommitCallbacks(execute=True):
                message = ContactMessage.objects.create(**VALID_PAYLOAD)
            self.assertEqual(notify.call_count, 1)

            with self.captureOnCommitCallbacks(execute=True):
                message.is_handled = True
                message.save()
            self.assertEqual(notify.call_count, 1)

    def test_no_email_is_sent_before_the_transaction_commits(self):
        with patch("contact.signals.notify_new_contact_message") as notify:
            ContactMessage.objects.create(**VALID_PAYLOAD)
            notify.assert_not_called()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CONTACT_NOTIFY_EMAIL="office@as-artgroup.az",
)
class ContactEmailTests(BaseTestCase):
    def _submit(self):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                "/api/v1/contact/messages/", VALID_PAYLOAD, content_type="application/json"
            )

    def test_submission_emails_the_office(self):
        self._submit()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["office@as-artgroup.az"])

    def test_email_contains_every_submitted_field(self):
        self._submit()
        body = mail.outbox[0].body
        for value in [VALID_PAYLOAD["name"], VALID_PAYLOAD["email"],
                      VALID_PAYLOAD["phone"], VALID_PAYLOAD["message"]]:
            self.assertIn(value, body)

    def test_subject_names_the_sender(self):
        self._submit()
        self.assertIn(VALID_PAYLOAD["name"], mail.outbox[0].subject)

    def test_reply_goes_straight_to_the_customer(self):
        self._submit()
        self.assertEqual(mail.outbox[0].reply_to, [VALID_PAYLOAD["email"]])

    def test_email_links_to_the_admin_record(self):
        self._submit()
        message = ContactMessage.objects.get()
        self.assertIn(f"/admin/contact/contactmessage/{message.pk}/change/", mail.outbox[0].body)

    def test_invalid_submission_sends_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                "/api/v1/contact/messages/",
                {**VALID_PAYLOAD, "email": "bad"},
                content_type="application/json",
            )
        self.assertEqual(len(mail.outbox), 0)

    def test_a_broken_mail_server_never_breaks_the_submission(self):
        with patch("contact.notifications.EmailMessage.send", side_effect=OSError("smtp down")):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    "/api/v1/contact/messages/", VALID_PAYLOAD,
                    content_type="application/json",
                )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationRecipientTests(BaseTestCase):
    @override_settings(CONTACT_NOTIFY_EMAIL="")
    def test_falls_back_to_the_address_configured_in_admin(self):
        site_settings = SiteSettings.load()
        site_settings.email = "office@as-artgroup.az"
        site_settings.save()
        self.assertEqual(notification_recipients(), ["office@as-artgroup.az"])

    @override_settings(CONTACT_NOTIFY_EMAIL="leads@as-artgroup.az")
    def test_environment_override_wins(self):
        self.assertEqual(notification_recipients(), ["leads@as-artgroup.az"])

    @override_settings(CONTACT_NOTIFY_EMAIL="")
    def test_no_recipient_configured_skips_sending(self):
        site_settings = SiteSettings.load()
        site_settings.email = ""
        site_settings.save()
        with self.captureOnCommitCallbacks(execute=True):
            ContactMessage.objects.create(**VALID_PAYLOAD)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ContactMessage.objects.count(), 1)


class ContactFallbackViewTests(BaseTestCase):
    def test_no_js_form_post_saves_and_redirects(self):
        response = self.client.post("/az/elaqe/submit/", VALID_PAYLOAD)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_no_js_form_post_with_invalid_data_does_not_save(self):
        response = self.client.post("/az/elaqe/submit/", {**VALID_PAYLOAD, "phone": "123"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 0)
