import os
from django.conf import settings

def get_full_url(file_path):
    """
    Formats file paths into full URLs based on storage configuration.
    
    Args:
        file_path: The file path stored in the model field
        
    Returns:
        str: The full URL to the file, considering S3 or local storage
    """
    if not file_path:
        return None
        
    # If it's already a full URL, return it as is
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return file_path
    
    # Check if using S3 storage
    if settings.USE_S3_STORAGE:
        # If the path already contains the bucket name, it's already formatted for S3
        if settings.AWS_STORAGE_BUCKET_NAME in file_path:
            return f"https://{file_path}"
            
        # Normalize the path to ensure proper S3 URL construction
        clean_path = file_path.lstrip('/')
        
        # Construct the S3 URL
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{clean_path}"
    else:
        # Local storage - add the backend URL
        backend_url = "http://localhost:8000" if settings.DEBUG else "https://jobmatrix.up.railway.app"
        path = file_path if file_path.startswith('/') else f'/{file_path}'
        return f"{backend_url}{settings.MEDIA_URL.rstrip('/')}{path}" 