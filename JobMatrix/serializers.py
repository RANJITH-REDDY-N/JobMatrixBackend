from django.conf import settings
from .models import *
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import serializers
from Profile.serializers import (
    SkillSerializer,
    WorkExperienceSerializer,
    EducationSerializer,
)
import logging
from .utils import get_full_url

logger = logging.getLogger(__name__) 


class UserSerializer(serializers.ModelSerializer): 
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data): 
        validated_data['user_password'] = make_password(validated_data['user_password']) # Hash the password
        return super().create(validated_data) # Create the user

class UserSerializerForResponse(serializers.ModelSerializer):
    class Meta:
        model = User # User model
        fields = ["user_id", "user_first_name", "user_last_name", "user_email", "user_phone", "user_street_no",
                  "user_city", "user_state", "user_zip_code", "user_role", "user_profile_photo", "user_created_date"]

    def create(self, validated_data): 
        validated_data['user_password'] = make_password(validated_data['user_password']) # Hash the password
        return super().create(validated_data) # Create the user

    def to_representation(self, instance): # Convert the user object to a dictionary
        # Get the default representation
        representation = super().to_representation(instance) # Get the default representation
        
        # Replace user_profile_photo with the full URL
        if representation.get('user_profile_photo') and instance.user_profile_photo:
            try:
                # Use the utility function to get the proper URL
                if hasattr(instance.user_profile_photo, 'name'):
                    representation['user_profile_photo'] = get_full_url(instance.user_profile_photo.name)
                else:
                    representation['user_profile_photo'] = get_full_url(str(instance.user_profile_photo))
            except Exception as e:
                # Log the error but don't break the application
                logger.error(f"Error generating URL for user_profile_photo: {str(e)}")
                # Keep the original value unchanged
        
        return representation

class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = ["applicant_id", "applicant_resume"]
        extra_kwargs = {
            'applicant_id': {'read_only': True}
        }

    def create(self, validated_data):
        user = self.context.get('user')
        validated_data['applicant_id'] = user
        return super().create(validated_data)

    def to_representation(self, instance):
        # Get the default representation
        representation = super().to_representation(instance)

        # Replace applicant_resume with the full URL
        if representation.get('applicant_resume') and instance.applicant_resume:
            try:
                # Use the utility function to get the proper URL
                if hasattr(instance.applicant_resume, 'name'):
                    representation['applicant_resume'] = get_full_url(instance.applicant_resume.name)
                else:
                    representation['applicant_resume'] = get_full_url(str(instance.applicant_resume))
            except Exception as e:
                # Log the error but don't break the application
                logger.error(f"Error generating URL for applicant_resume: {str(e)}")
                # Keep the original value or set to None to avoid frontend errors
                representation['applicant_resume'] = None

        return representation

class RecruiterSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), source="company", write_only=True)
    class Meta:
        model = Recruiter
        fields = '__all__'
        extra_kwargs = {
            'recruiter_id': {'read_only': True}
        }

    def create(self, validated_data):
        user = self.context.get('user')
        # company = self.context.get('company')
        company = validated_data.pop("company")
        validated_data['recruiter_id'] = user
        validated_data['company_id'] = company
        return super().create(validated_data)

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'
        extra_kwargs = {
            'admin_id': {'read_only': True}
        }

    def create(self, validated_data):
        user = self.context.get('user')
        validated_data['admin_id'] = user
        return super().create(validated_data)

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"
        extra_kwargs = {
            'company_id': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['company_secret_key'] = make_password(validated_data['company_secret_key'])
        return super().create(validated_data)

    def to_representation(self, instance):
        # Get the default representation
        representation = super().to_representation(instance)

        # Replace company_image with the full URL
        if representation.get('company_image') and instance.company_image:
            try:
                # Use the utility function to get the proper URL
                if hasattr(instance.company_image, 'name'):
                    representation['company_image'] = get_full_url(instance.company_image.name)
                else:
                    representation['company_image'] = get_full_url(str(instance.company_image))
            except Exception as e:
                # Log the error but don't break the application
                logger.error(f"Error generating URL for company_image: {str(e)}")
                # Keep the original value or set to None to avoid frontend errors
                representation['company_image'] = None

        return representation

class CompanySerializerForResponse(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['company_id', 'company_name', 'company_description', 'company_industry','company_image']
        extra_kwargs = {
            'company_id': {'read_only': True}
        }

    def to_representation(self, instance):
        # Get the default representation
        representation = super().to_representation(instance)

        # Replace company_image with the full URL
        if representation.get('company_image') and instance.company_image:
            try:
                # Use the utility function to get the proper URL
                if hasattr(instance.company_image, 'name'):
                    representation['company_image'] = get_full_url(instance.company_image.name)
                else:
                    representation['company_image'] = get_full_url(str(instance.company_image))
            except Exception as e:
                # Log the error but don't break the application
                logger.error(f"Error generating URL for company_image: {str(e)}")
                # Keep the original value or set to None to avoid frontend errors
                representation['company_image'] = None

        return representation

    def create(self, validated_data):
        validated_data['company_secret_key'] = make_password(validated_data['company_secret_key'])
        return super().create(validated_data)

class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.SerializerMethodField()
    applicant_name = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ['application_id', 'job_id', 'applicant_id', 'applicant_name']

    def get_job_title(self, obj):
        return obj.job_id.job_title if obj.job_id else None

    def get_applicant_name(self, obj):
        if obj.applicant_id:
            user = obj.applicant_id.user
            return f"{user.first_name} {user.last_name}" if user else "Unknown"
        return None

class JobListSerializer(serializers.ModelSerializer):
    """Serializer for listing jobs posted by a company"""
    recruiter_name = serializers.SerializerMethodField()
    date_posted = serializers.DateTimeField(source='job_date_posted', format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Job
        fields = ['job_id', 'job_title', 'job_description', 'job_location',
                  'job_salary', 'date_posted', 'recruiter_name']

    def get_recruiter_name(self, obj):
        if obj.recruiter_id and hasattr(obj.recruiter_id, 'recruiter_id'):
            user = obj.recruiter_id.recruiter_id
            return f"{user.user_first_name} {user.user_last_name}" if user.user_first_name else user.user_last_name
        return "Unknown recruiter"


class CompanyUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating company details
    """
    company_name = serializers.CharField(required=False)
    company_industry = serializers.CharField(required=False)
    company_description = serializers.CharField(required=False)
    company_image = serializers.FileField(required=False, allow_null=True, allow_empty_file=True)
    
    class Meta:
        model = Company
        fields = [
            'company_name',
            'company_industry',
            'company_description',
            'company_image',
        ]
        
    def validate_company_image(self, value):
        """
        Custom validation for company_image field to handle various input types
        """
        if value == '' or value is None:
            return None
        
        # If it's a string that's a URL, don't try to handle it as a file
        if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
            return value
            
        return value

class CompanySecretKeyUpdateSerializer(serializers.ModelSerializer):
    current_company_secret_key = serializers.CharField(write_only=True, required=True)
    new_company_secret_key = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Company
        fields = ['current_company_secret_key', 'new_company_secret_key']

    def validate(self, attrs):
        instance = self.instance

        if not check_password(attrs['current_company_secret_key'], instance.company_secret_key):
            raise serializers.ValidationError({"current_company_secret_key": "Current secret key is incorrect"})

        return attrs

    def update(self, instance, validated_data):
        instance.company_secret_key = make_password(validated_data['new_company_secret_key'])
        instance.save()
        return instance

class AdminUserListSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    work_experience = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    applicant_resume = serializers.SerializerMethodField()
    recruiter = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    admin_ssn = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'user_id', 'user_first_name', 'user_last_name', 'user_email',
            'user_phone', 'user_street_no', 'user_city', 'user_state',
            'user_zip_code', 'user_role', 'user_profile_photo',
            'user_created_date', 'skills', 'work_experience', 'education',
            'applicant_resume', 'recruiter', 'company', 'admin_ssn'
        ]

    def get_skills(self, obj):
        if obj.user_role == 'APPLICANT':
            applicant = Applicant.objects.filter(applicant_id=obj.user_id).first()
            if applicant:
                skills = Skill.objects.filter(applicant_id=applicant)
                return SkillSerializer(skills, many=True).data
        return None

    def get_work_experience(self, obj):
        if obj.user_role == 'APPLICANT':
            applicant = Applicant.objects.filter(applicant_id=obj.user_id).first()
            if applicant:
                work_experience = WorkExperience.objects.filter(applicant_id=applicant)
                return WorkExperienceSerializer(work_experience, many=True).data
        return None

    def get_education(self, obj):
        if obj.user_role == 'APPLICANT':
            applicant = Applicant.objects.filter(applicant_id=obj.user_id).first()
            if applicant:
                education = Education.objects.filter(applicant_id=applicant)
                return EducationSerializer(education, many=True).data
        return None

    def get_applicant_resume(self, obj):
        if obj.user_role == 'APPLICANT':
            applicant = Applicant.objects.filter(applicant_id=obj.user_id).first()
            if applicant and applicant.applicant_resume:
                try:
                    # Use the utility function to get the proper URL
                    if hasattr(applicant.applicant_resume, 'name'):
                        return get_full_url(applicant.applicant_resume.name)
                    return get_full_url(str(applicant.applicant_resume))
                except Exception as e:
                    # Log the error but don't break the application
                    logger.error(f"Error generating URL for applicant_resume in AdminUserListSerializer: {str(e)}")
                    return None
        return None

    def get_recruiter(self, obj):
        if obj.user_role == 'RECRUITER':
            recruiter = Recruiter.objects.filter(recruiter_id=obj.user_id).first()
            if recruiter:
                return RecruiterSerializer(recruiter).data
        return None

    def get_company(self, obj):
        if obj.user_role == 'RECRUITER':
            recruiter = Recruiter.objects.filter(recruiter_id=obj.user_id).first()
            if recruiter and recruiter.company_id:
                return CompanySerializerForResponse(recruiter.company_id).data
        return None

    def get_admin_ssn(self, obj):
        if obj.user_role == 'ADMIN':
            admin = Admin.objects.filter(admin_id=obj.user_id).first()
            if admin:
                return admin.admin_ssn
        return None