import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
import pyotp
import qrcode
from io import BytesIO
from datetime import datetime

# Get the absolute path to the credentials file
current_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.join(current_dir, "frf_gcp.json")

# Initialize Firebase Admin with specific database
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase initialization error: {e}")
    raise

# Get Firestore client
try:
    db = firestore.client()
except Exception as e:
    print(f"Firestore client error: {e}")
    raise


class SecurityManager:
    """Manages user authentication and security features"""

    def __init__(self):
        """Initialize SecurityManager with Firebase services"""
        self.auth = auth
        self.db = db
        self.users_ref = self.db.collection("users")

    def create_user(self, email: str, password: str) -> tuple:
        """
        Create a new user in Firebase Auth and Firestore

        Args:
            email (str): User's email address
            password (str): User's password

        Returns:
            tuple: (success: bool, result: dict/str)
        """
        try:
            # Check if user already exists
            try:
                existing_user = self.auth.get_user_by_email(email)
                return False, "Email already exists"
            except auth.UserNotFoundError:
                pass

            # Create user in Firebase Auth
            user = self.auth.create_user(email=email, password=password)

            # Generate 2FA secret
            secret = pyotp.random_base32()

            # Store user data in Firestore
            user_ref = self.users_ref.document(email)
            user_data = {
                "uid": user.uid,
                "email": email,
                "two_fa_secret": secret,
                "two_fa_enabled": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            user_ref.set(user_data)
            return True, {"uid": user.uid, "email": email}

        except Exception as e:
            print(f"Error creating user: {str(e)}")
            return False, str(e)

    def get_user(self, email: str) -> tuple:
        """
        Get user data from both Firebase Auth and Firestore

        Args:
            email (str): User's email address

        Returns:
            tuple: (success: bool, user_data: dict/str)
        """
        try:
            # Get user from Firebase Auth
            auth_user = self.auth.get_user_by_email(email)

            # Get additional user data from Firestore
            user_doc = self.users_ref.document(email).get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data.update(
                    {"uid": auth_user.uid, "email_verified": auth_user.email_verified}
                )
                return True, user_data
            return False, "User document not found"

        except auth.UserNotFoundError:
            return False, "User not found"
        except Exception as e:
            return False, str(e)

    def verify_token(self, id_token: str) -> tuple:
        """
        Verify Firebase ID token

        Args:
            id_token (str): Firebase ID token

        Returns:
            tuple: (success: bool, token_data: dict/str)
        """
        try:
            decoded_token = self.auth.verify_id_token(id_token)
            return True, decoded_token
        except Exception as e:
            return False, str(e)

    def generate_qr(self, email: str) -> bytes:
        """
        Generate QR code for 2FA setup

        Args:
            email (str): User's email address

        Returns:
            bytes: QR code image data
        """
        try:
            user_doc = self.users_ref.document(email).get()
            if user_doc.exists:
                data = user_doc.to_dict()
                secret = data.get("two_fa_secret")
                if secret:
                    totp = pyotp.TOTP(secret)
                    otp_uri = totp.provisioning_uri(name=email, issuer_name="FRF-AI")
                    qr = qrcode.make(otp_uri)
                    buffered = BytesIO()
                    qr.save(buffered, format="PNG")
                    return buffered.getvalue()
            return None
        except Exception as e:
            print(f"Error generating QR: {str(e)}")
            return None

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """
        Verify 2FA OTP code

        Args:
            email (str): User's email address
            otp_code (str): OTP code to verify

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            user_doc = self.users_ref.document(email).get()
            if user_doc.exists:
                data = user_doc.to_dict()
                secret = data.get("two_fa_secret")
                if secret:
                    totp = pyotp.TOTP(secret)
                    return totp.verify(otp_code)
            return False
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")
            return False

    def enable_2fa(self, email: str) -> tuple:
        """
        Enable 2FA for user

        Args:
            email (str): User's email address

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            self.users_ref.document(email).update(
                {"two_fa_enabled": True, "updated_at": datetime.utcnow()}
            )
            return True, "2FA enabled successfully"
        except Exception as e:
            return False, str(e)

    def disable_2fa(self, email: str) -> tuple:
        """
        Disable 2FA for user

        Args:
            email (str): User's email address

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            new_secret = pyotp.random_base32()
            self.users_ref.document(email).update(
                {
                    "two_fa_secret": new_secret,
                    "two_fa_enabled": False,
                    "updated_at": datetime.utcnow(),
                }
            )
            return True, "2FA disabled successfully"
        except Exception as e:
            return False, str(e)

    def delete_user(self, email: str) -> tuple:
        """
        Delete user from both Firebase Auth and Firestore

        Args:
            email (str): User's email address

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Delete from Firebase Auth
            user = self.auth.get_user_by_email(email)
            self.auth.delete_user(user.uid)

            # Delete from Firestore
            self.users_ref.document(email).delete()

            return True, "User deleted successfully"
        except Exception as e:
            return False, str(e)

    def list_users(self) -> tuple:
        """
        List all users with their data

        Returns:
            tuple: (success: bool, users: list/str)
        """
        try:
            users = []
            for user in self.auth.list_users().iterate_all():
                user_doc = self.users_ref.document(user.email).get()
                user_data = {
                    "uid": user.uid,
                    "email": user.email,
                    "email_verified": user.email_verified,
                }
                if user_doc.exists:
                    user_data.update(user_doc.to_dict())
                users.append(user_data)
            return True, users
        except Exception as e:
            return False, str(e)

    def update_user(self, email: str, **kwargs) -> tuple:
        """
        Update user data in Firestore

        Args:
            email (str): User's email address
            **kwargs: Fields to update

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Add update timestamp
            kwargs["updated_at"] = datetime.utcnow()

            # Update in Firestore
            self.users_ref.document(email).update(kwargs)
            return True, "User updated successfully"
        except Exception as e:
            return False, str(e)
