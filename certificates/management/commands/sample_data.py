# Esto crea datos de prueba
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import CustomUser, News, Event, Schedule, SupportRequest


class Command(BaseCommand):
    help = 'Create sample data for the application'

    def handle(self, *args, **options):
        # Get users
        admin = CustomUser.objects.filter(user_type='administrator').first()
        professor = CustomUser.objects.filter(user_type='professor').first()

        if not admin or not professor:
            self.stdout.write(self.style.ERROR('Please create test users first'))
            return

        # Create news items
        news_items = [
            {
                'title': 'Inscripciones abiertas para el semestre Otoño 2025',
                'content': 'Las inscripciones para el semestre Otoño 2025 estarán abiertas del 15 al 30 de julio. Por favor, revise los requisitos y horarios disponibles.',
                'category': 'academic',
                'published': True,
                'published_date': timezone.now()
            },
            {
                'title': 'Conferencia sobre Física Cuántica',
                'content': 'El Dr. Stephen Hawking Jr. ofrecerá una conferencia sobre los últimos avances en física cuántica el próximo 15 de mayo en el auditorio principal.',
                'category': 'events',
                'published': True,
                'published_date': timezone.now()
            }
        ]

        for news_data in news_items:
            News.objects.create(author=admin, **news_data)

        # Create events
        events = [
            {
                'title': 'Semana de la Ciencia 2025',
                'description': 'Una semana llena de actividades científicas, talleres y conferencias para toda la comunidad universitaria.',
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=37),
                'location': 'Campus Universitario',
                'event_type': 'conference',
                'registration_required': True,
                'max_participants': 500
            },
            {
                'title': 'Torneo de Ajedrez FCFM',
                'description': 'Torneo anual de ajedrez para estudiantes y profesores de la facultad.',
                'start_date': timezone.now() + timedelta(days=15),
                'end_date': timezone.now() + timedelta(days=15),
                'location': 'Sala de Usos Múltiples',
                'event_type': 'sports',
                'registration_required': True,
                'max_participants': 64
            }
        ]

        for event_data in events:
            Event.objects.create(organizer=admin, **event_data)

        # Create schedules
        schedules = [
            {
                'course_name': 'Física I',
                'course_code': 'FIS101',
                'day_of_week': 'monday',
                'start_time': '08:00:00',
                'end_time': '10:00:00',
                'classroom': 'Aula 101',
                'semester': 'Otoño 2025'
            },
            {
                'course_name': 'Cálculo Diferencial',
                'course_code': 'MAT201',
                'day_of_week': 'wednesday',
                'start_time': '10:00:00',
                'end_time': '12:00:00',
                'classroom': 'Aula 203',
                'semester': 'Otoño 2025'
            }
        ]

        for schedule_data in schedules:
            Schedule.objects.create(professor=professor, **schedule_data)

        # Create support requests
        student = CustomUser.objects.filter(user_type='student').first()
        if student:
            SupportRequest.objects.create(
                requester=student,
                title='Problema con acceso al laboratorio',
                description='No puedo acceder al laboratorio de física con mi credencial estudiantil.',
                category='facilities',
                priority='medium'
            )

        self.stdout.write(self.style.SUCCESS('Sample data created successfully'))