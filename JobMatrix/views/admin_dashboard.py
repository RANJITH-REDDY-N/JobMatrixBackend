from datetime import timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from JobMatrix.models import User, Company, Job, Admin, Applicant, Recruiter, Application, Bookmark
from JobMatrix.auth_backend import JWTAuthentication
from JobMatrix.permissions import IsAdmin

class AdminDashboardCountsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            today = now()
            last_week = today - timedelta(days=7)

            # Base counts
            total_users = User.objects.count()
            total_applicants = Applicant.objects.count()
            total_recruiters = Recruiter.objects.count()
            total_admins = Admin.objects.count()

            total_companies = Company.objects.count()
            total_jobs = Job.objects.count()
            total_bookmarks = Bookmark.objects.count()
            total_applications = Application.objects.count()

            # New this week
            new_users = User.objects.filter(user_created_date__gte=last_week).count()
            new_jobs = Job.objects.filter(job_date_posted__gte=last_week).count()
            new_admins = User.objects.filter(user_created_date__gte=last_week, user_role='admin').count()

            # NOTE: Company created date is not available, so we skip trend for it
            new_companies = None

            def calc_trend(new_count, total):
                if not new_count or not total:
                    return 0
                return round((new_count / total) * 100, 2)

            # Industry-wise job distribution
            job_distribution_qs = (
                Job.objects.values('recruiter_id__company_id__company_industry')
                .annotate(count=Count('job_id'))
                .order_by('-count')
            )

            job_distribution = [
                {
                    "industry_type": entry["recruiter_id__company_id__company_industry"],
                    "count": entry["count"]
                }
                for entry in job_distribution_qs
            ]

            data = {
                "users": {
                    "total": total_users,
                    "new_this_week": new_users,
                    "trend": calc_trend(new_users, total_users),
                    "applicants": total_applicants,
                    "recruiters": total_recruiters,
                    "admins": total_admins,
                },
                "companies": {
                    "total": total_companies,
                    "new_this_week": new_companies,
                    "trend": None,  # No created date
                },
                "jobs": {
                    "total": total_jobs,
                    "new_this_week": new_jobs,
                    "trend": calc_trend(new_jobs, total_jobs),
                    "distribution_by_industry": list(job_distribution),
                },
                "admins": {
                    "total": total_admins,
                    "new_this_week": new_admins,
                    "trend": calc_trend(new_admins, total_admins),
                },
                "activity": {
                    "total_applications": total_applications,
                    "total_bookmarks": total_bookmarks,
                }
            }

            return Response({
                "message": "Dashboard insights fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": "Failed to fetch dashboard insights",
                "data": {},
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
