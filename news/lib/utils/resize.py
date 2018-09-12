import io

from PIL import Image


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


def square_crop(img, size=(256,256)):
    """
    Create square crop from the image of given size
    :param img: image to crop
    :param size: size
    :return: squared image
    """
    img.thumbnail(size, Image.ANTIALIAS)
    background = Image.new('RGBA', size, (255, 255, 255, 0))
    background.paste(
        img, (int((size[0] - img.size[0]) / 2), int((size[1] - img.size[1]) / 2))
    )
    return img