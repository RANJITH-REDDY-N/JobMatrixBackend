from datetime import datetime, timedelta

from django.http import Http404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from JobMatrix.permissions import *
from JobMatrix.auth_backend import JWTAuthentication
from JobMatrix.models import Job, Applicant, Application, User
from .serializers import *
from JobMatrix.permissions import IsRecruiter
from django.db import IntegrityError
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views import generic
from django.urls import reverse_lazy


# ---------------- Jobs ------------------ #
class JobListPagination(PageNumberPagination):
    page_size = 6  # Default number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100


class JobCreateView(generics.CreateAPIView):
    """
    View for creating a new job. Only recruiters are allowed to create jobs.
    """
    serializer_class = JobSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsRecruiter]

    def create(self, request, *args, **kwargs):
        # Check if recruiter_id is provided in the request data
        if 'recruiter_id' not in request.data:
            return Response({
                'status': 'error',
                'message': 'recruiter_id is required to create a job'
            }, status=status.HTTP_400_BAD_REQUEST)

        recruiter_id = request.data.get('recruiter_id')
        current_user_id = request.user.user_id  # or request.user.user_id depending on your User model

        # Check if the recruiter_id matches the user's ID
        if str(current_user_id) != str(recruiter_id):
            return Response({
                'status': 'error',
                'message': 'You can only create jobs with your own recruiter profile'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if a Recruiter with this ID exists
        try:
            recruiter = Recruiter.objects.get(recruiter_id=recruiter_id)
        except Recruiter.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No recruiter profile found with this ID'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)

        # Validate all fields except job_title
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Job posted successfully',
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                # If there's still an integrity error (like from a database constraint),
                # we need to handle it more thoroughly

                # Create a Job directly to bypass serializer validation
                job_data = request.data.copy()

                # Create the job object directly
                job = Job.objects.create(
                    job_title=job_data.get('job_title'),
                    job_description=job_data.get('job_description'),
                    # Add all other required fields from your model
                    # job_location=job_data.get('job_location'),
                    # job_salary=job_data.get('job_salary'),
                    # etc.

                    # If recruiter is a foreign key in Job model:
                    recruiter_id=recruiter_id
                )

                # Serialize the created job for the response
                return_serializer = self.get_serializer(job)
                return Response({
                    'status': 'success',
                    'message': 'Job posted successfully',
                    'data': return_serializer.data
                }, status=status.HTTP_201_CREATED)

        # For cases where other validations fail
        return Response({
            'status': 'error',
            'message': 'Failed to post job',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class JobCreateViewMultiple(generics.CreateAPIView):
    serializer_class = JobSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsRecruiter]

    def create(self, request, *args, **kwargs):
        # Get the authenticated user's recruiter profile
        try:
            recruiter = Recruiter.objects.get(recruiter_id=request.user.user_id)
            if not recruiter.recruiter_is_active:
                return Response({
                    'status': 'error',
                    'message': 'Your recruiter profile is not active. Please contact support.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Recruiter.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'No recruiter profile found for this user'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if request data is a list
        if not isinstance(request.data, list):
            return Response({
                'status': 'error',
                'message': 'Request data should be a list of jobs'
            }, status=status.HTTP_400_BAD_REQUEST)

        created_jobs = []
        errors = []

        for job_data in request.data:
            # Add recruiter_id to each job data
            job_data['recruiter_id'] = recruiter.recruiter_id

            serializer = self.get_serializer(data=job_data)

            if serializer.is_valid():
                try:
                    job = serializer.save()
                    created_jobs.append(serializer.data)
                except IntegrityError:
                    # Fallback to direct creation if serializer fails
                    try:
                        job = Job.objects.create(
                            job_title=job_data.get('job_title'),
                            job_description=job_data.get('job_description'),
                            job_location=job_data.get('job_location'),
                            job_salary=job_data.get('job_salary'),
                            recruiter_id=recruiter.recruiter_id
                        )
                        created_jobs.append(self.get_serializer(job).data)
                    except Exception as e:
                        errors.append({
                            'job_data': job_data,
                            'error': str(e)
                        })
            else:
                errors.append({
                    'job_data': job_data,
                    'error': serializer.errors
                })

        if len(errors) > 0:
            if len(created_jobs) > 0:
                # Partial success
                return Response({
                    'status': 'partial_success',
                    'message': f'{len(created_jobs)} jobs created successfully, {len(errors)} failed',
                    'created_jobs': created_jobs,
                    'errors': errors
                }, status=status.HTTP_207_MULTI_STATUS)
            else:
                # Complete failure
                return Response({
                    'status': 'error',
                    'message': 'All jobs failed to create',
                    'errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)

        # All jobs created successfully
        return Response({
            'status': 'success',
            'message': f'{len(created_jobs)} jobs created successfully',
            'data': created_jobs
        }, status=status.HTTP_201_CREATED)

class CompanyJobsListView(generics.ListAPIView):
    """
    View for retrieving all jobs with company details and flexible filtering options
    """
    serializer_class = JobWithCompanySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = JobListPagination

    def get_queryset(self):
        # Get all filter parameters
        company_ids = self.request.query_params.getlist('company_id')
        company_names = self.request.query_params.getlist('company_name')
        min_salary = self.request.query_params.get('min_salary')
        date_posted = self.request.query_params.get('date_posted')
        locations = self.request.query_params.getlist('location')
        job_titles = self.request.query_params.getlist('job_title')

        # Start with all jobs and prefetch related recruiter and company
        queryset = Job.objects.select_related(
            'recruiter_id',
            'recruiter_id__company_id'
        ).order_by('-job_date_posted')

        # Apply company filters if provided
        recruiter_ids = self.get_recruiter_ids_from_company_filters(company_ids, company_names)
        if recruiter_ids is not None:  # None means no filter was applied, empty set means no matches
            if not recruiter_ids:  # Empty set means no matching recruiters found
                return Job.objects.none()
            queryset = queryset.filter(recruiter_id__in=recruiter_ids)

        # Filter by minimum salary if provided
        if min_salary:
            try:
                min_salary_value = float(min_salary)
                queryset = queryset.filter(job_salary__gte=min_salary_value)
            except (ValueError, TypeError):
                # If min_salary is not a valid number, ignore this filter
                pass

        # Filter by date posted if provided
        if date_posted and date_posted != "Any time":
            time_threshold = self.get_date_threshold(date_posted)
            if time_threshold:
                queryset = queryset.filter(job_date_posted__gte=time_threshold)

        # Filter by location if provided
        if locations:
            location_query = Q()
            for location in locations:
                location_query |= Q(job_location__icontains=location)
            queryset = queryset.filter(location_query)

        # Filter by job title if provided
        if job_titles:
            title_query = Q()
            for title in job_titles:
                title_query |= Q(job_title__icontains=title)
            queryset = queryset.filter(title_query)

        # Filter out jobs that the user has already bookmarked or applied for
        user = self.request.user

        # Try to get the applicant profile of the current user
        try:
            applicant = Applicant.objects.get(applicant_id=user.user_id)

            # Get the jobs that the user has already bookmarked
            bookmarked_job_ids = Bookmark.objects.filter(
                applicant_id=applicant
            ).values_list('job_id', flat=True)

            # Get the jobs that the user has already applied for
            applied_job_ids = Application.objects.filter(
                applicant_id=applicant
            ).values_list('job_id', flat=True)

            # Exclude jobs that the user has already bookmarked or applied for
            if bookmarked_job_ids.exists() or applied_job_ids.exists():
                combined_job_ids = list(bookmarked_job_ids) + list(applied_job_ids)
                queryset = queryset.exclude(job_id__in=combined_job_ids)

        except Applicant.DoesNotExist:
            # If the user is not an applicant, we don't need to filter out any jobs
            pass

        return queryset

    def get_recruiter_ids_from_company_filters(self, company_ids, company_names):
        """
        Helper method to get recruiter IDs based on company filters
        Returns:
        - None if no filters applied
        - Set of recruiter IDs if filters applied and matches found
        - Empty set if filters applied but no matches found
        """
        if not company_ids and not company_names:
            return None

        recruiter_ids = set()

        # Process company IDs if provided
        if company_ids:
            company_recruiters = Recruiter.objects.filter(company_id__in=company_ids)
            recruiter_ids.update(company_recruiters.values_list('recruiter_id', flat=True))

        # Process company names if provided
        if company_names:
            name_queries = Q()
            for name in company_names:
                name_queries |= Q(company_name__icontains=name)

            companies = Company.objects.filter(name_queries)
            if companies.exists():
                matched_company_ids = companies.values_list('company_id', flat=True)
                name_company_recruiters = Recruiter.objects.filter(company_id__in=matched_company_ids)
                recruiter_ids.update(name_company_recruiters.values_list('recruiter_id', flat=True))

        return recruiter_ids

    def get_date_threshold(self, date_posted):
        """
        Helper method to get the datetime threshold based on date_posted filter
        """
        now = timezone.now()

        if date_posted == "Past 24 hours":
            return now - timezone.timedelta(hours=24)
        elif date_posted == "Past 3 days":
            return now - timezone.timedelta(days=3)
        elif date_posted == "Past week":
            return now - timezone.timedelta(days=7)
        elif date_posted == "Past month":
            return now - timezone.timedelta(days=30)

        return None

    def list(self, request, *args, **kwargs):
        # Extract all filter parameters for message generation
        company_ids = request.query_params.getlist('company_id')
        company_names = request.query_params.getlist('company_name')
        min_salary = request.query_params.get('min_salary')
        date_posted = request.query_params.get('date_posted')
        locations = request.query_params.getlist('location')
        job_titles = request.query_params.getlist('job_title')

        # Get filtered queryset
        queryset = self.get_queryset()

        # Build filter description for message
        filter_parts = []

        if company_ids:
            filter_parts.append(f"company IDs {', '.join(company_ids)}")

        if company_names:
            filter_parts.append(f"company names similar to '{', '.join(company_names)}'")

        if min_salary:
            try:
                min_salary_value = float(min_salary)
                filter_parts.append(f"minimum salary of {min_salary_value}")
            except (ValueError, TypeError):
                pass

        if date_posted and date_posted != "Any time":
            filter_parts.append(f"jobs posted in the {date_posted.lower()}")

        if locations:
            filter_parts.append(f"locations including '{', '.join(locations)}'")

        if job_titles:
            filter_parts.append(f"job titles including '{', '.join(job_titles)}'")

        filter_message = "all companies" if not filter_parts else " and ".join(filter_parts)

        # Add message about excluding bookmarked and applied jobs
        if hasattr(request.user, 'user_id'):
            try:
                applicant = Applicant.objects.get(applicant_id=request.user.user_id)
                filter_message += " (excluding jobs you've already bookmarked or applied for)"
            except Applicant.DoesNotExist:
                pass

        # Check if queryset is empty
        if not queryset.exists():
            return Response({
                'status': 'success',
                'message': f'No jobs found for {filter_message}',
                'data': [],
                'total_count': 0,
                'total_pages': 0,
                'current_page': 1
            }, status=status.HTTP_200_OK)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            # Extract pagination data
            response_data = paginated_response.data

            # Get current page and calculate page size for total pages
            page_size = self.pagination_class.page_size
            if self.pagination_class.page_size_query_param in request.query_params:
                try:
                    page_size = int(request.query_params.get(self.pagination_class.page_size_query_param))
                except (ValueError, TypeError):
                    page_size = self.pagination_class.page_size

            # Create our custom response format
            return Response({
                'status': 'success',
                'message': f'Jobs retrieved successfully for {filter_message}',
                'data': response_data['results'],
                'total_count': response_data['count'],
                'next': response_data['next'],
                'previous': response_data['previous'],
                'current_page': int(request.query_params.get('page', 1)),
                'total_pages': (response_data['count'] + page_size - 1) // page_size
            })

        # If pagination is not configured correctly, fall back to regular response
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': f'Jobs retrieved successfully for {filter_message}',
            'data': serializer.data,
            'total_count': len(serializer.data)
        }, status=status.HTTP_200_OK)

class JobUpdateView(generics.UpdateAPIView):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    permission_classes = [IsAuthenticated, IsRecruiter]
    lookup_field = 'job_id'

    def get_queryset(self):
        return Job.objects.filter(recruiter_id = self.request.user.user_id)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception = True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

class JobDeleteView(generics.DestroyAPIView):
    queryset = Job.objects.all()
    permission_classes = [IsAuthenticated, IsRecruiter]
    lookup_field = 'job_id'

    def get_object(self):
        job_id = self.kwargs.get(self.lookup_field)
        job = get_object_or_404(Job.objects.all(), job_id=job_id)
        current_user = self.request.user
        try:
            user_recruiter = current_user.recruiter
            user_company = user_recruiter.company_id
        except AttributeError:
            self.permission_denied(
                self.request,
                message="You don't have a recruiter profile with an associated company."
            )
        job_recruiter = job.recruiter_id
        if not job_recruiter:
            self.permission_denied(
                self.request,
                message="This job doesn't have an associated recruiter or company."
            )

        job_company = job_recruiter.company_id
        if user_company.company_id != job_company.company_id:
            self.permission_denied(
                self.request,
                message="You can only delete jobs from your own company."
            )
        return job

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"message": "Job deleted successfully"}, status=status.HTTP_200_OK)
        except Http404:
            job_id = kwargs.get(self.lookup_field)
            return Response(
                {"message": f"Job with ID {job_id} does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

# ----------------- BookMarks ------------------- #

class BookmarkView(generics.ListCreateAPIView):
    """
    GET: List all bookmarks for the current applicant
    POST: Create a new bookmark for the current applicant
    """
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated, IsApplicant]

    def get_queryset(self):
        try:
            applicant = self.request.user.applicant
            return Bookmark.objects.filter(applicant_id=applicant).order_by('-created_at')
        except (AttributeError, Applicant.DoesNotExist):
            return Bookmark.objects.none()

    def perform_create(self, serializer):
        # Get the job
        job_id = serializer.validated_data.get('job_id')
        job = get_object_or_404(Job, job_id=job_id.job_id if hasattr(job_id, 'job_id') else job_id)

        # Get current user's applicant profile
        try:
            applicant = self.request.user.applicant
        except (AttributeError, Applicant.DoesNotExist):
            raise serializers.ValidationError(
                {"message": "You must have an applicant profile to bookmark jobs."}
            )

        # Check if bookmark already exists
        if Bookmark.objects.filter(job_id=job, applicant_id=applicant).exists():
            raise serializers.ValidationError(
                {"message": "You have already bookmarked this job."}
            )

        # Create the bookmark
        serializer.save(applicant_id=applicant, job_id=job)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response({"message": "Job bookmarked successfully"}, status=status.HTTP_201_CREATED)

class BookmarkDetailView(generics.RetrieveDestroyAPIView):
    """
    GET: Retrieve a specific bookmark
    DELETE: Remove a specific bookmark
    Users can only retrieve/delete their own bookmarks
    """
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated, IsApplicant]
    lookup_field = 'bookmark_id'

    def get_queryset(self):
        try:
            applicant = self.request.user.applicant
            return Bookmark.objects.filter(applicant_id=applicant)
        except (AttributeError, Applicant.DoesNotExist):
            return Bookmark.objects.none()

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"message": "Bookmark removed successfully"}, status=status.HTTP_200_OK)
        except:
            bookmark_id = kwargs.get(self.lookup_field)
            return Response(
                {"message": f"Bookmark with ID {bookmark_id} does not exist or you don't have permission to delete it."},
                status=status.HTTP_404_NOT_FOUND
            )

class BookmarkListView(generics.ListAPIView):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated, IsApplicant]
    pagination_class = JobListPagination

    def get_queryset(self):
        try:
            applicant = self.request.user.user_id
            queryset = Bookmark.objects.filter(applicant_id=applicant).order_by('-bookmark_date_saved')

            # Get all filter parameters
            company_names = self.request.query_params.getlist('company_name')
            min_salary = self.request.query_params.get('min_salary')
            date_posted = self.request.query_params.get('date_posted')
            locations = self.request.query_params.getlist('location')
            job_titles = self.request.query_params.getlist('job_title')
            job_location = self.request.query_params.get('job_location')

            # Apply filters for job titles (if provided)
            if job_titles:
                title_queries = Q()
                for title in job_titles:
                    title_queries |= Q(job_id__job_title__icontains=title)
                queryset = queryset.filter(title_queries)
            elif job_title := self.request.query_params.get('job_title'):  # Fallback to single param
                queryset = queryset.filter(job_id__job_title__icontains=job_title)

            # Filter by locations
            if locations:
                location_queries = Q()
                for location in locations:
                    location_queries |= Q(job_id__job_location__icontains=location)
                queryset = queryset.filter(location_queries)
            elif job_location:  # Fallback to single param
                queryset = queryset.filter(job_id__job_location__icontains=job_location)

            # Filter by minimum salary
            if min_salary:
                try:
                    salary_value = float(min_salary)
                    queryset = queryset.filter(job_id__job_salary__gte=salary_value)
                except (ValueError, TypeError):
                    pass  # Invalid salary format, ignore filter

            # Filter by date posted - UPDATED to match the format from other views
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
                        # Try to parse as a number of days first
                        try:
                            days = int(date_posted)
                            date_threshold = now - timezone.timedelta(days=days)
                        except ValueError:
                            # Try to parse as a date string (YYYY-MM-DD)
                            try:
                                date_obj = datetime.strptime(date_posted, '%Y-%m-%d').date()
                                date_threshold = timezone.make_aware(datetime.combine(date_obj, datetime.min.time()))
                            except ValueError:
                                raise ValueError("Invalid date format")

                    queryset = queryset.filter(job_id__job_date_posted__gte=date_threshold)

                except (ValueError, TypeError):
                    pass  # Invalid date format, ignore filter

            # Filter by company names
            if company_names:
                company_name_queries = Q()
                for name in company_names:
                    company_name_queries |= Q(job_id__recruiter_id__company_id__company_name__icontains=name)
                queryset = queryset.filter(company_name_queries)
            elif company_name := self.request.query_params.get('company_name'):  # Fallback to single param
                queryset = queryset.filter(job_id__recruiter_id__company_id__company_name__icontains=company_name)

            return queryset
        except AttributeError:
            return Bookmark.objects.none()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
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

            # Create a new response structure
            new_data = {
                'total_count': count,
                'next': next_link,
                'previous': previous_link,
                'current_page': current_page,
                'total_pages': total_pages,
                'results': response.data.get('results', [])
            }

            response.data = new_data

        return response

