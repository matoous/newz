import io

from PIL import Image
from flask import current_app


IMAGE_WIDTHS = [800, 1200, 1920]

def create_feed_images(data):
    img = Image.open(data)
    return [{'data': resize_image(img, size).getvalue(), 'size': size} for size in IMAGE_WIDTHS]

def resize_image(img, width):
    resize_ratio = width / img.width
    size = int(img.width * resize_ratio), int(img.height * resize_ratio)
    img.thumbnail(size, Image.ANTIALIAS)
    in_mem_file = io.BytesIO()
    img.save(in_mem_file, format="PNG")
    return in_mem_file