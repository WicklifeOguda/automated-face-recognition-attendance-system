import json
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi.requests import Request
from fastapi.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

load_dotenv()


# Load encryption key from environment variable
encryption_key = os.getenv("ENCRYPTION_KEY")
if encryption_key is None:
    raise ValueError("Encryption key not found in environment variables")

# Initialize Fernet cipher with encryption key
cipher = Fernet(encryption_key.encode())

ADMIN_CREDENTIALS_FILE = "admin_credentials.json"


class AdminAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        # Load encrypted admin credentials from JSON file
        with open(ADMIN_CREDENTIALS_FILE, "r") as file:
            encrypted_credentials = json.load(file)

        # Decrypt admin credentials
        encrypted_data = encrypted_credentials.get("encrypted_data")
        if not encrypted_data:
            raise ValueError("No encrypted data found in admin credentials file")

        decrypted_value = cipher.decrypt(encrypted_data.encode()).decode()

        # Parse decrypted JSON string to extract admin credentials
        decrypted_credentials = json.loads(decrypted_value)

        # Check if provided username and password match any admin credentials
        admins = decrypted_credentials[0]["admins"]
        for admin_data in admins:
            if (
                username == admin_data["username"]
                and password == admin_data["password"]
            ):
                # Save username in session
                request.session.update({"username": username})
                return response

        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        return "username" in request.session

    def get_admin_config(self, request: Request) -> AdminConfig:
        user = request.session.get("username")
        return AdminConfig(app_title=f"Admin - {user}")

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.session.get("username")
        return AdminUser(username=user)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
