import warnings
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


def validate_image_upload(upload):
    if upload.size > settings.MAX_UPLOAD_SIZE:
        raise ValidationError("Images must be 5 MiB or smaller.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                image_format = image.format
                if image.width * image.height > settings.MAX_IMAGE_PIXELS:
                    raise ValidationError("Image dimensions are too large.")
                image.verify()
    except (Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise ValidationError("Image dimensions are too large.") from error
    except (UnidentifiedImageError, OSError) as error:
        raise ValidationError("Upload a valid JPEG, PNG, or WebP image.") from error
    finally:
        upload.seek(0)

    if image_format not in {"JPEG", "PNG", "WEBP"}:
        raise ValidationError("Upload a valid JPEG, PNG, or WebP image.")


def _image_upload_path(folder, instance, filename):
    image_file = instance.image.file
    try:
        image = Image.open(image_file)
        extension = Image.EXTENSION.get(image.format, ".img").lstrip(".")
    except (UnidentifiedImageError, OSError):
        extension = Path(filename).suffix.lstrip(".").lower() or "img"
    finally:
        image_file.seek(0)
    return f"{folder}/{uuid4().hex}.{extension}"


def post_image_upload_path(instance, filename):
    return _image_upload_path("posts", instance, filename)


def campaign_image_upload_path(instance, filename):
    return _image_upload_path("campaigns", instance, filename)
