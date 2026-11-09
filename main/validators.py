from django.core.exceptions import ValidationError
from django.utils.html import strip_tags


def clean_skill_text(value):
    """Use the same text validation for the API and legacy Skill forms."""
    value = strip_tags(value).strip()
    if not value:
        raise ValidationError("Field ini wajib berisi teks, bukan hanya spasi atau tag HTML.")
    return value
