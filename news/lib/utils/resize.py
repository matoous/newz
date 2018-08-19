import io

from PIL import Image
from flask import current_app


def create_feed_logo(data):
    img = Image.open(data)
    resize_ratio = min(current_app.config['FEED_LOGO_SIZE'][0] / img.width, current_app.config['FEED_LOGO_SIZE'][1] / img.height)
    size = int(img.width * resize_ratio), int(img.height * resize_ratio)
    img.thumbnail(size, Image.ANTIALIAS)
    in_mem_file = io.BytesIO()
    img.save(in_mem_file, format="PNG")
    return in_mem_file.getvalue()