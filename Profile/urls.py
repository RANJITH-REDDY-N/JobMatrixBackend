from django.urls import path
from Profile.views import *

urlpatterns = [

    # ------------------------- Work Experience ------------------------

    path("work-experience/create/", WorkExperienceCreateView.as_view(), name="create-work-experience"),
    path("work-experience/user/<int:user_id>/", UserWorkExperienceListView.as_view(),
         name="specific-user-work-experience"),
    path("work-experience/update/<int:work_experience_id>/", WorkExperienceUpdateView.as_view(),
             name="update-work-experience"),
    path("work-experience/delete/<int:work_experience_id>/", WorkExperienceDeleteView.as_view(),
         name='work-experience-delete'),

    # ------------------------- Skill ------------------------------

    path("skill/create/", ApplicantSkillCreateView.as_view(), name="create-skill" ),
    path('skill/user/<str:applicant_id>/', ApplicantSkillListView.as_view(), name='applicant-skill-list'),
    path('skill/update/<str:skill_id>/', ApplicantSkillUpdateView.as_view(), name='applicant-skill-update'),
    path('skill/delete/<str:skill_id>/', ApplicantSkillDeleteView.as_view(), name='applicant-skill-delete'),

    # ------------------------- Education ------------------------------

    path('education/create/', ApplicantEducationCreateView.as_view(), name='applicant-education-create'),
    path('education/user/<int:user_id>/', UserEducationListView.as_view(), name='applicant-education-list'),
    path('education/update/<int:education_id>/', UserEducationUpdateView.as_view(), name='education-update'),
    path('education/delete/<int:education_id>/', UserEducationDetailView.as_view(), name='education-detail'),

]