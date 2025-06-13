import jwt
from datetime import datetime, timezone, timedelta
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from JobMatrix.models import User

class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1] # Extract the token from the header
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]) # Decode the token
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        try:
            user = User.objects.get(user_id=payload["user_id"]) # Get the user from the database
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found") # Raise an authentication failed exception if the user is not found

        return user, None

    @staticmethod
    def generate_jwt(user): # Generate a JWT token for the user
        """
        Generates a JWT token for the user.
        """
        now_utc = datetime.now(timezone.utc) # Get the current time in UTC
        expiration_days = int(settings.JWT_EXPIRATION_DAYS) # Get the expiration days from the settings
        payload = {
            "user_id": user.user_id,    # User ID
            "exp": now_utc + timedelta(days=expiration_days), # Expiration time
            "iat": now_utc,     # Issued at time
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token
