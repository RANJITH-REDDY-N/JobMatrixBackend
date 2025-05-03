import os
from django.conf import settings
from os.path import basename

def get_full_url(file_path):
    """
    Formats file paths into full URLs based on storage configuration.
    
    Args:
        file_path: The file path stored in the model field
        
    Returns:
        str: The full URL to the file, always using S3
    """
    if not file_path:
        return None
        
    # If it's already a full URL, return it as is
    if file_path.startswith('http://') or file_path.startswith('https://'):
        return file_path
    
    # Normalize the path to ensure proper URL construction
    # Handle special cases and clean up the path
    clean_path = file_path.lstrip('/')
    
    # Handle any absolute paths by extracting just the basename
    if os.path.isabs(clean_path):
        clean_path = basename(clean_path)
        
        # Determine folder based on filename pattern or add to default folder
        if 'profile' in clean_path.lower():
            clean_path = f"profilephotos/{clean_path}"
        elif 'resume' in clean_path.lower():
            clean_path = f"resumes/{clean_path}" 
        elif 'company' in clean_path.lower():
            clean_path = f"companyimages/{clean_path}"
        else:
            # Default to a generic media folder
            clean_path = f"media/{clean_path}"
    
    # Always construct the S3 URL, regardless of storage setting
    return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{clean_path}" 