from rest_framework import serializers
from JobMatrix.models import WorkExperience, Education, Skill


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            'work_experience_id',
            'applicant_id',
            'work_experience_job_title',
            'work_experience_company',
            'work_experience_summary',
            'work_experience_start_date',
            'work_experience_end_date',
            'work_experience_is_currently_working'
        ]
        read_only_fields = ['work_experience_id']

    def validate(self, data):
        is_currently_working = data.get('work_experience_is_currently_working')
        end_date = data.get('work_experience_end_date')
        start_date = data.get('work_experience_start_date')

        # If currently working, end_date should be null
        if is_currently_working and end_date is not None:
            raise serializers.ValidationError("End date should be empty if currently working at this Job")

        # If not currently working, end date should be provided and after start date
        if not is_currently_working:
            if end_date is None:
                raise serializers.ValidationError("End date is required if not currently working")
            if end_date and start_date and end_date <= start_date:
                raise serializers.ValidationError("End date must be after start date")

        return data

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['skill_id', 'skill_name', 'skill_years_of_experience']
        extra_kwargs = {
            'skill_id': {'read_only': True}
        }