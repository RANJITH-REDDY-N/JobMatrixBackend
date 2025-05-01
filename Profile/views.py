from django.shortcuts import render
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.utils import timezone
from .serializers import WorkExperienceSerializer, EducationSerializer, SkillSerializer
from JobMatrix.models import Applicant, User, WorkExperience, Education, Skill
from collections import defaultdict
from JobMatrix.auth_backend import JWTAuthentication
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.core.exceptions import FieldError



User = get_user_model()

# ================================================
# WORK EXPERIENCE VIEW
# ================================================

class WorkExperienceCreateView(generics.CreateAPIView):
    serializer_class = WorkExperienceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Get the applicant linked to the authenticated user
        try:
            applicant = Applicant.objects.get(applicant_id=self.request.user.user_id)
            serializer.save(applicant_id=applicant)
        except Applicant.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise serializers.ValidationError("User is not registered as an applicant")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Work experience created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class UserWorkExperienceListView(generics.ListAPIView):
    serializer_class = WorkExperienceSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if not user_id:
            return WorkExperience.objects.none()

        try:
            applicant = Applicant.objects.get(applicant_id=user_id)
            return WorkExperience.objects.filter(applicant_id=applicant)
        except Applicant.DoesNotExist:
            return WorkExperience.objects.none()

    def parse_date(self, date_string):
        if not date_string or date_string == 'Present':
            return None

        formats_to_try = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]

        for date_format in formats_to_try:
            try:
                return datetime.strptime(date_string, date_format)
            except ValueError:
                continue

        return None

    def calculate_experience_duration(self, start_date_str, end_date_str=None):

        start_date = self.parse_date(start_date_str)
        if not start_date:
            return {"years": 0, "months": 0, "days": 0}

        if not end_date_str or end_date_str == 'Present':
            end_date = datetime.now()
        else:
            end_date = self.parse_date(end_date_str)
            if not end_date:
                end_date = datetime.now()

        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()

        if start_date > end_date:
            return {"years": 0, "months": 0, "days": 0}

        years = end_date.year - start_date.year

        if (end_date.month, end_date.day) < (start_date.month, start_date.day):
            years -= 1

        months = end_date.month - start_date.month
        if months < 0:
            months += 12

        if end_date.day < start_date.day:
            months = (months - 1) % 12

        comparison_day = min(start_date.day, [31, 29 if end_date.year % 4 == 0 and (
                    end_date.year % 100 != 0 or end_date.year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30,
                                              31][end_date.month - 1])

        if end_date.day >= start_date.day:
            days = end_date.day - start_date.day
        else:
            days = end_date.day + (comparison_day - start_date.day)

        return {
            "years": years,
            "months": months,
            "days": days
        }

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')
        if not user_id:
            return Response({
                "status": "error",
                "message": "user_id parameter is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        authenticated_user_id = str(request.user.user_id)
        requested_user_id = str(user_id)
        if authenticated_user_id != requested_user_id:
            return Response({
                "status": "error",
                "message": "You can only view your own work experience details"
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({
                "status": "error",
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        processed_data = []

        total_years = 0
        total_months = 0
        total_days = 0

        for item in serializer.data:
            start_date = item.get('work_experience_start_date')
            end_date = item.get('work_experience_end_date')

            duration = self.calculate_experience_duration(start_date, end_date)

            total_years += duration['years']
            total_months += duration['months']
            total_days += duration['days']

            experience_parts = []
            if duration['years'] > 0:
                experience_parts.append(f"{duration['years']} years")
            if duration['months'] > 0:
                experience_parts.append(f"{duration['months']} months")
            if duration['days'] > 0:
                experience_parts.append(f"{duration['days']} days")

            experience_str = ", ".join(experience_parts) if experience_parts else "0 days"
            item['experience_duration'] = experience_str
            processed_data.append(item)

        total_months += total_days // 30
        total_days = total_days % 30
        total_years += total_months // 12
        total_months = total_months % 12

        total_parts = []
        if total_years > 0:
            total_parts.append(f"{total_years} years")
        if total_months > 0:
            total_parts.append(f"{total_months} months")
        if total_days > 0:
            total_parts.append(f"{total_days} days")

        total_exp_str = ", ".join(total_parts) if total_parts else "0 days"

        return Response({
            "status": "success",
            "message": "Work experience records retrieved successfully",
            "data": processed_data,
            "total_experience": total_exp_str
        })

class WorkExperienceUpdateView(generics.UpdateAPIView):
    """
    API view for updating a work experience record
    Only the owner of the work experience can update their own record
    """
    serializer_class = WorkExperienceSerializer
    queryset = WorkExperience.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'work_experience_id'

    def update(self, request, *args, **kwargs):
        # Get the work experience record
        work_experience_id = self.kwargs.get('work_experience_id')

        try:
            work_experience = WorkExperience.objects.get(work_experience_id=work_experience_id)
        except WorkExperience.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Work experience record not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the authenticated user is the owner of this work experience record
        # Get the applicant_id associated with the authenticated user
        try:
            user_applicant = Applicant.objects.get(applicant_id=request.user.user_id)
        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "You are not authorized to update this work experience record"
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if the work experience record belongs to the authenticated user
        if work_experience.applicant_id != user_applicant:
            return Response({
                "status": "error",
                "message": "You can only update your own work experience records"
            }, status=status.HTTP_403_FORBIDDEN)

        # Proceed with the update if authorization passes
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(work_experience, data=request.data, partial=partial)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Work experience updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Invalid data provided",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class WorkExperienceDeleteView(generics.DestroyAPIView):
    queryset = WorkExperience.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    lookup_field = 'work_experience_id'

    def destroy(self, request, *args, **kwargs):
        work_experience_id = self.kwargs.get('work_experience_id')

        try:
            work_experience = WorkExperience.objects.get(work_experience_id=work_experience_id)
        except WorkExperience.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Work experience record not found"
            }, status=status.HTTP_404_NOT_FOUND)
        try:
            user_applicant = Applicant.objects.get(applicant_id=request.user.user_id)
        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "You are not authorized to delete this work experience record"
            }, status=status.HTTP_403_FORBIDDEN)

        if work_experience.applicant_id != user_applicant:
            return Response({
                "status": "error",
                "message": "You can only delete your own work experience records"
            }, status=status.HTTP_403_FORBIDDEN)

        work_experience.delete()

        return Response({
            "status": "success",
            "message": "Work experience record deleted successfully"
        }, status=status.HTTP_200_OK)


# ================================================
# SKILL VIEW
# ================================================


class ApplicantSkillCreateView(generics.CreateAPIView):
    """
    API view for creating a skill record for an applicant
    Only the applicant can add skills to their own profile
    """
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        applicant_id = request.data.get('applicant_id')

        if not applicant_id and 'applicant_id' in kwargs:
            applicant_id = kwargs.get('applicant_id')

        if not applicant_id:
            return Response({
                "status": "error",
                "message": "Applicant ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the authenticated user is the same as the applicant
        try:
            # Get authenticated user's applicant record
            authenticated_applicant = Applicant.objects.get(applicant_id=request.user.user_id)

            # Get the target applicant
            target_applicant = Applicant.objects.get(applicant_id=applicant_id)

            # Compare the two
            if authenticated_applicant != target_applicant:
                return Response({
                    "status": "error",
                    "message": "You can only add skills to your own profile"
                }, status=status.HTTP_403_FORBIDDEN)

        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Applicant not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Create a new skill for this applicant
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Ensure the applicant_id is set to the authenticated user's applicant
            serializer.validated_data['applicant_id'] = authenticated_applicant
            serializer.save()

            return Response({
                "status": "success",
                "message": "Skill added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "error",
                "message": "Invalid data provided",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class ApplicantSkillListView(generics.ListAPIView):
    """
    API view for listing skills of an applicant
    Only the applicant can view their own skills
    """
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        # By default, empty queryset
        return Skill.objects.none()

    def list(self, request, *args, **kwargs):
        # Get the applicant ID from the URL
        applicant_id = self.kwargs.get('applicant_id')

        if not applicant_id:
            return Response({
                "status": "error",
                "message": "Applicant ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            authenticated_applicant = Applicant.objects.get(applicant_id=request.user.user_id)

            target_applicant = Applicant.objects.get(applicant_id=applicant_id)

            if authenticated_applicant != target_applicant:
                return Response({
                    "status": "error",
                    "message": "You can only view your own skills"
                }, status=status.HTTP_403_FORBIDDEN)

        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Applicant not found"
            }, status=status.HTTP_404_NOT_FOUND)

        skills = Skill.objects.filter(applicant_id=authenticated_applicant)
        serializer = self.get_serializer(skills, many=True)

        return Response({
            "status": "success",
            "message": "Skills retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class ApplicantSkillUpdateView(generics.UpdateAPIView):
    """
    API view for updating a specific skill of an applicant
    Only the applicant can edit their own skills
    """
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    http_method_names = ['patch']  # Only allow PATCH method

    def get_queryset(self):
        return Skill.objects.none()

    def update(self, request, *args, **kwargs):
        skill_id = self.kwargs.get('skill_id')

        if not skill_id:
            return Response({
                "status": "error",
                "message": "Skill ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            skill = Skill.objects.get(skill_id=skill_id)
        except Skill.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Skill not found"
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            authenticated_applicant = Applicant.objects.get(applicant_id=request.user.user_id)

            if skill.applicant_id != authenticated_applicant:
                return Response({
                    "status": "error",
                    "message": "You can only edit your own skills"
                }, status=status.HTTP_403_FORBIDDEN)

        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Applicant not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(skill, data=request.data, partial=True)

        if serializer.is_valid():
            if 'applicant_id' in serializer.validated_data:
                serializer.validated_data.pop('applicant_id')

            serializer.save()

            return Response({
                "status": "success",
                "message": "Skill updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Invalid data provided",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class ApplicantSkillDeleteView(generics.DestroyAPIView):
    """
    API view for deleting a specific skill of an applicant
    Only the applicant can delete their own skills
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        # By default, empty queryset
        return Skill.objects.none()

    def destroy(self, request, *args, **kwargs):
        # Get the skill ID from the URL
        skill_id = self.kwargs.get('skill_id')

        if not skill_id:
            return Response({
                "status": "error",
                "message": "Skill ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the skill object
        try:
            skill = Skill.objects.get(skill_id=skill_id)
        except Skill.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Skill not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if the authenticated user is the owner of the skill
        try:
            # Get authenticated user's applicant record
            authenticated_applicant = Applicant.objects.get(applicant_id=request.user.user_id)

            # Check if the skill belongs to the authenticated applicant
            if skill.applicant_id != authenticated_applicant:
                return Response({
                    "status": "error",
                    "message": "You can only delete your own skills"
                }, status=status.HTTP_403_FORBIDDEN)

        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Applicant not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Get skill details before deletion for the response
        skill_name = skill.skill_name

        # Delete the skill
        skill.delete()

        return Response({
            "status": "success",
            "message": f"Skill '{skill_name}' deleted successfully"
        }, status=status.HTTP_200_OK)



# ================================================
# EDUCATION VIEW
# ================================================
class ApplicantEducationCreateView(generics.CreateAPIView):
    """
    API view for creating an education record for an applicant
    Only the applicant can add education to their own profile
    """
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        # Get the applicant ID from the request body
        applicant_id = request.data.get('applicant_id')

        if not applicant_id:
            return Response({
                "status": "error",
                "message": "Applicant ID is required in the request body"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if the authenticated user is the same as the applicant
        try:
            # Get authenticated user's applicant record
            # Use the current user to find their applicant record
            # Assuming there's a relationship between User and Applicant
            authenticated_applicant = Applicant.objects.get(applicant_id=request.user.applicant.applicant_id)

            # Get the target applicant
            target_applicant = Applicant.objects.get(applicant_id=applicant_id)

            # Compare the two
            if authenticated_applicant.applicant_id != target_applicant.applicant_id:
                return Response({
                    "status": "error",
                    "message": "You can only add education to your own profile"
                }, status=status.HTTP_403_FORBIDDEN)

        except Applicant.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Applicant not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            return Response({
                "status": "error",
                "message": "User is not associated with an applicant profile"
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if end date is provided when is_currently_enrolled is False
        is_currently_enrolled = request.data.get('education_is_currently_enrolled')
        if is_currently_enrolled is not None and not is_currently_enrolled and not request.data.get(
                'education_end_date'):
            return Response({
                "status": "error",
                "message": "End date is required when not currently enrolled"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create a new education record for this applicant
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "status": "success",
                "message": "Education record added successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": "error",
                "message": "Invalid data provided",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

class UserEducationListView(generics.ListAPIView):
    """
    API view for retrieving the current user's education details.
    Users can only access their own education details.
    """
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        # Use user_id instead of id
        return Education.objects.filter(applicant_id=self.request.user.user_id)

    def list(self, request, *args, **kwargs):
        user_id = self.kwargs.get('user_id')

        # Use user_id attribute instead of id
        current_user_id = request.user.user_id

        # If the user is trying to access someone else's data, return a 403
        if int(user_id) != current_user_id:
            return Response({
                "status": "error",
                "message": "You can only access your own education records"
            }, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset()

        if not queryset.exists():
            return Response({
                "status": "error",
                "message": "No education records found for your account"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "status": "success",
            "message": "Your education records retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class UserEducationUpdateView(generics.UpdateAPIView):
    """
    API view for updating a specific education record.
    Users can only update their own education records.
    """
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        education_id = self.kwargs.get('education_id')
        # Get the education record
        education = get_object_or_404(Education, education_id=education_id)

        # Check if the education record belongs to the current user
        if education.applicant_id.applicant_id_id != self.request.user.user_id:
            self.permission_denied(
                self.request,
                message="You do not have permission to update this education record"
            )

        return education

    def update(self, request, *args, **kwargs):
        # Only allow PATCH method for partial updates
        if request.method != 'PATCH':
            return Response({
                "status": "error",
                "message": "Only PATCH method is allowed for this endpoint"
            }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        partial = kwargs.pop('partial', True)  # Always use partial=True for PATCH
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Education record updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Failed to update education record",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserEducationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a specific education record.
    Users can only access their own education records.
    """
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        education_id = self.kwargs.get('education_id')
        # Get the education record
        education = get_object_or_404(Education, education_id=education_id)

        # Check if the education record belongs to the current user
        if education.applicant_id.applicant_id_id != self.request.user.user_id:
            self.permission_denied(
                self.request,
                message="You do not have permission to access this education record"
            )

        return education

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            "status": "success",
            "message": "Education record retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Education record updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": "Failed to update education record",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            education_id = instance.education_id  # Save before deletion for the response

            self.perform_destroy(instance)

            return Response({
                "status": "success",
                "message": f"Education record {education_id} deleted successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": f"Failed to delete education record: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
