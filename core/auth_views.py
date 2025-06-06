#Login de usuario
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    User login endpoint
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Por favor proporciona nombre de usuario y contraseña.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'error': 'Credenciales inválidas.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': UserSerializer(user).data
    })


#Registro de usuario
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    User registration endpoint
    """
    password = request.data.get('password')

    if not password or len(password) < 6:
        return Response(
            {'error': 'La contraseña debe tener al menos 6 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = CustomUser.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=password,
            user_type=serializer.validated_data.get('user_type', 'student'),
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', '')
        )

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Obtener perfil de usuario autenticado
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Get current user profile (requires authentication)
    """
    return Response(UserSerializer(request.user).data)

#Logout seguro
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint (deletes user's auth token)
    """
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    return Response({'message': 'Sesión cerrada exitosamente'})

