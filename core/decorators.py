# core/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

def user_type_required(user_types):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            if not hasattr(request.user, 'user_type') or request.user.user_type not in user_types:
                return Response({'error': 'User type not allowed'}, status=status.HTTP_403_FORBIDDEN)

            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator