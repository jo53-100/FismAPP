from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView


def home(request):
    return JsonResponse({
        'message': 'Faculty App API',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/',
            'api-auth': '/api-auth/',
            'certificates': '/api/certificates/'
        },
        'web_interface': {
            'main': '/certificates/',
            'request': '/certificates/request/',
            'verify': '/certificates/verify/'
        }
    })


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/certificates/', include('certificates.urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # Web interface routes
    path('certificates/', TemplateView.as_view(template_name='static/index.html'), name='certificates-home'),
    path('certificates/request/', TemplateView.as_view(template_name='static/certificate_request.html'), name='certificate-request'),
    path('certificates/verify/', TemplateView.as_view(template_name='static/verify_certificate.html'), name='certificate-verify'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)