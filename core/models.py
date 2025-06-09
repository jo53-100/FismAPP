# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('professor', 'Professor'),
        ('administrator', 'Administrator'),
        ('alumni', 'Alumni'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES)

    def is_professor(self):
        return self.user_type == 'professor'

    def is_administrator(self):
        return self.user_type == 'administrator'

    def is_alumni(self):
        return self.user_type == 'alumni'

    def is_student(self):
        return self.user_type == 'student'


# Profile models for additional information
class ProfessorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    office_number = models.CharField(max_length=20)
    research_areas = models.TextField()
    id_docente = models.CharField(max_length=9, blank=True)


class AdministratorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    administrative_role = models.CharField(max_length=100)
    office_location = models.CharField(max_length=100)


class AlumniProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    graduation_year = models.IntegerField()
    current_occupation = models.CharField(max_length=200)
    company = models.CharField(max_length=200, blank=True)


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    enrollment_year = models.IntegerField()
    major = models.CharField(max_length=100)
    semester = models.IntegerField()


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=[
        ('academic', 'Academic'),
        ('events', 'Events'),
        ('announcements', 'Announcements'),
        ('research', 'Research'),
    ])
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)

    def publish(self):
        self.published = True
        self.published_date = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "News"


# Events model
class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=[
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
    ])
    registration_required = models.BooleanField(default=False)
    max_participants = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)

    class Meta:
        ordering = ['start_date']


# Schedule model
class Schedule(models.Model):
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20)
    professor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'professor'})
    day_of_week = models.CharField(max_length=10, choices=[
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    classroom = models.CharField(max_length=50)
    semester = models.CharField(max_length=20)

    class Meta:
        ordering = ['day_of_week', 'start_time']


# Support Request model
class SupportRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('facilities', 'Facilities'),
        ('other', 'Other'),
    ]

    requester = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_requests',
                                    limit_choices_to={'user_type': 'administrator'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


# Survey/Poll model
class Survey(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    target_audience = models.CharField(max_length=20, choices=CustomUser.USER_TYPES + (('all', 'All'),))

    class Meta:
        ordering = ['-start_date']


class SurveyQuestion(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('rating', 'Rating'),
    ])
    order = models.IntegerField()

    class Meta:
        ordering = ['order']


class SurveyOption(models.Model):
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=200)
    order = models.IntegerField()

    class Meta:
        ordering = ['order']


class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    respondent = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('survey', 'respondent')
