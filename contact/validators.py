import re

from django.core.exceptions import ValidationError

PHONE_ALLOWED_CHARS_RE = re.compile(r"^[\d\s+()\-.]+$")


def validate_phone(value):
    """Mirrors the original front-end JS validation rule exactly:
    strip everything but digits, require 9-15 digits, and reject any
    character outside digits/space/+/()/-/. in the raw input.
    """
    if not PHONE_ALLOWED_CHARS_RE.match(value or ""):
        raise ValidationError("Telefon nömrəsi düzgün görünmür. Nümunə: +994 50 000 00 00")

    digits_only = re.sub(r"\D", "", value or "")
    if not (9 <= len(digits_only) <= 15):
        raise ValidationError("Telefon nömrəsi düzgün görünmür. Nümunə: +994 50 000 00 00")


# A brief is a document, not an executable. Keeping this to an explicit list
# means an upload can never be something the server or a viewer might run.
ATTACHMENT_EXTENSIONS = ("pdf", "doc", "docx", "xls", "xlsx")
ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024


def validate_attachment(value):
    """Extension and size. Both are checked server-side because the accept=
    attribute and the JS check in front of it are conveniences, not controls."""
    name = getattr(value, "name", "") or ""
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if extension not in ATTACHMENT_EXTENSIONS:
        raise ValidationError(
            "Yalnız PDF, Word və Excel faylları qəbul olunur "
            "(%s)." % ", ".join(e.upper() for e in ATTACHMENT_EXTENSIONS)
        )

    size = getattr(value, "size", 0) or 0
    if size > ATTACHMENT_MAX_BYTES:
        raise ValidationError(
            "Fayl çox böyükdür (%.1f MB). Maksimum %d MB."
            % (size / 1024 / 1024, ATTACHMENT_MAX_BYTES // 1024 // 1024)
        )
