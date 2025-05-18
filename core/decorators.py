import logging
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

def user_type_required(user_types, redirect_to_error_page=False):
    """
    Decorador para verificar el tipo de usuario antes de permitir acceso a la vista.
    :param user_types: Lista de tipos de usuario permitidos.
    :param redirect_to_error_page: Si es True, redirige a una página de error en lugar de lanzar un PermissionDenied.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.user_type not in user_types:
                logger.warning(f"Usuario {request.user.username} intentó acceder a una vista restringida.")

                if redirect_to_error_page:
                    return redirect('error_page')
                else:
                    raise PermissionDenied("No tienes permiso para acceder a esta vista.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

#Uso de vistas basadas en funciónes
from django.shortcuts import render
from .decorators import user_type_required

@user_type_required(user_types=['admin', 'professor'], redirect_to_error_page=True)
def professor_dashboard(request):
    return render(request, 'professor_dashboard.html')

#Uso en vistas basadas en clase
from django.utils.decorators import method_decorator
from django.views.generic import View
from .decorators import user_type_required

class ProfessorDashboardView(View):
    @method_decorator(user_type_required(user_types=['admin', 'professor'], redirect_to_error_page=True))
    def get(self, request, *args, **kwargs):
        return render(request, 'professor_dashboard.html')

#REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from .decorators import user_type_required

class ProfessorView(APIView):
    @user_type_required(user_types=['admin', 'professor'], redirect_to_error_page=True)
    def get(self, request, *args, **kwargs):
        return Response({"message": "Este es el perfil del profesor."})

from rest_framework import viewsets
from .models import Professor
from .serializers import ProfessorSerializer
from .decorators import user_type_required

class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer

    @user_type_required(user_types=['admin', 'professor'], redirect_to_error_page=True)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
