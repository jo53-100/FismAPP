#Importaciones y Modelos
from django.contrib import admin
from .models import (
    CustomUser, ProfessorProfile, AdministratorProfile,
    AlumniProfile, StudentProfile, News, Event,
    Schedule, SupportRequest, Survey, SurveyQuestion,
    SurveyOption
)


#Administración de usuario
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


#Noticias
@admin.action(description='Marcar como publicadas')
def mark_as_published(modeladmin, request, queryset):
    queryset.update(published=True)

def short_content(obj):
    return obj.content[:75] + "..." if obj.content else ""
short_content.short_description = "Resumen"

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published', 'created_at', short_content)
    list_filter = ('published', 'category', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    actions = [mark_as_published]

#Evento
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'location')
    list_filter = ('event_type', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'

#Horarios con búsqueda por profesor
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'professor', 'day_of_week', 'start_time', 'classroom')
    list_filter = ('day_of_week', 'semester')
    search_fields = ('course_name', 'course_code', 'professor__username')
    autocomplete_fields = ['professor']

#Solicitudes de soporte
@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'requester', 'category', 'status', 'priority', 'created_at')
    list_filter = ('status', 'category', 'priority')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

#Inlines para encuestas
class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 1

class SurveyOptionInline(admin.TabularInline):
    model = SurveyOption
    extra = 1

#Administración de encuestas con inlines
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'target_audience')
    search_fields = ('title', 'description')
    inlines = [SurveyQuestionInline]
    autocomplete_fields = ['creator']

#Registro de perfiles
admin.site.register(ProfessorProfile)
admin.site.register(AdministratorProfile)
admin.site.register(AlumniProfile)
admin.site.register(StudentProfile)

#Registro directo de preguntas y opciones si se desea acceder aparte
admin.site.register(SurveyQuestion)
admin.site.register(SurveyOption)
