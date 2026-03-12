import requests
from requests.adapters import HTTPAdapter

class AuthInterceptor(HTTPAdapter):
    def __init__(self, auth):
        self.auth = auth
        super().__init__()

    def send(self, request, **kwargs):
        # Inject the Authorization header if access_token is available
        access_token = self.auth.access_token
        if access_token:
            request.headers['Authorization'] = f'Bearer {access_token}'
            #print(f"{request.headers['Authorization']}")

        return super().send(request, **kwargs)
