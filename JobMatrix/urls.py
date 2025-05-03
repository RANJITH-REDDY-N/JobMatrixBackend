from django.urls import path

from JobMatrix.views.password_reset_view import PasswordResetRequestView, VerifyResetCodeView, ResetPasswordView, ChangePasswordView
from JobMatrix.views.views import *
from JobMatrix.views import check_broken_files

from JobMatrix.views.admin_dashboard import AdminDashboardCountsView
from JobMatrix.views.admin_actions import (
    AdminUserDeleteView,
    AdminCompanyListView,
    AdminCompanyDeleteView,
    AdminJobDeleteView
)

urlpatterns = [
    # Auth & User
    path("login/", LoginView.as_view(), name="login"),
    path("users/create/", UserCreateView.as_view(), name="create-user"),
    path("users/get/", UserRetrieveView.as_view(), name="get-users"),
    path("users/update/<int:pk>/", UserUpdateView.as_view(), name="update-user"),
    path("users/patch/<int:pk>/", UserPartialUpdateView.as_view(), name="patch-user"),
    path("users/resume-update/", ApplicantResumeUpdateView.as_view(), name="update-applicant-resume"),
    path("users/recruiter-update/", RecruiterDetailsUpdateView.as_view(), name="recruiter-details-update"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),  # New endpoint

    # Company
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('company-jobs/', CompanyJobsListView.as_view(), name='company-jobs-list'),
    path('company/update/', CompanyUpdateView.as_view(), name='company-update'),
    path('recruiter/company-stats/', RecruiterCompanyDetailView.as_view(), name='recruiter-company-stats'),

    # Admin Dashboard
    path('admin/dashboard-insights/', AdminDashboardCountsView.as_view(), name='admin-dashboard-insights'),

    # Admin User Management
    path("admin/users/all/", UserListView.as_view(), name="get-all-users-for-admin"),
    path('admin/users/<int:user_id>/delete/', AdminUserDeleteView.as_view(), name='admin-user-delete'),

    # Admin Company Management
    path('admin/companies/', AdminCompanyListView.as_view(), name='admin-companies'),
    path('admin/companies/<int:company_id>/delete/', AdminCompanyDeleteView.as_view(), name='admin-company-delete'),

    # Admin Job Management
    path('admin/jobs/<int:job_id>/delete/', AdminJobDeleteView.as_view(), name='admin-job-delete'),

    # Password Reset URLs
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='verify_reset_code'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),  # New endpoint
]

# Add this at the bottom after your other URL patterns
urlpatterns.append(path('admin/check-broken-files/', check_broken_files, name='check_broken_files'))