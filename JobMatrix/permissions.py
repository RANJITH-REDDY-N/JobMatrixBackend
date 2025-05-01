from rest_framework.permissions import BasePermission
from .models import Recruiter
import logging

logger = logging.getLogger(__name__)



class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_role == 'ADMIN'

class IsRecruiter(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.user_role == 'RECRUITER'

class IsApplicant(BasePermission):
    # def has_permission(self, request, view):
    #     return request.user and request.user.user_role == 'APPLICANT'
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'applicant')
        )


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.user_role == 'ADMIN' or obj.user_id == request.user.user_id

class IsSelf(BasePermission):
    def has_permission(self, request, view):
        email_param = request.query_params.get('user_email')
        if not request.user.is_authenticated:
            return False

        user_str = str(request.user)
        if '(' in user_str:
            potential_email = user_str.split(' (')[0]
            if potential_email == email_param:
                return True

        for attr_name in ['email', 'username', 'user_id']:
            if hasattr(request.user, attr_name):
                attr_value = getattr(request.user, attr_name)
                if attr_value == email_param:
                    return True
        return False


# class IsActiveRecruiter(BasePermission):
#     """
#     Custom permission to only allow active recruiters to access the view.
#     """
#
#     def has_permission(self, request, view):
#         try:
#             return Recruiter.objects.filter(
#                 recruiter_id=request.user.id,
#                 recruiter_is_active=True
#             ).exists()
#         except:
#             return False

class IsActiveRecruiter(BasePermission):
    """
    Custom permission to only allow active recruiters to access the view.
    """

    def has_permission(self, request, view):
        try:
            if not request.user.is_authenticated:
                return False

            # Check if user is a recruiter
            if request.user.user_role != 'RECRUITER':
                return False

            # Check if recruiter is active
            return Recruiter.objects.filter(
                recruiter_id=request.user,
                recruiter_is_active=True
            ).exists()
        except Exception as e:
            print(f"Permission error: {str(e)}")
            return False

class IsCompanyRecruiter(BasePermission):
    """
    Permission to only allow recruiters who belong to a company to view its jobs.
    """

    def has_permission(self, request, view):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if the user is a recruiter
        if not hasattr(request.user, 'recruiter'):
            return False

        # For listing jobs by company_id, check if the recruiter belongs to that company
        company_id = view.kwargs.get('company_id')
        if company_id:
            return request.user.recruiter.company_id.company_id == int(company_id)

        return True




