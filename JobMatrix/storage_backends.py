from django.conf import settings
from django.utils.text import get_valid_filename
from django.core.files.storage import FileSystemStorage
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# Import S3 storage only if S3 settings are configured
if settings.USE_S3_STORAGE:
    from storages.backends.s3boto3 import S3Boto3Storage
    import boto3
    from botocore.exceptions import ClientError
    
    class MediaStorage(S3Boto3Storage):
        location = ''  # Empty string to keep paths clean
        file_overwrite = False
        region_name = settings.AWS_S3_REGION_NAME  # Explicitly set region
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME  # Explicitly set bucket name
        querystring_auth = True  # Explicitly enable querystring auth
        querystring_expire = settings.AWS_QUERYSTRING_EXPIRE
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Verify S3 credentials and bucket access
            try:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                s3.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
                # Success, but don't log it
            except ClientError as e:
                error_code = int(e.response['Error']['Code'])
                if error_code == 403:
                    logger.error(f"Access denied to S3 bucket {settings.AWS_STORAGE_BUCKET_NAME}. Check permissions.")
                elif error_code == 404:
                    logger.error(f"S3 bucket {settings.AWS_STORAGE_BUCKET_NAME} does not exist.")
                else:
                    logger.error(f"Error accessing S3: {str(e)}")
            except Exception as e:
                logger.error(f"Error initializing S3 storage: {str(e)}")
        
        def get_valid_name(self, name):
            # Preserve the original filename
            return get_valid_filename(name)
        
        def url(self, name, *args, **kwargs):
            """
            Return URL for the file, handling missing files gracefully
            """
            if not name:
                return ""
                
            try:
                # Check if the file exists first
                exists_result = self.exists(name)
                
                if exists_result:
                    # File exists, generate URL
                    if isinstance(exists_result, str):
                        # exists() returned an alternate path, use that instead
                        alt_path = exists_result
                        # Create a temporary instance to generate URL for alternate path
                        storage = S3Boto3Storage(location='')
                        return storage.url(alt_path, *args, **kwargs)
                    else:
                        # File exists at original path, generate URL normally
                        return super().url(name, *args, **kwargs)
                else:
                    # File doesn't exist in S3 - return placeholder silently
                    if hasattr(settings, 'DEFAULT_IMAGE_URL'):
                        return settings.DEFAULT_IMAGE_URL
                    return ""
                    
            except Exception as e:
                # Log errors at debug level to reduce verbosity
                logger.debug(f"Error generating URL for {name}: {str(e)}")
                return ""
                
        def exists(self, name):
            """
            Check if a file exists in S3 storage
            """
            try:
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_S3_REGION_NAME
                )
                
                # Try to head the object to check if it exists at the original path
                try:
                    s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=name)
                    return True
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        # File not found at original location
                        # Check if file exists in the "new" folder instead
                        if 'profile_photos/' in name or 'resumes/' in name or 'company_images/' in name:
                            parts = name.split('/')
                            if len(parts) >= 2:
                                # Construct path with "new" instead of user/company ID
                                folder_type = parts[0]  # profile_photos, resumes, or company_images
                                filename = parts[-1]    # The actual filename
                                new_path = f"{folder_type}/new/{filename}"
                                
                                try:
                                    s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=new_path)
                                    # Found in new/ folder! Return it
                                    logger.debug(f"File found at alternate location: {new_path}")
                                    return new_path  # Return the alternate path instead of True
                                except ClientError:
                                    # Not found in new/ folder either
                                    pass
                        
                        # File really doesn't exist
                        return False
                    # Some other error occurred
                    logger.debug(f"Error checking if file exists in S3 ({name}): {str(e)}")
                    return False
            except Exception as e:
                logger.debug(f"Unexpected error checking if file exists in S3 ({name}): {str(e)}")
                return False
else:
    # Fallback to file system storage for development
    class MediaStorage(FileSystemStorage):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('location', settings.MEDIA_ROOT)
            super().__init__(*args, **kwargs)
            
        def get_valid_name(self, name):
            # Preserve the original filename
            return get_valid_filename(name) 