# core/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import (
    CustomUser, News, Event, Schedule,
    SupportRequest, Survey, SurveyQuestion,
    SurveyOption, SurveyResponse
)
from .serializers import (
    UserSerializer, NewsSerializer, EventSerializer,
    ScheduleSerializer, SupportRequestSerializer,
    SurveySerializer, SurveyQuestionSerializer,
    SurveyOptionSerializer, SurveyResponseSerializer
)
from .decorators import user_type_required
from .tasks import execute_script


@api_view(['GET'])
def test_endpoint(request):
    return Response({'message': 'Test endpoint working!'})


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_administrator()


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.filter(published=True)
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = News.objects.all()
        if self.request.user.is_authenticated and self.request.user.is_administrator():
            return queryset
        return queryset.filter(published=True)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    @user_type_required(['administrator'])
    def publish(self, request, pk=None):
        news = self.get_object()
        news.publish()
        return Response({'status': 'news published'})


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        upcoming_events = Event.objects.filter(start_date__gte=timezone.now())
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'student':
            # Filter schedules based on student's enrollment
            return Schedule.objects.all()  # You might want to filter by student's courses
        elif user.user_type == 'professor':
            return Schedule.objects.filter(professor=user)
        return Schedule.objects.all()


class SupportRequestViewSet(viewsets.ModelViewSet):
    queryset = SupportRequest.objects.all()
    serializer_class = SupportRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_administrator():
            return SupportRequest.objects.all()
        return SupportRequest.objects.filter(requester=user)

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=['post'])
    @user_type_required(['administrator'])
    def assign(self, request, pk=None):
        support_request = self.get_object()
        admin_id = request.data.get('admin_id')

        try:
            admin = CustomUser.objects.get(id=admin_id, user_type='administrator')
            support_request.assigned_to = admin
            support_request.status = 'in_progress'
            support_request.save()
            return Response({'status': 'request assigned'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    @user_type_required(['administrator'])
    def resolve(self, request, pk=None):
        support_request = self.get_object()
        support_request.status = 'resolved'
        support_request.resolved_at = timezone.now()
        support_request.save()
        return Response({'status': 'request resolved'})


class SurveyViewSet(viewsets.ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Survey.objects.filter(is_active=True)

        # Filter by target audience
        return queryset.filter(
            target_audience__in=[user.user_type, 'all']
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def submit_response(self, request, pk=None):
        survey = self.get_object()

        # Check if user already responded
        if SurveyResponse.objects.filter(survey=survey, respondent=request.user).exists():
            return Response({'error': 'You have already responded to this survey'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create response
        response_data = {
            'survey': survey.id,
            'respondent': request.user.id
        }

        serializer = SurveyResponseSerializer(data=response_data)
        if serializer.is_valid():
            serializer.save(respondent=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessorViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(user_type='professor')

    @action(detail=False, methods=['post'])
    @user_type_required(['professor', 'administrator'])
    def run_grade_analysis(self, request):
        """Run grade analysis script"""
        task = execute_script.delay('generate_report', ['grades'])
        return Response({'task_id': task.id})


class AdministratorViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(user_type='administrator')

    @action(detail=False, methods=['post'])
    @user_type_required(['administrator'])
    def generate_statistics(self, request):
        """Generate faculty statistics"""
        task = execute_script.delay('process_data', ['statistics'])
        return Response({'task_id': task.id})
