import requests

class Client:
    BASE_URL = 'https://www.gradescope.com'

    def __init__(self, session: requests.Session = None):
        self.session = session

    def _request(self, method, endpoint, **kwargs) -> requests.Response:

        url = f'{self.BASE_URL}{endpoint}'
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code in (200, 201):
            return response
        else:
            response.raise_for_status()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return
