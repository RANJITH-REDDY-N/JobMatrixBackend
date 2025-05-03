from rest_framework import serializers
from JobMatrix.models import Job
from decimal import Decimal
from JobMatrix.serializers import CompanySerializer  # Import from JobMatrix
from JobMatrix.models import Recruiter, Company, Bookmark, Application, Job, Applicant
from config import settings
from JobMatrix.utils import get_full_url


class JobSerializer(serializers.ModelSerializer):
    job_salary = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0')
    )

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['job_id', 'job_date_posted']

    def validate_job_title(self, value):
        return value

class JobWithCompanySerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    job_salary = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0')
    )

    class Meta:
        model = Job
        fields = ['job_id', 'job_title', 'job_description', 'job_location',
                'job_salary', 'job_date_posted', 'recruiter_id', 'company']
        read_only_fields = ['job_id', 'job_date_posted']

    def get_company(self, obj):
        # Get the company through the recruiter
        recruiter = Recruiter.objects.get(recruiter_id=obj.recruiter_id.recruiter_id)
        company = Company.objects.get(company_id=recruiter.company_id.company_id)
        return CompanySerializer(company).data


class JobApplicantDetailSerializer(serializers.ModelSerializer):
    # Get applicant details including user information
    applicant_details = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ['application_id', 'application_status', 'application_date_applied',
                  'application_recruiter_comment', 'applicant_details']

    def get_applicant_details(self, obj):
        # Access the related applicant model through the foreign key
        applicant = obj.applicant_id
        user = applicant.applicant_id  # This is the User model linked to Applicant

        # Create a dictionary with all the needed information
        applicant_data = {
            'id': user.user_id,
            'email': user.user_email,
            'full_name': f"{user.user_first_name} {user.user_last_name}",
            'profile_photo': None,
            'resume': None
        }

        if applicant.applicant_resume:
            try:
                if hasattr(applicant.applicant_resume, 'name'):
                    applicant_data['resume'] = get_full_url(applicant.applicant_resume.name)
                else:
                    applicant_data['resume'] = get_full_url(str(applicant.applicant_resume))
            except Exception as e:
                # Handle error but continue
                pass

        if user.user_profile_photo:
            try:
                if hasattr(user.user_profile_photo, 'name'):
                    applicant_data['profile_photo'] = get_full_url(user.user_profile_photo.name)
                else:
                    applicant_data['profile_photo'] = get_full_url(str(user.user_profile_photo))
            except Exception as e:
                # Handle error but continue
                pass

        return applicant_data


# ---------------- Bookmark Serializer -------------------

class BookmarkSerializer(serializers.ModelSerializer):
    job_details = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = "__all__"
        read_only_fields = ['bookmark_id', 'applicant_id', 'bookmark_date_saved']

    def get_job_details(self, obj):
        job = obj.job_id
        if not job:
            return {}

        response_data = {
            'job_id': job.job_id,
            'job_title': job.job_title,
            'job_description': job.job_description,
            'job_location': job.job_location,
            'job_salary': job.job_salary,
            'job_date_posted': job.job_date_posted.strftime('%Y-%m-%d %H:%M:%S') if job.job_date_posted else '',
        }

        if job.recruiter_id and job.recruiter_id.company_id:
            company = job.recruiter_id.company_id
            company_image = None
            
            if company.company_image:
                try:
                    if hasattr(company.company_image, 'name'):
                        company_image = get_full_url(company.company_image.name)
                    else:
                        company_image = get_full_url(str(company.company_image))
                except Exception:
                    # Handle error but continue
                    pass

            response_data['company'] = {
                'company_id': company.company_id,
                'company_name': company.company_name,
                'company_description': company.company_description,
                'company_industry': company.company_industry,
                'company_image': company_image,
            }

        else:
            response_data['company'] = {}

        return response_data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('job_id') and isinstance(representation['job_id'], dict):
            representation['job_id'] = representation['job_id'].get('job_id')
        if representation.get('applicant_id') and isinstance(representation['applicant_id'], dict):
            representation['applicant_id'] = representation['applicant_id'].get('applicant_id')

        return representation

class BookmarkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ['job_id']

# ---------------- Application Serializer ----------------

class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Application
        fields = ['application_id', 'job_id', 'applicant_id', 'application_status',
                  'application_recruiter_comment', 'application_date_applied', 'job_title']
        read_only_fields = ['application_id', 'applicant_id', 'application_status',
                            'application_recruiter_comment', 'application_date_applied']

    def get_job_title(self, obj):
        """Return job title for better user context"""
        if obj.job_id:
            return obj.job_id.job_title
        return None

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['job_id']
        # Only job_id is needed for application creation

class UserAppliedJobsSerializer(serializers.ModelSerializer):
    """Serializer for job applications with detailed job information"""
    job_details = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'application_id',
            'application_status',
            'application_date_applied',
            'application_recruiter_comment',
            'job_details'
        ]

    def get_job_details(self, obj):
        """Format job details using the actual field names from the Job model"""
        job = obj.job_id
        if not job:
            return {}

        # Get company details
        company_details = self._get_company_details(obj)

        # Return job details with nested company details
        return {
            "job_id": job.job_id,
            "job_title": job.job_title,
            "job_description": job.job_description,
            "job_location": job.job_location,
            "job_salary": float(job.job_salary),
            "job_date_posted": job.job_date_posted,
            "company_details": company_details
        }

    def _get_company_details(self, obj):
        """Get company details through job -> recruiter -> company relationship"""
        job = obj.job_id
        if not job or not job.recruiter_id or not hasattr(job.recruiter_id, 'company_id'):
            return {
                "company_id": None,
                "company_name": "Unknown Company",
                "company_industry": "",
                "company_description": "",
                "company_image": None
            }

        company = job.recruiter_id.company_id
        company_image = None
        
        if company.company_image:
            try:
                if hasattr(company.company_image, 'name'):
                    company_image = get_full_url(company.company_image.name)
                else:
                    company_image = get_full_url(str(company.company_image))
            except Exception:
                # Handle error but continue
                pass

        return {
            "company_id": company.company_id,
            "company_name": company.company_name,
            "company_industry": company.company_industry,
            "company_description": company.company_description,
            "company_image": company_image
        }


class ApplicantDetailSerializer(serializers.ModelSerializer):
    """Serializer for applicant details"""
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Applicant
        fields = ['full_name', 'email', 'applicant_resume']

    def get_full_name(self, obj):
        return f"{obj.applicant_id.first_name} {obj.applicant_id.last_name}"

    def get_email(self, obj):
        return obj.applicant_id.email
        
    def to_representation(self, instance):
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
                representation['applicant_resume'] = None
                
        return representation

class ApplicantSerializerForJob(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Applicant
        fields = ['applicant_id', 'full_name']

    def get_full_name(self, obj):
        return f"{obj.applicant_id.first_name} {obj.applicant_id.last_name}"

class ApplicationListSerializer(serializers.ModelSerializer):
    job = JobSerializer(source='job_id', read_only=True)
    applicant = ApplicantSerializerForJob(source='applicant_id', read_only=True)

    class Meta:
        model = Application
        fields = [
            'application_id',
            'applicant',
            'job',
            'application_status',
            'application_recruiter_comment',
            'application_date_applied'
        ]
        read_only_fields = fields

class ApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            'application_id',
            'application_status',
            'application_recruiter_comment'
        ]
        read_only_fields = ['application_id']

    def validate_application_status(self, value):
        # Ensure status is one of the valid choices
        valid_statuses = [status[0] for status in Application.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
