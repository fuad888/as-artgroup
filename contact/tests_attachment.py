"""Customers may attach a brief; the server decides what is acceptable."""

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from contact.models import ContactMessage
from core.testing import BaseTestCase

PDF = b"%PDF-1.4 fake brief"


def upload(name, content=PDF, content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


BASE = {"name": "Test", "email": "t@example.com",
        "phone": "+994501234567", "message": "brif əlavə etdim"}


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
                   CONTACT_NOTIFY_EMAIL="office@as-artgroup.az")
class AttachmentUploadTests(BaseTestCase):
    def _post(self, **extra):
        return self.client.post("/api/v1/contact/messages/", {**BASE, **extra})

    def test_a_pdf_is_accepted_and_stored(self):
        response = self._post(attachment=upload("brief.pdf"))
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ContactMessage.objects.get().attachment.name)

    def test_word_and_excel_are_accepted(self):
        for name in ["brief.doc", "brief.docx", "data.xls", "data.xlsx"]:
            with self.subTest(name=name):
                self.cache_clear() if hasattr(self, "cache_clear") else None
                from django.core.cache import cache
                cache.clear()
                response = self._post(attachment=upload(name), email=f"{name}@example.com")
                self.assertEqual(response.status_code, 201, response.content)

    def test_an_executable_is_refused(self):
        """The accept= attribute is a convenience; this is the control."""
        response = self._post(attachment=upload("payload.exe", b"MZ", "application/x-msdownload"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("attachment", response.json())
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_a_renamed_script_is_refused_on_its_extension(self):
        for name in ["shell.php", "run.sh", "app.js", "archive.zip", "photo.svg"]:
            with self.subTest(name=name):
                from django.core.cache import cache
                cache.clear()
                self.assertEqual(self._post(attachment=upload(name)).status_code, 400)

    def test_an_oversized_file_is_refused(self):
        big = upload("huge.pdf", b"x" * (10 * 1024 * 1024 + 1))
        self.assertEqual(self._post(attachment=big).status_code, 400)

    def test_the_attachment_stays_optional(self):
        self.assertEqual(self._post().status_code, 201)
        self.assertFalse(ContactMessage.objects.get().attachment)

    def test_the_notification_names_the_file(self):
        with self.captureOnCommitCallbacks(execute=True):
            self._post(attachment=upload("brief.pdf"))
        self.assertIn("brief", mail.outbox[0].body)

    def test_the_notification_says_so_when_there_is_none(self):
        with self.captureOnCommitCallbacks(execute=True):
            self._post()
        self.assertIn("yoxdur", mail.outbox[0].body)


class AttachmentFormTests(BaseTestCase):
    def test_the_no_js_form_accepts_a_file_too(self):
        response = self.client.post(
            "/az/elaqe/submit/", {**BASE, "attachment": upload("brief.pdf")}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ContactMessage.objects.get().attachment)

    def test_the_no_js_form_refuses_a_bad_file(self):
        self.client.post("/az/elaqe/submit/", {**BASE, "attachment": upload("x.exe")})
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_the_form_can_carry_files(self):
        html = self.client.get("/az/elaqe/").content.decode()
        self.assertIn('enctype="multipart/form-data"', html)
        self.assertIn('name="attachment"', html)
        self.assertIn('type="file"', html)
