from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views

router = DefaultRouter()
router.register(r'professors',         views.ProfessorViewSet,        basename='professor')
router.register(r'administrators',     views.AdministratorViewSet,    basename='administrator')
router.register(r'news',               views.NewsViewSet,             basename='news')
router.register(r'events',             views.EventViewSet,            basename='event')
router.register(r'schedules',          views.ScheduleViewSet,         basename='schedule')
router.register(r'support-requests',   views.SupportRequestViewSet,   basename='support-request')
router.register(r'surveys',            views.SurveyViewSet,           basename='survey')

urlpatterns = [

    path('', include(router.urls)),

    path('test/', views.test_endpoint, name='test-endpoint'),

    path('auth/login/',     auth_views.login,        name='login'),
    path('auth/register/',  auth_views.register,     name='register'),
    path('auth/logout/',    auth_views.logout,       name='logout'),
    path('auth/profile/',   auth_views.get_profile,  name='profile'),
]

#Configuración del esquema Swagger, Documentación Swagger y Redoc
!pip install drf-yasg

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="FismAPP API",
        default_version='v1',
        description="Documentación interactiva de la API",
        contact=openapi.Contact(email="soporte@tu-facultad.edu"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

#Para evitar romper la compativilidad
urlpatterns = [
    path('api/v1/', include(router.urls)),
]

#Manejo de errores
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'

def error_404(request, exception):
    return JsonResponse({'error': 'No encontrado'}, status=404)

def error_500(request):
    return JsonResponse({'error': 'Error interno del servidor'}, status=500)

#Archivos estáticos
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
