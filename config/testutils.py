from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def make_image_upload(name="small.png", image_format="PNG", color="teal"):
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color).save(buffer, format=image_format)
    content_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[
        image_format
    ]
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)
