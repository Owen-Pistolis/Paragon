import threading
import requests
import logging
from authServer import AuthServer
from authInterceptor import AuthInterceptor

AUTH0_DOMAIN = "auth0.paragonai.io"
CLIENT_ID = "lbHE7kBvGsLXGKN6mCzljYJhDZYCGELt"
LOGIN_REDIRECT_URI = "http://localhost:3000/callback"
LOGOUT_REDIRECT_URI = "http://localhost:3000/logout"
SECRET_KEY = "testsecretkey"
PORT = 3000
AUDIENCE = "https://api.paragonai.io"
ALGOTRITHM = ["RS256"]
LOCAL_CREDENTIAL_PATH = "./auth_credentials.json"

class Auth:

    auth_server = None
    auth_interceptor = None

    def __init__(self, main):
        self.session = requests.Session()
        self.auth_server = AuthServer(AUTH0_DOMAIN, CLIENT_ID, LOGIN_REDIRECT_URI, LOGOUT_REDIRECT_URI, SECRET_KEY, PORT, AUDIENCE, ALGOTRITHM, LOCAL_CREDENTIAL_PATH, self, main)
        self.auth_interceptor = AuthInterceptor(self)

        self.session.mount('http://', self.auth_interceptor)
        self.session.mount('https://', self.auth_interceptor)

        server_thread = threading.Thread(target=self.auth_server.start_server)
        server_thread.daemon = True
        server_thread.start()
        self.access_token = ""
        self.id_token = ""