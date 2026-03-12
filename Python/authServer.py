from flask import Flask, request, jsonify, session
import hashlib
import base64
import os
import requests
import secrets
import webbrowser
import logging
import threading
from authlib.jose import JsonWebToken, JoseError
import json
import jwt

class AuthServer:
    def __init__(self, auth0_domain, client_id, login_redirect_uri, logout_redirect_uri, secret_key, port, audience, algorithm, local_credential_path, main_auth, main):
        self.auth0_domain = auth0_domain
        self.client_id = client_id
        self.login_redirect_uri = login_redirect_uri
        self.logout_redirect_uri = logout_redirect_uri
        self.secret_key = secret_key
        self.port = port
        self.audience = audience
        self.algorithm = algorithm
        self.local_credential_path = local_credential_path
        self.main_auth = main_auth
        self.main = main

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.secret_key = self.secret_key

        # Define routes
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/callback', 'get_auth_code', self.get_auth_code)
        self.app.add_url_rule('/logout', 'logoutCallback', self.logoutCallback)

        # Thread for running the server
        self.server_thread = None

    def home(self):
        return "Flask Home!"

    def get_auth_code(self):
        # Get the authorization code from the query parameters
        auth_code = request.args.get('code')
        if not auth_code:
            return "Authorization code not found!", 400

        # Exchange the authorization code for tokens
        token_url = f"https://{self.auth0_domain}/oauth/token"
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'redirect_uri': self.login_redirect_uri,
            'code': auth_code,
            'audience': self.audience
        }

        try:
            response = requests.post(token_url, json=payload)
            response.raise_for_status()
            tokens = response.json()

        except requests.exceptions.RequestException as e:
            return f"Error exchanging code: {e}", 400

        # Save tokens to file
        try:
            with open(self.local_credential_path, "w") as file:
                file.write(json.dumps(tokens))
        except IOError as e:
            return f"Error saving tokens: {e}", 500

        # Return a success message
        self.main.communicator.login.emit("User logged in, updating GUI")
        self.main_auth.access_token = tokens.get('access_token')
        decoded = jwt.decode(self.main_auth.access_token, options={"verify_signature": False}, algorithms=["RS256"])
        print(decoded)
        self.main_auth.id_token = tokens.get('id_token')
        return "Tokens saved successfully!", 200

    def login(self):
        webbrowser.open("https://paragonai.io/login?app=python", new=0, autoraise=True)

    def logout(self, token):
         # Revoke the token
        url = f"https://{self.auth0_domain}/oauth/revoke"
        headers = {'content-type': "application/json"}
        data = {
            "token": token,
            "client_id": self.client_id
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("Token revoked successfully.")
            self.main.communicator.logout.emit("User logged out, updating GUI")
            self.main_auth.access_token = ""
            self.main_auth.id_token = ""
            logout_url = f"https://{self.auth0_domain}/v2/logout?client_id={self.client_id}&returnTo={self.logout_redirect_uri}"
            webbrowser.open(logout_url)
            logging.info("Directing user to logout")
            os.remove("./auth_credentials.json")
        else:
            print(f"Failed to revoke token: {response.status_code}")

    def start_server(self):
        self.app.run(port=self.port, debug=False, use_reloader=False)

    def is_authenticated(self):

        try:
            with open(self.local_credential_path, "r") as file:
                # Read content from the file
                content = file.read()
                content_json = json.loads(content)
                verified = self.verify_token(content_json['access_token'])
                if verified is not None:
                    self.main_auth.access_token = content_json['access_token']
                    print(self.main_auth.access_token)
                    self.main_auth.id_token = content_json['id_token']
                    print(self.main_auth.id_token)
                    return True
                else:
                    return False
        except FileNotFoundError:
            print(f"The file {self.local_credential_path} does not exist.")
            print("Please login for the first time.")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def verify_token(self, token):
        url = f"https://{self.auth0_domain}/userinfo"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return True
            else:
                return None
        except Exception as e:
            print(f"Error checking authentication: {e}")
            return None

    def logoutCallback(self):
        return "You have logged out"