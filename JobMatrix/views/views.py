from django.core.exceptions import ValidationError
from django.db import transaction, models
from datetime import datetime, timezone, timedelta, date

from django.shortcuts import get_object_or_404
from pymysql import DatabaseError
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import check_password
from decouple import config
from JobMatrix.serializers import *
from JobMatrix.auth_backend import JWTAuthentication
from JobMatrix.permissions import *
from JobMatrix.models import *
from Profile.serializers import *
from Job.serializers import *
import os

class CustomPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserCreateView(APIView):
    authentication_classes = []

    def post(self, request):
        try:
            with transaction.atomic():
                serializer = UserSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                if user.user_role == "APPLICANT":
                    applicant_serializer = ApplicantSerializer(data=request.data, context={"user": user})
                    applicant_serializer.is_valid(raise_exception=True)
                    applicant_serializer.save()

                elif user.user_role == "RECRUITER":
                    create_company = request.data.get('create_company')
                    recruiter_start_date = request.data.get("recruiter_start_date")

                    if create_company == 'True':
                        company_data = {
                            'company_name': request.data.get('company_name'),
                            'company_description': request.data.get('company_description'),
                            'company_industry': request.data.get('company_industry'),
                            'company_image': request.data.get('company_image'),
                            'company_secret_key': request.data.get('company_secret_key')
                        }

                        # create new company
                        company_serializer = CompanySerializer(data=company_data)
                        if not company_serializer.is_valid():
                            print("Serializer errors:", company_serializer.errors)
                            raise ValidationError(company_serializer.errors)
                        company = company_serializer.save()

                        # Associate the recruiter with the new company
                        recruiter_data = {**request.data, "company_id": company.company_id,}
                        if "recruiter_start_date" in recruiter_data:
                            try:
                                recruiter_data["recruiter_start_date"] = datetime.strptime(
                                    recruiter_start_date, "%Y-%m-%d").date()
                            except ValueError:
                                return Response({"message": "Invalid recruiter_start_date format. Use YYYY-MM-DD."}, status=400)


                        recruiter_serializer = RecruiterSerializer(data=recruiter_data, context={"user": user, "company": company, "request": request})
                        recruiter_serializer.is_valid(raise_exception=True)
                        recruiter_serializer.save(recruiter_start_date=recruiter_start_date)

                    else:
                        company_id = request.data.get("company_id")
                        company_secret_key = request.data.get("company_secret_key")
                        if not company_id or not company_secret_key:
                            raise ValueError("Company ID and Secret Key are required!")

                        company = Company.objects.select_for_update().get(company_id=company_id)
                        if not check_password(company_secret_key, company.company_secret_key):
                            raise ValueError("Invalid Company Secret Key!")

                        # Associate the recruiter with the existing company
                        recruiter_data = { **request.data, "company_id": company_id,}
                        if "recruiter_start_date" in recruiter_data:
                            try:
                                recruiter_data["recruiter_start_date"] = datetime.strptime(recruiter_start_date, "%Y-%m-%d").date()
                            except ValueError:
                                return Response({"message": "Invalid recruiter_start_date format. Use YYYY-MM-DD."}, status=400)

                        existing_recruiter = company.recruiters.filter(recruiter_is_active=True).first()
                        if existing_recruiter:
                            existing_recruiter.recruiter_is_active = False
                            existing_recruiter.recruiter_end_date = recruiter_data["recruiter_start_date"] - timedelta(days=1)
                            existing_recruiter.save()

                        recruiter_serializer = RecruiterSerializer(data=recruiter_data, context={"user": user})
                        recruiter_serializer.is_valid(raise_exception=True)
                        recruiter_serializer.save(recruiter_start_date=recruiter_start_date)

                elif user.user_role == "ADMIN":
                    secret_key = request.data.get("admin_secret_key")
                    expected_secret = config("ADMIN_SECRET_KEY")

                    if secret_key != expected_secret:
                        raise ValueError("Invalid admin secret key!")

                    admin_serializer = AdminSerializer(data=request.data, context={"user": user})
                    admin_serializer.is_valid(raise_exception=True)
                    admin_serializer.save()

                return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)

        except DatabaseError as db_error:
            return Response({"message": f"Database error: {str(db_error)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = []

    def post(self, request):
        user_email = request.data.get("user_email")
        user_password = request.data.get("user_password")

        if not user_email:
            return Response({"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not user_password:
            return Response({"message": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(user_email=user_email)

            # Specifically check for password mismatch
            if not check_password(user_password, user.user_password):
                return Response({"message": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

            # Check if the user is a RECRUITER and verify active status
            if hasattr(user, 'user_role') and user.user_role == "RECRUITER":
                try:
                    # Get the recruiter record associated with this user
                    recruiter = Recruiter.objects.get(recruiter_id=user.user_id)

                    # Check if the recruiter is active
                    if not recruiter.recruiter_is_active:
                        return Response(
                            {"message": "You can no longer login into the portal."},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except Recruiter.DoesNotExist:
                    return Response(
                        {"message": "Recruiter profile not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Exception as e:
                    # Handle any other recruiter-related errors
                    return Response(
                        {"message": "Error verifying recruiter status. Please contact support."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Generate JWT token
            token = JWTAuthentication.generate_jwt(user)

            # Return token with additional user info for better UX
            return Response({
                "token": token,
                "user_id": user.user_id,
                "user_email": user.user_email,
                "user_role": user.user_role if hasattr(user, 'user_role') else None,
                "message": "Login successful"
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "No account found with this email"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Handle any other unexpected errors
            return Response({"message": "Login failed. Please try again."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserUpdateView(generics.UpdateAPIView):
    """
    API for updating user details.
    - Requires authentication.
    - Only admins or the user themselves can update their data.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSelfOrAdmin]

class UserPartialUpdateView(generics.UpdateAPIView):
    """
    API for partially updating user details.
    - Requires authentication.
    - Allows users or admins to update specific fields.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSelfOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        
        # Get the user and update
        response = self.update(request, *args, **kwargs)
        
        # If successful, get full profile photo URL using get_full_url
        if response.status_code == 200 and 'user_profile_photo' in request.data:
            user_id = kwargs.get('pk')
            try:
                user = User.objects.get(pk=user_id)
                if user.user_profile_photo:
                    from JobMatrix.utils import get_full_url
                    if hasattr(user.user_profile_photo, 'name'):
                        response.data['user_profile_photo'] = get_full_url(user.user_profile_photo.name)
                    else:
                        response.data['user_profile_photo'] = get_full_url(str(user.user_profile_photo))
            except Exception as e:
                # Don't modify response on error
                pass
        
        return response

class UserRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsSelf | IsAdmin | IsRecruiter]
    serializer_class = UserSerializer

    def get_object(self):
        email = self.request.query_params.get('user_email')
        if not email:
            return Response({"message": "Email parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(user_email=email)
            self.check_object_permissions(self.request, user)
            return user
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()

        # Check if the response is already a Response object (an error occurred)
        if isinstance(user, Response):
            return user

        # Pass request to serializer context to build absolute URLs
        user_data = UserSerializerForResponse(user, context={'request': request}).data

        # Different responses based on user role
        if user.user_role == 'APPLICANT':
            # For APPLICANT, get all details without any pagination
            applicant_id = user.user_id

            # Skills - all of them
            skills = Skill.objects.filter(applicant_id=applicant_id)
            try:
                skills = skills.order_by('skill_id')
            except Exception:
                pass  # If ordering fails, use default order
            user_data['skills'] = SkillSerializer(skills, many=True).data

            # Work Experience - all of them
            work_experience = WorkExperience.objects.filter(applicant_id=applicant_id)
            try:
                work_experience = work_experience.order_by('-end_date')
            except Exception:
                pass  # If ordering fails, use default order
            user_data['work_experience'] = WorkExperienceSerializer(work_experience, many=True).data

            # Education - all of them
            education = Education.objects.filter(applicant_id=applicant_id)
            try:
                education = education.order_by('-end_date')
            except Exception:
                pass  # If ordering fails, use default order
            user_data['education'] = EducationSerializer(education, many=True).data
            try:
                applicant = Applicant.objects.get(applicant_id=user.user_id)
                applicant_data = ApplicantSerializer(applicant, context={'request': request}).data
                user_data['applicant_resume'] = applicant_data["applicant_resume"]
            except Applicant.DoesNotExist:
                user_data['applicant_resume'] = None

        elif user.user_role == 'RECRUITER':
            # For RECRUITER, get user details + company details
            try:
                # Get recruiter information for this user
                recruiter = Recruiter.objects.get(recruiter_id=user.user_id)
                recruiter_data = RecruiterSerializer(recruiter).data
                user_data['recruiter'] = recruiter_data

                # Get company information
                try:
                    company = Company.objects.get(company_id=recruiter.company_id_id)
                    serializer = CompanySerializerForResponse(company, context={'request': request})
                    company_data = serializer.data
                    user_data['company'] = company_data
                except Company.DoesNotExist:
                    user_data['company'] = None
                except Exception as e:
                    user_data['company_error'] = str(e)


            except Recruiter.DoesNotExist:
                user_data['recruiter'] = None
            except Exception as e:
                user_data['recruiter_error'] = str(e)

        elif user.user_role == 'ADMIN':
            try:
                admin = Admin.objects.get(admin_id=user.user_id)
                user_data['admin_ssn'] = admin.admin_ssn
            except Admin.DoesNotExist:
                pass
        return Response(user_data)

class ApplicantResumeUpdateView(generics.UpdateAPIView):
    serializer_class = ApplicantSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSelfOrAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        user = self.request.user
        applicant = get_object_or_404(Applicant, applicant_id = user.user_id)
        return applicant

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            applicant = Applicant.objects.get(applicant_id = user.user_id)
        except Applicant.DoesNotExist:
            return Response({"error": "You must be an applicant to update a resume"}, status=status.HTTP_403_FORBIDDEN)

        resume_data = {}
        if 'applicant_resume' in request.data:
            resume_data['applicant_resume'] = request.data['applicant_resume']

        if not resume_data:
            return Response(
                {'error': 'No resume file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(applicant, data=resume_data, partial=True)
        serializer.is_valid(raise_exception = True)
        self.perform_update(serializer)

        # Get the full resume URL for the response
        resume_url = None
        if applicant.applicant_resume:
            try:
                from JobMatrix.utils import get_full_url
                if hasattr(applicant.applicant_resume, 'name'):
                    resume_url = get_full_url(applicant.applicant_resume.name)
                else:
                    resume_url = get_full_url(str(applicant.applicant_resume))
            except Exception as e:
                resume_url = None

        response_data = {"applicant_id": applicant.applicant_id_id, "applicant_resume": resume_url}
        return Response(response_data)

class RecruiterApplicantListView(generics.ListAPIView):
    """
    API for recruiters to retrieve a list of applicants.
    - Requires authentication.
    - Only users with the recruiter role can access this endpoint.
    - Supports filtering by email, user ID, first name, and last name.
    """
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        queryset = User.objects.filter(user_role="APPLICANT")
        filters = ['user_email', 'user_id', 'user_first_name', 'user_last_name']
        filter_kwargs = {k: self.request.query_params[k] for k in filters if k in self.request.query_params}
        return queryset.filter(**filter_kwargs)

class RecruiterDetailsUpdateView(generics.UpdateAPIView):
    serializer_class = RecruiterSerializer
    authentication_classes = [JWTAuthentication]
    permission_class = [IsRecruiter & IsSelf]

    def get_object(self):
        user = self.request.user
        recruiter = Recruiter.objects.get(recruiter_id = user.user_id)
        if Recruiter.DoesNotExist:
            return Response({'error': 'Recruiter with this ID doesnot Exists'})

    def patch(self, request):
        user = request.user
        try:
            recruiter = Recruiter.objects.get(recruiter_id=user.user_id)
        except Recruiter.DoesNotExist:
            return Response({"error": "You must be an recruiter to update his details"}, status=status.HTTP_403_FORBIDDEN)

        update_data = {}
        if 'recruiter_is_active' in request.data and request.data['recruiter_is_active'] is False:
            if recruiter.recruiter_is_active:
                update_data['recruiter_is_active'] = False
                update_data['recruiter_end_date'] = date.today()
            else:
                return Response({'message': 'Recruiter is already inactive'},
                                status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Recruiter is inactive'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(recruiter, data = update_data, partial=True)
        serializer.is_valid(raise_exception = True)
        self.perform_update(serializer)
        return Response(serializer.data)

class CompanyListView(generics.ListAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializerForResponse


class CompanyJobsListView(generics.ListAPIView):
    """
    API view to list all jobs posted by the company of the authenticated recruiter,
    including jobs posted by inactive recruiters, with application statistics for each job.
    Requires JWT token authentication.
    """
    serializer_class = JobListSerializer
    authentication_classes = [JWTAuthentication]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user

        # Check if the user is a recruiter (only active recruiters can access)
        try:
            recruiter = Recruiter.objects.get(recruiter_id=user.user_id)

            # Only active recruiters can view the company's jobs
            if not recruiter.recruiter_is_active:
                return Job.objects.none()

            company = recruiter.company_id

            # Get ALL recruiters for this company, both active and inactive
            recruiter_ids = Recruiter.objects.filter(
                company_id=company
            ).values_list('recruiter_id', flat=True)

            # Get all jobs posted by any recruiter (active or inactive) from this company
            queryset = Job.objects.filter(recruiter_id__in=recruiter_ids).order_by('-job_date_posted')

            # Apply filters from query parameters
            min_salary = self.request.query_params.get('min_salary')
            date_posted = self.request.query_params.get('date_posted')
            location = self.request.query_params.get('job_location')
            job_title = self.request.query_params.get('job_title')

            # Filter by job title
            if job_title:
                queryset = queryset.filter(job_title__icontains=job_title)

            # Filter by location
            if location:
                queryset = queryset.filter(job_location__icontains=location)

            # Filter by minimum salary
            if min_salary:
                try:
                    salary_value = float(min_salary)
                    queryset = queryset.filter(job_salary__gte=salary_value)
                except (ValueError, TypeError):
                    pass  # Invalid salary format, ignore filter

            # Filter by date posted
            if date_posted:
                try:
                    now = timezone.now()
                    if date_posted == "Past 24 hours":
                        date_threshold = now - timezone.timedelta(hours=24)
                    elif date_posted == "Past 3 days":
                        date_threshold = now - timezone.timedelta(days=3)
                    elif date_posted == "Past week":
                        date_threshold = now - timezone.timedelta(days=7)
                    elif date_posted == "Past month":
                        date_threshold = now - timezone.timedelta(days=30)
                    else:
                        # Try to parse as a number of days
                        try:
                            days = int(date_posted)
                            date_threshold = now - timezone.timedelta(days=days)
                        except ValueError:
                            # Try to parse as a date string (YYYY-MM-DD)
                            try:
                                from datetime import datetime
                                date_obj = datetime.strptime(date_posted, '%Y-%m-%d').date()
                                date_threshold = timezone.make_aware(datetime.combine(date_obj, datetime.min.time()))
                            except ValueError:
                                raise ValueError("Invalid date format")

                    queryset = queryset.filter(job_date_posted__gte=date_threshold)
                except (ValueError, TypeError):
                    pass  # Invalid date format, ignore filter

            return queryset

        except Recruiter.DoesNotExist:
            # User is not a recruiter
            return Job.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Override list method to handle case when recruiter is not active
        and provide customized response with application stats for each job
        """
        try:
            recruiter = Recruiter.objects.get(recruiter_id=request.user)

            # Only active recruiters can access this endpoint
            if not recruiter.recruiter_is_active:
                return Response(
                    {"detail": "Your recruiter account is not active."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Continue with regular list behavior
            response = super().list(request, *args, **kwargs)

            # Check if response contains paginated data
            if isinstance(response.data, dict) and 'results' in response.data:
                # Get pagination info
                count = response.data.get('count', 0)
                next_link = response.data.get('next', None)
                previous_link = response.data.get('previous', None)
                page_size = self.paginator.page_size
                current_page = request.query_params.get(self.paginator.page_query_param, 1)

                try:
                    current_page = int(current_page)
                except (ValueError, TypeError):
                    current_page = 1

                total_pages = (count + page_size - 1) // page_size if page_size > 0 else 0

                # Get application stats for each job
                job_results = response.data.get('results', [])
                job_ids = [job['job_id'] for job in job_results]

                # Get all applications for these jobs in a single query
                applications = Application.objects.filter(job_id__in=job_ids)

                # Create a dictionary to store stats for each job
                job_stats = {}
                for app in applications:
                    job_id = app.job_id_id
                    if job_id not in job_stats:
                        job_stats[job_id] = {
                            'total_applications': 0,
                            'approved_applications': 0,
                            'rejected_applications': 0,
                            'pending_applications': 0
                        }

                    job_stats[job_id]['total_applications'] += 1
                    if app.application_status == "APPROVED":
                        job_stats[job_id]['approved_applications'] += 1
                    elif app.application_status == "REJECTED":
                        job_stats[job_id]['rejected_applications'] += 1
                    elif app.application_status == "PENDING":
                        job_stats[job_id]['pending_applications'] += 1

                # Add stats to each job in the results
                for job in job_results:
                    job_id = job['job_id']
                    if job_id in job_stats:
                        job.update(job_stats[job_id])
                    else:
                        job.update({
                            'total_applications': 0,
                            'approved_applications': 0,
                            'rejected_applications': 0,
                            'pending_applications': 0
                        })

                # Create a custom response with additional info
                company = recruiter.company_id
                new_data = {
                    'status': 'success',
                    'message': f"All jobs for {company.company_name} retrieved successfully, including those posted by inactive recruiters",
                    'company_name': company.company_name,
                    'company_id': company.company_id,
                    'total_count': count,
                    'next': next_link,
                    'previous': previous_link,
                    'current_page': current_page,
                    'total_pages': total_pages,
                    'results': job_results
                }

                response.data = new_data

            return response

        except Recruiter.DoesNotExist:
            return Response(
                {"detail": "You do not have a recruiter profile."},
                status=status.HTTP_403_FORBIDDEN
            )


class CompanyUpdateView(generics.UpdateAPIView):
    """
    API view for updating company details

    Handles PUT/PATCH requests to update company information
    - PUT: Complete update (all fields required except image and secret_key)
    - PATCH: Partial update (only include fields you want to change)

    To update company_secret_key:
    - Include 'current_company_secret_key' and 'new_company_secret_key' in request
    """
    permission_classes = [IsRecruiter]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        # Use the appropriate serializer based on request params
        if 'current_company_secret_key' in self.request.data and 'new_company_secret_key' in self.request.data:
            return CompanySecretKeyUpdateSerializer
        return CompanyUpdateSerializer

    def get_object(self):
        """
        Get the company associated with the logged-in recruiter
        """
        try:
            # Get the recruiter associated with the current user
            recruiter = Recruiter.objects.get(recruiter_id=self.request.user)
            # Return the company associated with this recruiter
            return recruiter.company_id
        except Recruiter.DoesNotExist:
            return None

    def update(self, request, *args, **kwargs):
        """
        Handle company update requests (PUT or PATCH)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log incoming request details for debugging
        logger.info(f"Company update request received. Method: {request.method}")
        logger.info(f"Content type: {request.content_type}")
        
        if 'company_image' in request.data:
            if hasattr(request.data['company_image'], 'size'):
                logger.info(f"Image size: {request.data['company_image'].size} bytes")
            else:
                logger.info(f"Image is not a file: {type(request.data['company_image'])}")
        
        instance = self.get_object()
        if not instance:
            return Response(
                {
                    "message": "You do not have access to a company.",
                    "error": "403 Forbidden"
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if this is a secret key update
        is_secret_key_update = ('current_company_secret_key' in request.data and
                                'new_company_secret_key' in request.data)

        # Use partial=True for PATCH requests
        partial = kwargs.pop('partial', False) or request.method == 'PATCH'

        # Handle file deletion - convert empty string to None for image field
        if 'company_image' in request.data and request.data['company_image'] == '':
            from django.core.files.uploadedfile import InMemoryUploadedFile
            # If company_image is empty string (not a file), set it to None
            if not isinstance(request.data['company_image'], InMemoryUploadedFile):
                mutable_data = request.data.copy()
                mutable_data['company_image'] = None
                request._full_data = mutable_data

        # Create a cleaned copy of the data to avoid directly modifying request.data
        data_copy = request.data.copy()
        
        # Always handle image files specially
        if 'company_image' in request.FILES:
            # Use a safe function to process the uploaded file
            try:
                from django.core.files.base import ContentFile
                file_obj = request.FILES['company_image']
                file_content = file_obj.read()  # Read file content
                
                # Create a clean file without problematic path info
                clean_name = os.path.basename(file_obj.name)
                
                # Remove the original file from data
                data_copy.pop('company_image', None)
                
                # Add a clean version
                data_copy['company_image'] = ContentFile(file_content, name=clean_name)
                
                logger.info(f"Successfully processed company image file: {clean_name}")
            except Exception as e:
                logger.error(f"Error processing company image file: {str(e)}")
                # Continue without the image if there's an error
                data_copy.pop('company_image', None)

        # Get appropriate serializer with our cleaned data
        serializer = self.get_serializer(instance, data=data_copy, partial=partial)

        if serializer.is_valid():
            try:
                # Save the updated company details
                self.perform_update(serializer)

                # For secret key updates, return simplified success response
                if is_secret_key_update:
                    return Response({
                        "message": "Company secret key updated successfully"
                    }, status=status.HTTP_200_OK)

                # For other updates, prepare full response
                # Prepare image URL if available
                image_url = None
                if instance.company_image:
                    try:
                        from JobMatrix.utils import get_full_url
                        if hasattr(instance.company_image, 'name'):
                            image_url = get_full_url(instance.company_image.name)
                        else:
                            image_url = get_full_url(str(instance.company_image))
                    except Exception as e:
                        # Log specific error but use fallback
                        logger.error(f"Error generating company image URL: {str(e)}")
                        image_url = instance.company_image.name if instance.company_image else None

                # Prepare company data for response
                company_data = {
                    "company_id": instance.company_id,
                    "company_name": instance.company_name,
                    "company_industry": instance.company_industry,
                    "company_description": instance.company_description,
                    "company_image": image_url
                }

                # Return success response with new structure
                return Response({
                    "message": "Company updated successfully",
                    "data": company_data
                }, status=status.HTTP_200_OK)

            except Exception as e:
                # Handle unexpected errors during update
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Error updating company: {error_details}")
                return Response({
                    "message": "Failed to update company details",
                    "error": f"500 Internal Server Error: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Log validation errors
            logger.error(f"Validation errors: {serializer.errors}")
        
            # Return validation errors with the new format
            error_message = "Validation error"
            # Get the first error message if available
            if serializer.errors:
                for field, errors in serializer.errors.items():
                    if errors and isinstance(errors, list) and len(errors) > 0:
                        error_message = f"{field}: {errors[0]}"
                        break

            return Response({
                "message": error_message,
                "error": "400 Bad Request"
            }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Handle PATCH requests
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserListView(generics.ListAPIView):
    """
    API for retrieving a list of all users with pagination and filtering.
    - Requires authentication.
    - Only accessible by admins.
    - Supports filtering by user_role (APPLICANT, RECRUITER, ADMIN)
    - Supports search by name and email
    """
    queryset = User.objects.all().order_by('-user_created_date')
    serializer_class = AdminUserListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user_role']
    search_fields = ['user_first_name', 'user_last_name']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class RecruiterCompanyDetailView(APIView):
    """
    API view that returns company details for a recruiter along with:
    - List of all recruiters with their details
    - Total jobs for the company
    - Number of jobs posted by each recruiter

    - Requires authentication
    - Only accessible to authenticated recruiters
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsRecruiter]

    def get(self, request):
        try:
            # Get the currently authenticated recruiter - this was causing the error
            # We need to query by the user's ID, not the user object itself
            current_recruiter = Recruiter.objects.get(recruiter_id_id=request.user.user_id)

            # Get the company details
            company = current_recruiter.company_id

            # Use get_full_url for company image
            company_image_url = None
            if company.company_image:
                try:
                    if hasattr(company.company_image, 'name'):
                        company_image_url = get_full_url(company.company_image.name)
                    else:
                        company_image_url = get_full_url(str(company.company_image))
                except Exception as e:
                    logger.error(f"Error generating URL for company_image: {str(e)}")
                    company_image_url = None

            # Prepare company data
            company_data = {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "company_industry": company.company_industry,
                "company_description": company.company_description,
                "company_image": company_image_url
            }

            # Get all recruiters for this company
            recruiters = Recruiter.objects.filter(company_id=company)

            # Get total jobs count for the company
            # Use recruiter_id_id field for job counting
            total_jobs = Job.objects.filter(
                recruiter_id__in=recruiters
            ).count()

            # Prepare recruiter data with job counts
            recruiter_data = []
            for recruiter in recruiters:
                # Get User model information
                user = User.objects.get(user_id=recruiter.recruiter_id_id)

                # Count jobs by this recruiter
                recruiter_job_count = Job.objects.filter(recruiter_id=recruiter).count()

                # Get profile photo URL using get_full_url
                profile_photo_url = None
                if user.user_profile_photo:
                    try:
                        if hasattr(user.user_profile_photo, 'name'):
                            profile_photo_url = get_full_url(user.user_profile_photo.name)
                        else:
                            profile_photo_url = get_full_url(str(user.user_profile_photo))
                    except Exception as e:
                        logger.error(f"Error generating URL for profile_photo: {str(e)}")
                        profile_photo_url = None

                # Add recruiter info to the list
                recruiter_data.append({
                    "recruiter_id": recruiter.recruiter_id_id,
                    "user_email": user.user_email,
                    "user_first_name": user.user_first_name,
                    "user_last_name": user.user_last_name,
                    "profile_photo": profile_photo_url,
                    "is_active": recruiter.recruiter_is_active,
                    "start_date": recruiter.recruiter_start_date.strftime(
                        '%Y-%m-%d') if recruiter.recruiter_start_date else None,
                    "end_date": recruiter.recruiter_end_date.strftime(
                        '%Y-%m-%d') if recruiter.recruiter_end_date else None,
                    "jobs_posted": recruiter_job_count,
                    "is_current_user": recruiter.recruiter_id_id == request.user.user_id
                })

            # Sort recruiters by activity status and then by jobs posted
            recruiter_data = sorted(
                recruiter_data,
                key=lambda x: (-x["is_active"], -x["jobs_posted"])
            )

            # Prepare response data
            response_data = {
                "company": company_data,
                "stats": {
                    "total_recruiters": len(recruiter_data),
                    "active_recruiters": sum(1 for r in recruiter_data if r["is_active"]),
                    "total_jobs": total_jobs
                },
                "recruiters": recruiter_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Recruiter.DoesNotExist:
            return Response(
                {"message": "You don't have a recruiter profile or it's not active."},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )