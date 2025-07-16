# core/ admin.py
from django.contrib import admin
from .models import (
    CustomUser, ProfessorProfile, AdministratorProfile,
    AlumniProfile, StudentProfile, News, Event,
    Schedule, SupportRequest, Survey, SurveyQuestion,
    SurveyOption
)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published', 'created_at')
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'location')
    list_filter = ('event_type', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'professor', 'day_of_week', 'start_time', 'classroom')
    list_filter = ('day_of_week', 'semester')
    search_fields = ('course_name', 'course_code', 'professor__username')


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'requester', 'category', 'status', 'priority', 'created_at')
    list_filter = ('status', 'category', 'priority')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'target_audience')
    search_fields = ('title', 'description')


# Register profile models
admin.site.register(ProfessorProfile)
admin.site.register(AdministratorProfile)
admin.site.register(AlumniProfile)
admin.site.register(StudentProfile)

# Register survey components
admin.site.register(SurveyQuestion)
admin.site.register(SurveyOption)
