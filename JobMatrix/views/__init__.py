from .views import *
from .admin_dashboard import *
from .admin_actions import *
from .password_reset_view import *

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from JobMatrix.models import User, Applicant, Company
from JobMatrix.permissions import IsAdmin
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAdmin])
def check_broken_files(request):
    """
    Admin utility to check for broken file references in the database
    and report missing files in S3
    """
    
    try:
        # Initialize counters
        total_files = 0
        missing_files = 0
        file_report = []
        
        # Only do this check if S3 is enabled
        if not settings.USE_S3_STORAGE:
            return Response({"message": "S3 storage is not enabled. This check is only needed for S3."})
            
        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        # Check User profile photos
        users = User.objects.exclude(user_profile_photo='').exclude(user_profile_photo__isnull=True)
        for user in users:
            total_files += 1
            try:
                s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=str(user.user_profile_photo))
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    missing_files += 1
                    file_report.append({
                        'type': 'User Profile Photo',
                        'id': user.user_id,
                        'path': str(user.user_profile_photo),
                        'user': f"{user.user_first_name} {user.user_last_name} ({user.user_email})"
                    })
        
        # Check Applicant resumes
        applicants = Applicant.objects.exclude(applicant_resume='').exclude(applicant_resume__isnull=True)
        for applicant in applicants:
            total_files += 1
            try:
                s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=str(applicant.applicant_resume))
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    missing_files += 1
                    file_report.append({
                        'type': 'Applicant Resume',
                        'id': applicant.applicant_id_id,
                        'path': str(applicant.applicant_resume),
                        'user': f"{applicant.applicant_id.user_first_name} {applicant.applicant_id.user_last_name}"
                    })
        
        # Check Company images
        companies = Company.objects.exclude(company_image='').exclude(company_image__isnull=True)
        for company in companies:
            total_files += 1
            try:
                s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=str(company.company_image))
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    missing_files += 1
                    file_report.append({
                        'type': 'Company Image',
                        'id': company.company_id,
                        'path': str(company.company_image),
                        'name': company.company_name
                    })
        
        # Return results
        return Response({
            "total_files_checked": total_files,
            "missing_files": missing_files,
            "missing_file_details": file_report,
            "message": f"Found {missing_files} missing files out of {total_files} total files."
        })
            
    except Exception as e:
        logger.error(f"Error checking broken files: {str(e)}")
        return Response({"error": str(e)}, status=500)
