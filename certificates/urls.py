# certificates/urls
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.CertificateTemplateViewSet, basename='certificate-template')
router.register(r'courses-history', views.CoursesHistoryViewSet, basename='courses-history')
router.register(r'certificates', views.CertificateViewSet, basename='certificate')

urlpatterns = [
    path('', include(router.urls)),
    # Public API endpoints (no authentication required)
    path('request-public/', views.public_request_certificate, name='public-request-certificate'),
    path('verify-public/', views.public_verify_certificate, name='public-verify-certificate'),
    path('professors-public/', views.public_professors_list, name='public-professors-list'),
    path('templates-public/', views.public_templates_list, name='public-templates-list'),
    path('fields-public/', views.public_available_fields, name='public-available-fields'),
    path('api-info/', views.public_api_info, name='public-api-info'),
]
