# Esto crea usuarios de prueba
from django.core.management.base import BaseCommand
from core.models import CustomUser, ProfessorProfile, AdministratorProfile, StudentProfile


class Command(BaseCommand):
    help = 'Create test users for the application'

    def handle(self, *args, **options):
        # Create admin user
        admin, created = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@fcfm.mx',
                'user_type': 'administrator',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            AdministratorProfile.objects.create(
                user=admin,
                administrative_role='System Administrator',
                office_location='Main Office'
            )
            self.stdout.write(self.style.SUCCESS('Admin user created'))

        # Create professor user
        professor, created = CustomUser.objects.get_or_create(
            username='professor1',
            defaults={
                'email': 'professor1@fcfm.mx',
                'user_type': 'professor',
                'first_name': 'Juan',
                'last_name': 'Pérez'
            }
        )
        if created:
            professor.set_password('prof123')
            professor.save()
            ProfessorProfile.objects.create(
                user=professor,
                department='Physics',
                office_number='FM-201',
                research_areas='Quantum Physics, Optics'
            )
            self.stdout.write(self.style.SUCCESS('Professor user created'))

        # Create student user
        student, created = CustomUser.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student1@fcfm.mx',
                'user_type': 'student',
                'first_name': 'María',
                'last_name': 'González'
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            StudentProfile.objects.create(
                user=student,
                student_id='201900123',
                enrollment_year=2019,
                major='Applied Physics',
                semester=6
            )
            self.stdout.write(self.style.SUCCESS('Student user created'))

        self.stdout.write(self.style.SUCCESS('Test users created successfully'))
        