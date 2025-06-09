from django.contrib import admin
from .models import CertificateTemplate, GeneratedCertificate, CoursesHistory


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'department_name', 'secretary_name', 'created_at')
    search_fields = ('name', 'department_name', 'secretary_name')
    readonly_fields = ('id',)  # Make ID visible but read-only

@admin.register(GeneratedCertificate)
class GeneratedCertificateAdmin(admin.ModelAdmin):
    list_display = ('professor', 'template', 'verification_code', 'generated_at')
    list_filter = ('template', 'generated_at')
    search_fields = ('professor__username', 'professor__first_name', 'professor__last_name', 'verification_code')
    readonly_fields = ('id', 'verification_code', 'generated_at')


@admin.register(CoursesHistory)
class CoursesHistoryAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'materia', 'periodo', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin')
    list_filter = ('periodo', 'fecha_inicio')
    search_fields = ('profesor', 'materia', 'clave', 'nrc')
    date_hierarchy = 'fecha_inicio'
