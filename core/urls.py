from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, auth_views

router = DefaultRouter()
router.register(r'professors', views.ProfessorViewSet, basename='professor')
router.register(r'administrators', views.AdministratorViewSet, basename='administrator')
router.register(r'news', views.NewsViewSet, basename='news')
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'schedules', views.ScheduleViewSet, basename='schedule')
router.register(r'support-requests', views.SupportRequestViewSet, basename='support-request')
router.register(r'surveys', views.SurveyViewSet, basename='survey')

urlpatterns = [
    path('', include(router.urls)),
    path('test/', views.test_endpoint, name='test-endpoint'),
    # Authentication endpoints
    path('auth/login/', auth_views.login, name='login'),
    path('auth/register/', auth_views.register, name='register'),
    path('auth/logout/', auth_views.logout, name='logout'),
    path('auth/profile/', auth_views.get_profile, name='profile'),
]
