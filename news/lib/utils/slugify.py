import slugify


def make_slug(s):
    slugged = slugify.slugify(s)
    return slugged[:min(100, len(slugged))]


def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)