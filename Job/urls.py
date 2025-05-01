from django.urls import path
from .views import *


urlpatterns = [
    path('create/', JobCreateView.as_view(), name='create-job'),
    path('create-jobs/', JobCreateViewMultiple.as_view(), name='create-jobs'),
    path('jobs-list/', CompanyJobsListView.as_view(), name='jobs-list'),
    path('<int:job_id>/update/', JobUpdateView.as_view(), name='job-update'),
    path('<int:job_id>/delete/', JobDeleteView.as_view(), name='job-delete'),


    # -------- Bookmark ----------- #

    path('bookmarks/', BookmarkView.as_view(), name='bookmark-list-create'),
    path('bookmarks/get/', BookmarkListView.as_view(), name='bookmark-list'),
    path('bookmarks/<int:bookmark_id>/', BookmarkDetailView.as_view(), name='bookmark-detail'),

    # ---------- Application ----------- #

    path('applications/', ApplicationView.as_view(), name='application-list-create'),
    path('applications/<int:application_id>/', ApplicationDetailView.as_view(), name='application-detail'),
    # path('job/<int:job_id>/application-status/', ApplicationStatusView.as_view(), name='application-status'),
    path('applied/', UserAppliedJobsView.as_view(), name='user-applied-jobs'),

    # --------- Recruiter Application ------------- #

    path('recruiter/applications/', RecruiterApplicationListView.as_view(), name='recruiter-applications-list'),
    path('recruiter/applications/<int:pk>/', RecruiterApplicationUpdateAPIView.as_view(), name='recruiter-application-update'),
    path('applicants/<int:job_id>/', JobApplicantsListView.as_view(), name='job-applicants-list'),
    path('recruiter/application-stats/<int:job_id>/', JobApplicationStatsView.as_view(), name='job-application-stats'),


]