from urllib.parse import urlparse, urljoin

from flask import request


def redirect_back(default='index'):
    url = request.args.get('next') or request.referrer
    return url if is_safe_url(url) else default

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc