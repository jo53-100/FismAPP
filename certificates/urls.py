from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.CertificateTemplateViewSet, basename='certificate-template')
router.register(r'courses-history', views.CoursesHistoryViewSet, basename='courses-history')
router.register(r'certificates|', views.CertificateViewSet, basename='certificate')

urlpatterns = [
    path('', include(router.urls)),
]