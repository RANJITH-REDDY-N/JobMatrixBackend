from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import string
import os

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config import settings
from ..models import PasswordResetToken, User
from ..auth_backend import JWTAuthentication
from django.contrib.auth.hashers import make_password, check_password
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def send_email_with_sendgrid(subject, message, from_email, to_email, fail_silently=False):

    mail_message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        plain_text_content=message
    )
    try:
        api_key = settings.EMAIL_HOST_PASSWORD

        sg = SendGridAPIClient(api_key)
        sg.client.verify_ssl_certs = False  # Disable SSL verification

        response = sg.send(mail_message)
        print(f"SendGrid API response status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email with SendGrid: {str(e)}")
        if not fail_silently:
            raise
        return False


class PasswordResetRequestView(APIView):

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if user exists
            user = User.objects.filter(user_email=email).first()

            if user:
                # Generate a random 6-digit code
                verification_code = ''.join(random.choices(string.digits, k=6))

                # Delete any existing tokens for this email
                PasswordResetToken.objects.filter(email=email).delete()

                # Create new token
                reset_token = PasswordResetToken(
                    email=email,
                    token=verification_code,
                    expires_at=timezone.now() + timedelta(minutes=15)
                )
                reset_token.save()

                # Email subject and message
                subject = "JobMatrix - Password Reset Verification"
                message = f"""
Hello {user.user_first_name},

You've requested to reset your password for JobMatrix. Please use the following verification code:

{verification_code}

This code will expire in 15 minutes.

If you didn't request a password reset, please ignore this email or contact support.

Regards,
The JobMatrix Team
                """

                # Send the email using SendGrid
                send_email_with_sendgrid(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_email=email,
                    fail_silently=False
                )

            # Always return 200 for security reasons
            return Response({
                'message': 'If an account with this email exists, a password reset verification code has been sent'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error sending email: {str(e)}")  # Log the error
            return Response({
                'message': 'Failed to send password reset email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyResetCodeView(APIView):

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not all([email, code]):
            return Response({
                'message': 'Email and verification code are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the token
            token = PasswordResetToken.objects.filter(email=email, token=code).first()

            if not token:
                return Response({
                    'message': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)

            if token.is_expired:
                return Response({
                    'message': 'Verification code has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'message': 'Verification code is valid'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error verifying code: {str(e)}")  # Log the error
            return Response({
                'message': 'Failed to verify code. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResetPasswordView(APIView):

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not all([email, code, new_password]):
            return Response({
                'message': 'Email, verification code, and new password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the token
            token = PasswordResetToken.objects.filter(email=email, token=code).first()

            if not token:
                return Response({
                    'message': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)

            if token.is_expired:
                return Response({
                    'message': 'Verification code has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Find the user and update password
            user = User.objects.get(user_email=email)
            user.user_password = make_password(new_password)
            user.save()

            # Delete the token
            token.delete()

            return Response({
                'message': 'Password has been reset successfully'
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'message': 'Invalid email or verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error resetting password: {str(e)}")  # Log the error
            return Response({
                'message': 'Failed to reset password. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not all([current_password, new_password, confirm_password]):
            return Response({
                'message': 'Current password, new password, and confirm password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({
                'message': 'New password and confirm password do not match'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = request.user
            if not check_password(current_password, user.user_password):
                return Response({
                    'message': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(new_password) < 8:
                return Response({
                    'message': 'New password must be at least 8 characters long'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.user_password = make_password(new_password)
            user.save()

            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error changing password: {str(e)}")
            return Response({
                'message': 'Failed to change password. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)