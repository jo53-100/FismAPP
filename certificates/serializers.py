#User serializer
from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'user_type', 'first_name', 'last_name')
        read_only_fields = ('id',)

    def validate_email(self, value):
        if "@" not in value:
            raise serializers.ValidationError("El correo electrónico no es válido.")
        return value

#Professor Profile Serializer
from .models import ProfessorProfile

class ProfessorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProfessorProfile
        fields = ('id', 'user', 'department', 'office_location', 'phone_number')
        read_only_fields = ('id',)

#Student Profile Serializer
from .models import StudentProfile

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = ('id', 'user', 'enrollment_number', 'major')
        read_only_fields = ('id',)

#News Serializer
from .models import News

class NewsSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = News
        fields = ('id', 'title', 'content', 'author_name', 'created_at', 'updated_at')
        read_only_fields = ('author',)

#Event Serializer
from .models import Schedule

class ScheduleSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.get_full_name', read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'professor_name', 'course_name', 'schedule_time')

#Schedule Serializer
from .models import Schedule

class ScheduleSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.get_full_name', read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'professor_name', 'course_name', 'schedule_time')

#Support Request Serializer
from .models import SupportRequest

class SupportRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = SupportRequest
        fields = ('id', 'requester_name', 'assigned_to_name', 'request_details', 'created_at', 'updated_at')
        read_only_fields = ('requester', 'created_at', 'updated_at')

#Survey Option Serializer
from .models import SurveyOption

class SurveyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOption
        fields = ('id', 'option_text', 'question')

#Survey Question Serializer
from .models import SurveyQuestion

class SurveyQuestionSerializer(serializers.ModelSerializer):
    options = SurveyOptionSerializer(many=True, read_only=True)

    class Meta:
        model = SurveyQuestion
        fields = ('id', 'question_text', 'survey', 'options')

#Survey Serializer
# serializers.py
from .models import Survey

class SurveySerializer(serializers.ModelSerializer):
    questions = SurveyQuestionSerializer(many=True, read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)

    class Meta:
        model = Survey
        fields = ('id', 'title', 'description', 'creator_name', 'questions')  # Filtrando los campos clave
        read_only_fields = ('creator',)

#Survey Response Serializer
from .models import SurveyResponse

class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = ('id', 'respondent', 'survey', 'response_data', 'submitted_at')  # Campos relevantes
        read_only_fields = ('respondent', 'submitted_at')
