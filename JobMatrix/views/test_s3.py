"""
Test view for S3 connection validation
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from ..utils import get_full_url

class TestS3View(APIView):
    """
    A simple view to test the S3 connection and URL formatting.
    For development/debugging use only.
    """
    def get(self, request):
        # Test data
        test_url = "profile_photos/1/test.jpg"
        result = {
            "s3_enabled": settings.USE_S3_STORAGE, 
            "test_path": test_url,
            "formatted_url": get_full_url(test_url),
            "bucket_name": settings.AWS_STORAGE_BUCKET_NAME if settings.USE_S3_STORAGE else None,
            "region": settings.AWS_S3_REGION_NAME if settings.USE_S3_STORAGE else None,
            "media_url_setting": settings.MEDIA_URL
        }
        
        return Response(result, status=status.HTTP_200_OK) 