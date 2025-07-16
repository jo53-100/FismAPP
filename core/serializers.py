# core/serializers
from rest_framework import serializers
from .models import (
    CustomUser, ProfessorProfile, AdministratorProfile,
    AlumniProfile, StudentProfile, News, Event,
    Schedule, SupportRequest, Survey, SurveyQuestion,
    SurveyOption, SurveyResponse
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'user_type', 'first_name', 'last_name')
        read_only_fields = ('id',)


class ProfessorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProfessorProfile
        fields = '__all__'


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = News
        fields = '__all__'
        read_only_fields = ('author',)


class EventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('organizer',)


class ScheduleSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.get_full_name', read_only=True)

    class Meta:
        model = Schedule
        fields = '__all__'


class SupportRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = SupportRequest
        fields = '__all__'
        read_only_fields = ('requester', 'created_at', 'updated_at')


class SurveyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOption
        fields = '__all__'


class SurveyQuestionSerializer(serializers.ModelSerializer):
    options = SurveyOptionSerializer(many=True, read_only=True)

    class Meta:
        model = SurveyQuestion
        fields = '__all__'


class SurveySerializer(serializers.ModelSerializer):
    questions = SurveyQuestionSerializer(many=True, read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)

    class Meta:
        model = Survey
        fields = '__all__'
        read_only_fields = ('creator',)


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = '__all__'
        read_only_fields = ('respondent', 'submitted_at')
