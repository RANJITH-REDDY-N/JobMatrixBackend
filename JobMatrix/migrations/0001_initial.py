# Generated by Django 5.1.7 on 2025-05-01 14:24

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('user_id', models.AutoField(db_column='user_id', primary_key=True, serialize=False)),
                ('user_first_name', models.CharField(db_column='user_first_name', max_length=255)),
                ('user_last_name', models.CharField(db_column='user_last_name', max_length=255)),
                ('user_email', models.EmailField(db_column='user_email', max_length=254, unique=True)),
                ('user_password', models.CharField(db_column='user_password', max_length=255, validators=[django.core.validators.MinLengthValidator(8)])),
                ('user_phone', models.CharField(blank=True, db_column='user_phone', max_length=15, null=True)),
                ('user_street_no', models.CharField(blank=True, db_column='user_street_no', max_length=100, null=True)),
                ('user_city', models.CharField(blank=True, db_column='user_city', max_length=100, null=True)),
                ('user_state', models.CharField(blank=True, db_column='user_state', max_length=100, null=True)),
                ('user_zip_code', models.CharField(blank=True, db_column='user_zip_code', max_length=10, null=True)),
                ('user_role', models.CharField(choices=[('ADMIN', 'ADMIN'), ('APPLICANT', 'APPLICANT'), ('RECRUITER', 'RECRUITER')], db_column='user_role', max_length=20)),
                ('user_profile_photo', models.FileField(blank=True, db_column='user_profile_photo', max_length=255, null=True, upload_to='profile_photos/')),
                ('user_created_date', models.DateTimeField(auto_now_add=True, db_column='user_created_date')),
            ],
            options={
                'db_table': 'USER',
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('company_id', models.AutoField(db_column='company_id', primary_key=True, serialize=False)),
                ('company_name', models.CharField(db_column='company_name', max_length=255, unique=True)),
                ('company_industry', models.CharField(db_column='company_industry', max_length=100)),
                ('company_description', models.TextField(db_column='company_description')),
                ('company_image', models.FileField(blank=True, db_column='company_image', max_length=255, null=True, upload_to='company_images/')),
                ('company_secret_key', models.CharField(db_column='company_secret_key', max_length=128)),
            ],
            options={
                'db_table': 'COMPANY',
            },
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('job_id', models.AutoField(db_column='job_id', primary_key=True, serialize=False)),
                ('job_title', models.CharField(db_column='job_title', max_length=255)),
                ('job_description', models.TextField(db_column='job_description')),
                ('job_location', models.CharField(db_column='job_location', max_length=255)),
                ('job_salary', models.DecimalField(db_column='job_salary', decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('job_date_posted', models.DateTimeField(auto_now_add=True, db_column='job_date_posted')),
            ],
            options={
                'db_table': 'JOB',
            },
        ),
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'PASSWORD_RESET_TOKEN',
            },
        ),
        migrations.CreateModel(
            name='Admin',
            fields=[
                ('admin_id', models.OneToOneField(db_column='admin_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='JobMatrix.user')),
                ('admin_ssn', models.CharField(db_column='admin_ssn', max_length=20, unique=True)),
            ],
            options={
                'db_table': 'ADMIN',
            },
        ),
        migrations.CreateModel(
            name='Applicant',
            fields=[
                ('applicant_id', models.OneToOneField(db_column='applicant_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='JobMatrix.user')),
                ('applicant_resume', models.FileField(blank=True, db_column='applicant_resume', max_length=255, null=True, upload_to='resumes/')),
            ],
            options={
                'db_table': 'APPLICANT',
            },
        ),
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('bookmark_id', models.AutoField(db_column='bookmark_id', primary_key=True, serialize=False)),
                ('bookmark_date_saved', models.DateTimeField(auto_now_add=True, db_column='bookmark_date_saved')),
                ('job_id', models.ForeignKey(db_column='job_id', on_delete=django.db.models.deletion.CASCADE, to='JobMatrix.job')),
                ('applicant_id', models.ForeignKey(db_column='applicant_id', on_delete=django.db.models.deletion.CASCADE, to='JobMatrix.applicant')),
            ],
            options={
                'db_table': 'BOOKMARK',
            },
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
                ('application_id', models.AutoField(db_column='application_id', primary_key=True, serialize=False)),
                ('application_status', models.CharField(choices=[('PENDING', 'PENDING'), ('APPROVED', 'APPROVED'), ('REJECTED', 'REJECTED')], db_column='application_status', default='PENDING', max_length=50)),
                ('application_recruiter_comment', models.TextField(blank=True, db_column='application_recruiter_comment', null=True)),
                ('application_date_applied', models.DateTimeField(auto_now_add=True, db_column='application_date_applied')),
                ('job_id', models.ForeignKey(db_column='job_id', on_delete=django.db.models.deletion.CASCADE, to='JobMatrix.job')),
                ('applicant_id', models.ForeignKey(db_column='applicant_id', on_delete=django.db.models.deletion.CASCADE, to='JobMatrix.applicant')),
            ],
            options={
                'db_table': 'APPLICATION',
            },
        ),
        migrations.CreateModel(
            name='Recruiter',
            fields=[
                ('recruiter_id', models.OneToOneField(db_column='recruiter_id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='JobMatrix.user')),
                ('recruiter_is_active', models.BooleanField(db_column='recruiter_is_active', default=True)),
                ('recruiter_start_date', models.DateField(db_column='recruiter_start_date')),
                ('recruiter_end_date', models.DateField(blank=True, db_column='recruiter_end_date', null=True)),
                ('company_id', models.ForeignKey(db_column='company_id', on_delete=django.db.models.deletion.CASCADE, related_name='recruiters', to='JobMatrix.company')),
            ],
            options={
                'db_table': 'RECRUITER',
            },
        ),
        migrations.AddField(
            model_name='job',
            name='recruiter_id',
            field=models.ForeignKey(db_column='recruiter_id', on_delete=django.db.models.deletion.CASCADE, to='JobMatrix.recruiter'),
        ),
        migrations.CreateModel(
            name='WorkExperience',
            fields=[
                ('work_experience_id', models.AutoField(db_column='work_experience_id', primary_key=True, serialize=False)),
                ('work_experience_job_title', models.CharField(db_column='work_experience_job_title', max_length=255)),
                ('work_experience_company', models.CharField(db_column='work_experience_company', max_length=255)),
                ('work_experience_summary', models.TextField(blank=True, db_column='work_experience_summary', max_length=5000, null=True)),
                ('work_experience_start_date', models.DateField(db_column='work_experience_start_date')),
                ('work_experience_end_date', models.DateField(blank=True, db_column='work_experience_end_date', null=True)),
                ('work_experience_is_currently_working', models.BooleanField(db_column='work_experience_is_currently_working', default=False)),
                ('applicant_id', models.ForeignKey(db_column='applicant_id', on_delete=django.db.models.deletion.CASCADE, related_name='work_experience', to='JobMatrix.applicant')),
            ],
            options={
                'db_table': 'WORK_EXPERIENCE',
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('work_experience_end_date__isnull', True), ('work_experience_is_currently_working', True)), models.Q(('work_experience_end_date__gt', models.F('work_experience_start_date')), ('work_experience_is_currently_working', False)), _connector='OR'), name='check_work_experience_end_date')],
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('skill_id', models.AutoField(db_column='skill_id', primary_key=True, serialize=False)),
                ('skill_name', models.CharField(db_column='skill_name', max_length=255)),
                ('skill_years_of_experience', models.PositiveIntegerField(db_column='skill_years_of_experience', default=0)),
                ('applicant_id', models.ForeignKey(db_column='applicant_id', on_delete=django.db.models.deletion.CASCADE, related_name='skills', to='JobMatrix.applicant')),
            ],
            options={
                'db_table': 'SKILL',
                'constraints': [models.CheckConstraint(condition=models.Q(('skill_years_of_experience__gte', 0)), name='check_skill_experience')],
            },
        ),
        migrations.CreateModel(
            name='Education',
            fields=[
                ('education_id', models.AutoField(db_column='education_id', primary_key=True, serialize=False)),
                ('education_school_name', models.CharField(db_column='education_school_name', max_length=255)),
                ('education_degree_type', models.CharField(db_column='education_degree_type', max_length=100)),
                ('education_major', models.CharField(blank=True, db_column='education_major', max_length=255, null=True)),
                ('education_gpa', models.DecimalField(blank=True, db_column='education_gpa', decimal_places=2, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('education_start_date', models.DateField(db_column='education_start_date')),
                ('education_end_date', models.DateField(blank=True, db_column='education_end_date', null=True)),
                ('education_is_currently_enrolled', models.BooleanField(db_column='education_is_currently_enrolled', default=False)),
                ('applicant_id', models.ForeignKey(db_column='applicant_id', on_delete=django.db.models.deletion.CASCADE, related_name='education', to='JobMatrix.applicant')),
            ],
            options={
                'db_table': 'EDUCATION',
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('education_end_date__isnull', True), ('education_is_currently_enrolled', True)), models.Q(('education_end_date__gt', models.F('education_start_date')), ('education_is_currently_enrolled', False)), _connector='OR'), name='check_education_end_date')],
            },
        ),
        migrations.AddConstraint(
            model_name='job',
            constraint=models.CheckConstraint(condition=models.Q(('job_salary__gte', 0)), name='check_job_salary'),
        ),
    ]
