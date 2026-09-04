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
