import base64
from django.core.files.base import ContentFile
import uuid

def decode_base64_image(data_url):
    """
    Decodes a base64 image data URL into a Django ContentFile
    Returns (ContentFile, extension)
    """
    try:
        format, imgstr = data_url.split(';base64,')
        ext = format.split('/')[-1]
        data = base64.b64decode(imgstr)
        file_name = f"{uuid.uuid4()}.{ext}"
        return ContentFile(data, name=file_name)
    except Exception as e:
        return None

def generate_session_title(message_content):
    """
    Generates a short title based on the first user message.
    """
    title = message_content.strip()
    if len(title) > 40:
        title = title[:37] + "..."
    if not title:
        title = "New Look"
    return title
