import requests
import typing as t

BASE_URL = 'https://www.gradescope.com/'

class PageNotFound(Exception):
    pass


def handle_api_error(res: requests.Response):
    if res.status_code != 200 or res.url == BASE_URL:
        raise PageNotFound("Page doesn't exist or inaccessible!")
