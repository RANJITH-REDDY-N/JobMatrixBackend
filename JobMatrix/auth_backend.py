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

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        try:
            user = User.objects.get(user_id=payload["user_id"])
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return user, None

    @staticmethod
    def generate_jwt(user):
        """
        Generates a JWT token for the user.
        - `exp`: Token expiration (1 day)
        - `iat`: Issued at timestamp
        """
        now_utc = datetime.now(timezone.utc)
        payload = {
            "user_id": user.user_id,
            "exp": now_utc + timedelta(days=1),
            "iat": now_utc,
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token