# ---------------- Application ------------------- #

class ApplicationView(generics.ListCreateAPIView):
    """
    GET: List all job applications for the current user
    POST: Create a new job application
    """
    permission_classes = [IsAuthenticated, IsApplicant]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def get_queryset(self):
        """Return only the current user's applications"""
        try:
            applicant = self.request.user.applicant
            return Application.objects.filter(applicant_id=applicant).order_by('-application_date_applied')
        except (AttributeError, Applicant.DoesNotExist):
            return Application.objects.none()

    def perform_create(self, serializer):
        """Create application with current user as applicant"""
        # Get the job
        job_id = serializer.validated_data.get('job_id')
        job = get_object_or_404(Job, job_id=job_id.job_id if hasattr(job_id, 'job_id') else job_id)

        # Get current user's applicant profile
        try:
            applicant = self.request.user.applicant
        except (AttributeError, Applicant.DoesNotExist):
            raise serializers.ValidationError(
                {"message": "You must have an applicant profile to apply for jobs."}
            )

        # Check if application already exists
        if Application.objects.filter(job_id=job, applicant_id=applicant).exists():
            raise serializers.ValidationError(
                {"message": "You have already applied for this job."}
            )

        # Delete bookmark if it exists
        self.delete_bookmark_if_exists(applicant, job)

        # Create the application with default status
        serializer.save(
            applicant_id=applicant,
            job_id=job,
            application_status="PENDING"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
            return Response({
                "message": "Job application submitted successfully",
                "status": "PENDING"
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            # Fixed: Correctly access the validation error details
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": "An error occurred while submitting your application."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_bookmark_if_exists(self, applicant, job):
        """
        Delete bookmark for this job if it exists
        """
        bookmarks_deleted, _ = Bookmark.objects.filter(
            applicant_id=applicant,
            job_id=job
        ).delete()

        if bookmarks_deleted:
            # Log or track that bookmarks were deleted
            # You could also add this information to the response if needed
            pass


class ApplicationDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a specific application
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsApplicant]
    lookup_field = 'application_id'

    def get_queryset(self):
        """Ensure users can only view their own applications"""
        try:
            applicant = self.request.user.applicant
            return Application.objects.filter(applicant_id=applicant)
        except (AttributeError, Applicant.DoesNotExist):
            return Application.objects.none()

class UserAppliedJobsView(generics.ListAPIView):
    """
    List all jobs that a user has applied for.
    - Regular users can only view their own applied jobs
    - Admin users can view any user's applied jobs by providing user_id parameter
    """
    serializer_class = UserAppliedJobsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = JobListPagination

    def get_queryset(self):
        # Check if admin is requesting another user's applications
        requested_user_id = self.request.query_params.get('user_id')

        if requested_user_id and requested_user_id != str(self.request.user.id):
            # Only admins can view other users' applications
            if not self.request.user.is_staff:
                return Application.objects.none()

            # Get the applicant profile for the requested user
            try:
                user = User.objects.get(id=requested_user_id)
                applicant = Applicant.objects.get(applicant_id=user)
                queryset = Application.objects.filter(applicant_id=applicant)
            except (User.DoesNotExist, Applicant.DoesNotExist):
                return Application.objects.none()
        else:
            # User is viewing their own applications
            try:
                applicant = self.request.user.applicant
                queryset = Application.objects.filter(applicant_id=applicant)
            except (AttributeError, Applicant.DoesNotExist):
                return Application.objects.none()

        # Apply filters
        # Get all filter parameters
        company_names = self.request.query_params.getlist('company_name')
        min_salary = self.request.query_params.get('min_salary')
        date_posted = self.request.query_params.get('date_posted')
        job_locations = self.request.query_params.getlist('job_location')  # Changed from 'location'
        job_titles = self.request.query_params.getlist('job_title')

        # Filter by company names
        if company_names:
            company_name_queries = Q()
            for name in company_names:
                company_name_queries |= Q(job_id__recruiter_id__company_id__company_name__icontains=name)
            queryset = queryset.filter(company_name_queries)
        elif company_name := self.request.query_params.get('company_name'):
            queryset = queryset.filter(job_id__recruiter_id__company_id__company_name__icontains=company_name)

        # Filter by minimum salary
        if min_salary:
            try:
                salary_value = float(min_salary)
                queryset = queryset.filter(job_id__job_salary__gte=salary_value)
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
                    try:
                        date_obj = datetime.strptime(date_posted, '%Y-%m-%d').date()
                        date_threshold = timezone.make_aware(datetime.combine(date_obj, datetime.min.time()))
                    except ValueError:
                        raise ValueError(
                            "Invalid date format, Expected `Past 24 hours` or `Past 3 days` or `Past week` or `Past month`")

                queryset = queryset.filter(job_id__job_date_posted__gte=date_threshold)

            except (ValueError, TypeError):
                pass  # Invalid date format, ignore filter

        # Filter by job locations
        if job_locations:
            location_queries = Q()
            for location in job_locations:
                location_queries |= Q(job_id__job_location__icontains=location)
            queryset = queryset.filter(location_queries)
        elif job_location := self.request.query_params.get('job_location'):  # Fallback to single parameter
            queryset = queryset.filter(job_id__job_location__icontains=job_location)

        # Filter by job titles
        if job_titles:
            title_queries = Q()
            for title in job_titles:
                title_queries |= Q(job_id__job_title__icontains=title)
            queryset = queryset.filter(title_queries)
        elif job_title := self.request.query_params.get('job_title'):  # Fallback to single param
            queryset = queryset.filter(job_id__job_title__icontains=job_title)

        # Final queryset with select_related for optimization and ordering
        return queryset.select_related(
            'job_id',
            'job_id__recruiter_id',
            'job_id__recruiter_id__company_id'
        ).order_by('-application_date_applied')

    def list(self, request, *args, **kwargs):
            # Handle permissions explicitly
            requested_user_id = request.query_params.get('user_id')

            if requested_user_id and requested_user_id != str(request.user.id) and not request.user.is_staff:
                return Response(
                    {"message": "You do not have permission to view other users' applications."},
                    status=status.HTTP_403_FORBIDDEN
                )

            try:
                # Check if current user has an applicant profile if viewing own applications
                if not requested_user_id or requested_user_id == str(request.user.id):
                    _ = request.user.applicant
            except (AttributeError, Applicant.DoesNotExist):
                return Response(
                    {"message": "You must have an applicant profile to view applied jobs."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get data with pagination support
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                response = self.get_paginated_response(serializer.data)

                # Customize the pagination response
                if isinstance(response.data, dict):
                    # Initialize default values
                    count = response.data.get('count', 0)
                    next_link = response.data.get('next', None)
                    previous_link = response.data.get('previous', None)

                    # Get page size from pagination class
                    page_size = self.pagination_class().page_size

                    # Get current page from request
                    current_page = request.query_params.get('page', 1)
                    try:
                        current_page = int(current_page)
                    except (ValueError, TypeError):
                        current_page = 1

                    # Calculate total pages
                    total_pages = (count + page_size - 1) // page_size if page_size > 0 else 0

                    # Create the new response format
                    new_data = {
                        'total_count': count,
                        'next': next_link,
                        'previous': previous_link,
                        'current_page': current_page,
                        'total_pages': total_pages,
                        'results': response.data.get('results', [])
                    }

                    # Update the response data
                    response.data = new_data



                return response

            # Handle case when pagination is not used
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "total_count": len(serializer.data),
                "next": None,
                "previous": None,
                "current_page": 1,
                "total_pages": 1,
                "results": serializer.data
            })

class JobApplicantsListView(generics.ListAPIView):
    """
    View to retrieve all applicants for a specific job with their complete details and resume
    """
    serializer_class = JobApplicantDetailSerializer
    permission_classes = [IsAuthenticated, IsRecruiter]
    pagination_class = JobListPagination

    def get_queryset(self):
        """
        This view returns a list of all applications for the job specified in the URL
        """
        job_id = self.kwargs.get('job_id')
        if not job_id:
            return Application.objects.none()

        # Filter applications by the specified job_id
        queryset = Application.objects.filter(job_id=job_id)

        # Apply status filter if provided in query params
        status = self.request.query_params.get('application_status')
        if status:
            queryset = queryset.filter(application_status=status)

        # Optimize query performance by prefetching related data
        queryset = queryset.select_related('applicant_id', 'applicant_id__applicant_id')

        return queryset

    def list(self, request, *args, **kwargs):
        job_id = self.kwargs.get('job_id')
        response = super().list(request, *args, **kwargs)

        if isinstance(response.data, dict) and 'results' in response.data:
            queryset = Application.objects.filter(job_id=job_id)

            # Get counts for different application statuses
            # Using the correct field name 'application_status' instead of 'status'
            pending_count = queryset.filter(application_status='Pending').count()
            rejected_count = queryset.filter(application_status='Rejected').count()
            applied_count = queryset.filter(application_status='Applied').count()

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

            # Create a new response structure with status counts
            new_data = {
                'total_count': count,
                'next': next_link,
                'previous': previous_link,
                'current_page': current_page,
                'total_pages': total_pages,
                'status_counts': {
                    'pending': pending_count,
                    'rejected': rejected_count,
                    'applied': applied_count,
                },
                'results': response.data.get('results', [])
            }

            response.data = new_data
        return response


# --------------- Recruiter Application ------------------- #

class RecruiterApplicationListView(generics.ListAPIView):
    """
    API view for recruiters to list applications for jobs posted by their company
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsRecruiter]
    pagination_class = JobListPagination

    def get_queryset(self):
        user = self.request.user
        try:
            # Since recruiter_id is OneToOneField to User, Django creates a reverse relation
            # but it's named 'recruiter', not 'recruiter_profile'
            recruiter = user.recruiter

            # The company field is named company_id in your model
            company = recruiter.company_id

            # Get all jobs from the same company
            # All recruiters have company_id field that references the same Company
            company_jobs = Job.objects.filter(recruiter_id__company_id=company)

            # Get all applications for jobs in this company
            queryset = Application.objects.filter(job_id__in=company_jobs)

            # Print for debugging - before any filtering
            print(f"Initial queryset count: {queryset.count()}")
            print(f"Initial statuses: {list(queryset.values_list('application_status', flat=True).distinct())}")

            # Apply application status filter only if provided in query parameters
            application_status = self.request.query_params.get('application_status', None)
            print(f"Requested status filter: {application_status}")

            # IMPORTANT: Force queryset to include ALL statuses if no filter is requested
            if application_status:
                valid_statuses = ['Pending', 'Approved', 'Rejected']
                if application_status in valid_statuses:
                    queryset = queryset.filter(application_status=application_status)
                    print(f"Filtered queryset by status: {application_status}")
            else:
                # Explicitly make sure we're not filtering by status
                # This is redundant but ensures we're getting all statuses
                print("No status filter applied - including ALL applications")

            queryset = queryset.order_by('-id')

            # Final check
            print(f"Final queryset count: {queryset.count()}")
            print(f"Final SQL query: {queryset.query}")

            return queryset

        except AttributeError as e:
            print(f"AttributeError: {e}")
            # User is not a recruiter
            return Application.objects.none()

class RecruiterApplicationUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        user = self.request.user
        try:
            recruiter = user.recruiter
            company = recruiter.company_id

            # Get all jobs from the same company
            company_jobs = Job.objects.filter(recruiter_id__company_id=company)

            # Return applications for jobs in this company
            return Application.objects.filter(job_id__in=company_jobs)
        except AttributeError:
            return Application.objects.none()

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()

        # Get the values from request.data
        new_status = request.data.get('application_status')
        new_comment = request.data.get('application_recruiter_comment')

        # Update fields if they're provided
        if new_status is not None:
            instance.application_status = new_status
        if new_comment is not None:
            instance.application_recruiter_comment = new_comment

        # Save the instance
        instance.save()

        # Serialize and return the updated instance
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class JobApplicationStatsView(APIView):
    permission_classes = [IsAuthenticated, IsActiveRecruiter]

    def get(self, request, job_id):
        try:
            # Get the job
            job = Job.objects.get(job_id=job_id)

            # Verify the recruiter belongs to the company that posted the job
            recruiter = Recruiter.objects.get(recruiter_id=request.user)
            job_company = job.recruiter_id.company_id

            if recruiter.company_id.company_id != job_company.company_id:
                return Response({
                    "message": "You don't have permission to view statistics for this job",
                    "error": True
                }, status=status.HTTP_403_FORBIDDEN)

            # Get application counts
            application_stats = Application.objects.filter(job_id=job_id)

            # Count total applications
            total_count = application_stats.count()

            # Count applications by status
            approved_count = application_stats.filter(application_status="APPROVED").count()
            rejected_count = application_stats.filter(application_status="REJECTED").count()
            pending_count = application_stats.filter(application_status="PENDING").count()

            return Response({
                "message": "Application statistics retrieved successfully",
                "error": False,
                "data": {
                    "job_id": job_id,
                    "total_applications": total_count,
                    "approved_applications": approved_count,
                    "rejected_applications": rejected_count,
                    "pending_applications": pending_count
                }
            }, status=status.HTTP_200_OK)

        except Job.DoesNotExist:
            return Response({
                "message": f"Job with ID {job_id} does not exist",
                "error": True
            }, status=status.HTTP_404_NOT_FOUND)
        except Recruiter.DoesNotExist:
            return Response({
                "message": "Recruiter profile not found",
                "error": True
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": f"An error occurred: {str(e)}",
                "error": True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
