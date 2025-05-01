from django.utils import timezone

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from JobMatrix.models import User, Applicant, Application, Bookmark, Skill, WorkExperience, Education
from JobMatrix.auth_backend import JWTAuthentication
from JobMatrix.permissions import IsAdmin


class AdminUserDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def delete(self, request, user_id):
        try:
            user = get_object_or_404(User, user_id=user_id)

            # Only allow deletion of applicants (as per requirements)
            if user.user_role == 'APPLICANT':
                applicant = Applicant.objects.filter(applicant_id=user.user_id).first()
                if applicant:
                    # Delete all related data
                    Skill.objects.filter(applicant_id=applicant).delete()
                    Education.objects.filter(applicant_id=applicant).delete()
                    WorkExperience.objects.filter(applicant_id=applicant).delete()
                    Bookmark.objects.filter(applicant_id=applicant).delete()
                    Application.objects.filter(applicant_id=applicant).delete()
                    applicant.delete()

                # Delete user record
                user.delete()

                return Response({
                    "message": "Applicant and all related data deleted successfully",
                    "data": []
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "Only applicants can be deleted. Recruiters and admins cannot be deleted.",
                    "data": []
                }, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({
                "message": "Failed to delete user",
                "data": [],
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from JobMatrix.models import Company, Recruiter, Job
from JobMatrix.auth_backend import JWTAuthentication
from JobMatrix.permissions import IsAdmin


class AdminCompanyListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            # Get all companies
            companies = Company.objects.all()

            # Prepare the response data
            response_data = []

            for company in companies:
                # Get all recruiters for this company with recruiter_is_active filter
                recruiters = Recruiter.objects.filter(
                    company_id=company.company_id
                ).select_related('recruiter_id')

                # Get the active and inactive recruiters
                active_recruiters = [r for r in recruiters if r.recruiter_is_active]
                inactive_recruiters = [r for r in recruiters if not r.recruiter_is_active]

                # Get all recruiter IDs (both active and inactive)
                all_recruiter_ids = [r.recruiter_id.user_id for r in recruiters]

                # Count total jobs for this company from all its recruiters (active and inactive)
                total_jobs = Job.objects.filter(recruiter_id__in=recruiters).count()

                # Build recruiter data
                active_recruiter_data = []
                for recruiter in active_recruiters:
                    # Get user details
                    user = recruiter.recruiter_id

                    # Count jobs by this specific recruiter
                    recruiter_job_count = Job.objects.filter(recruiter_id=recruiter).count()

                    active_recruiter_data.append({
                        'recruiter_id': user.user_id,
                        'name': f"{user.user_first_name} {user.user_last_name}",
                        'email': user.user_email,
                        'phone': user.user_phone,
                        'profile_photo': str(user.user_profile_photo) if user.user_profile_photo else None,
                        'start_date': recruiter.recruiter_start_date,
                        'job_count': recruiter_job_count
                    })

                # Build inactive recruiter data
                inactive_recruiter_data = []
                for recruiter in inactive_recruiters:
                    user = recruiter.recruiter_id
                    # Count jobs by this inactive recruiter
                    recruiter_job_count = Job.objects.filter(recruiter_id=recruiter).count()
                    inactive_recruiter_data.append({
                        'recruiter_id': user.user_id,
                        'name': f"{user.user_first_name} {user.user_last_name}",
                        'email': user.user_email,
                        'phone': user.user_phone,
                        'profile_photo': str(user.user_profile_photo) if user.user_profile_photo else None,
                        'start_date': recruiter.recruiter_start_date,
                        'end_date': recruiter.recruiter_end_date,
                        'job_count': recruiter_job_count

                    })

                # Add company data to response
                company_data = {
                    'company_id': company.company_id,
                    'company_name': company.company_name,
                    'company_industry': company.company_industry,
                    'company_description': company.company_description,
                    'company_image': str(company.company_image) if company.company_image else None,
                    'active_recruiters_count': len(active_recruiters),
                    'inactive_recruiters_count': len(inactive_recruiters),
                    'total_jobs': total_jobs,
                    'active_recruiters': active_recruiter_data,
                    'inactive_recruiters': inactive_recruiter_data
                }

                response_data.append(company_data)

            return Response({
                "message": "Companies with recruiters and job counts fetched successfully",
                "data": response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "Failed to fetch companies information",
                "data": [],
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from JobMatrix.models import Company, Recruiter, Job, Bookmark, Application, User
from JobMatrix.auth_backend import JWTAuthentication
from JobMatrix.permissions import IsAdmin


class AdminCompanyDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def delete(self, request, company_id):
        try:
            with transaction.atomic():  # Use transaction to ensure atomicity
                company = get_object_or_404(Company, company_id=company_id)

                # Get all recruiters associated with this company
                recruiters = Recruiter.objects.filter(company_id=company)
                recruiter_users = []

                # Get all users who are recruiters for this company
                for recruiter in recruiters:
                    recruiter_users.append(recruiter.recruiter_id)

                # Get all jobs posted by recruiters of this company
                jobs = Job.objects.filter(recruiter_id__in=recruiters)

                # Delete bookmarks for these jobs
                bookmark_count = Bookmark.objects.filter(job_id__in=jobs).delete()[0]

                # Delete applications for these jobs
                application_count = Application.objects.filter(job_id__in=jobs).delete()[0]

                # Delete all jobs
                job_count = jobs.delete()[0]

                # Delete recruiters
                recruiter_count = recruiters.delete()[0]

                # Delete all user records for recruiters
                user_count = 0
                for user in recruiter_users:
                    if user.user_role == 'RECRUITER':
                        user.delete()
                        user_count += 1

                # Finally, delete the company
                company_name = company.company_name
                company.delete()

                return Response({
                    "message": f"Company '{company_name}' and all related data deleted successfully",
                    "details": {
                        "deleted_bookmarks": bookmark_count,
                        "deleted_applications": application_count,
                        "deleted_jobs": job_count,
                        "deleted_recruiters": recruiter_count,
                        "deleted_users": user_count
                    }
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "Failed to delete company",
                "data": [],
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AdminJobDeleteView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def delete(self, request, job_id):
        try:
            job = get_object_or_404(Job, job_id=job_id)

            Bookmark.objects.filter(job_id=job).delete()
            Application.objects.filter(job_id=job).delete()
            job.delete()

            return Response({
                "message": "Job and related data deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "Failed to delete job",
                "data": [],
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
