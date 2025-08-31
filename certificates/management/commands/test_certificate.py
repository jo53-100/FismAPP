from django.core.management.base import BaseCommand
from django.conf import settings
from certificates.models import CertificateTemplate, CoursesHistory
from certificates.services import CertificateService
import os


class Command(BaseCommand):
    help = 'Test certificate generation with different templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id_docente',
            type=str,
            help='ID docente to test with',
        )
        parser.add_argument(
            '--template_id',
            type=int,
            help='Template ID to use',
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Certificate Generation System...")
        
        # Get or create a test template
        if options['template_id']:
            try:
                template = CertificateTemplate.objects.get(id=options['template_id'])
                self.stdout.write(f"✅ Using existing template: {template.name}")
            except CertificateTemplate.DoesNotExist:
                self.stdout.write(f"❌ Template with ID {options['template_id']} not found")
                return
        else:
            # Create a test template
            template, created = CertificateTemplate.objects.get_or_create(
                name="Test Template",
                defaults={
                    'description': 'Template for testing',
                    'layout_type': 'background_pdf',
                    'is_default': True
                }
            )
            if created:
                self.stdout.write(f"✅ Created test template: {template.name}")
            else:
                self.stdout.write(f"✅ Using existing test template: {template.name}")

        # Get test data
        if options['id_docente']:
            id_docente = options['id_docente']
        else:
            # Get first available professor
            course = CoursesHistory.objects.first()
            if not course:
                self.stdout.write("❌ No course data available. Please import data first.")
                return
            id_docente = course.id_docente

        self.stdout.write(f"👨‍🏫 Testing with ID docente: {id_docente}")

        # Get courses for this professor
        courses = CoursesHistory.objects.filter(id_docente=id_docente)
        if not courses.exists():
            self.stdout.write(f"❌ No courses found for ID docente: {id_docente}")
            return

        professor_name = courses.first().profesor
        self.stdout.write(f"📚 Found {courses.count()} courses for {professor_name}")

        # Test options
        test_options = {
            'id_docente': id_docente,
            'destinatario': 'A QUIEN CORRESPONDA (TEST)',
            'incluir_qr': True,
            'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
        }

        # Test different generation methods
        self.stdout.write("\n🔍 Testing different generation methods...")

        # Test 1: Background PDF method
        if template.layout_type == 'background_pdf':
            self.stdout.write("📄 Testing Background PDF generation...")
            try:
                pdf_content, verification_code = CertificateService.generate_pdf(
                    id_docente=id_docente,
                    courses=courses,
                    template=template,
                    options=test_options
                )
                self.stdout.write(f"✅ Background PDF generated successfully!")
                self.stdout.write(f"   Verification code: {verification_code[:8]}...")
                self.stdout.write(f"   PDF size: {len(pdf_content.read())} bytes")
                pdf_content.seek(0)
            except Exception as e:
                self.stdout.write(f"❌ Background PDF generation failed: {e}")

        # Test 2: HTML method
        self.stdout.write("\n🌐 Testing HTML generation...")
        try:
            # Create a copy of the template for HTML testing
            html_template = CertificateTemplate.objects.create(
                name=f"{template.name} (HTML Copy)",
                description=template.description,
                layout_type='default',
                department_name=template.department_name,
                university_name=template.university_name,
                address=template.address,
                title_text=template.title_text,
                recipient_line=template.recipient_line,
                intro_text=template.intro_text,
                courses_intro=template.courses_intro,
                closing_text=template.closing_text,
                secretary_name=template.secretary_name,
                secretary_title=template.secretary_title,
                primary_color=template.primary_color,
                secondary_color=template.secondary_color,
                font_family=template.font_family,
                is_default=False
            )
            
            pdf_content, verification_code = CertificateService.generate_pdf(
                id_docente=id_docente,
                courses=courses,
                template=html_template,
                options=test_options
            )
            self.stdout.write(f"✅ HTML PDF generated successfully!")
            self.stdout.write(f"   Verification code: {verification_code[:8]}...")
            self.stdout.write(f"   PDF size: {len(pdf_content.read())} bytes")
            pdf_content.seek(0)
            
            # Clean up the temporary template
            html_template.delete()
            
        except Exception as e:
            self.stdout.write(f"❌ HTML PDF generation failed: {e}")

        # Test 3: ReportLab fallback
        self.stdout.write("\n📊 Testing ReportLab fallback...")
        try:
            pdf_content, verification_code = CertificateService.generate_pdf_reportlab(
                id_docente=id_docente,
                courses=courses,
                template=template,
                options=test_options
            )
            self.stdout.write(f"✅ ReportLab PDF generated successfully!")
            self.stdout.write(f"   Verification code: {verification_code[:8]}...")
            self.stdout.write(f"   PDF size: {len(pdf_content.read())} bytes")
        except Exception as e:
            self.stdout.write(f"❌ ReportLab PDF generation failed: {e}")

        # Check background PDF availability
        background_pdf_paths = [
            os.path.join(settings.MEDIA_ROOT, 'Hoja membretada.pdf'),
            os.path.join(settings.MEDIA_ROOT, 'certificate_pdf_templates', 'Hoja membretada.pdf'),
            os.path.join(settings.MEDIA_ROOT, 'certificate_pdf_templates', 'Hoja_membretada.pdf'),
        ]
        
        background_found = False
        for path in background_pdf_paths:
            if os.path.exists(path):
                self.stdout.write(f"\n✅ Background PDF found: {path}")
                self.stdout.write(f"   Size: {os.path.getsize(path)} bytes")
                background_found = True
                break
        
        if not background_found:
            self.stdout.write(f"\n⚠️  Background PDF not found in any of these locations:")
            for path in background_pdf_paths:
                self.stdout.write(f"   - {path}")
            self.stdout.write("   Please ensure 'Hoja membretada.pdf' is available")

        # Summary
        self.stdout.write("\n🎯 Test Summary:")
        self.stdout.write(f"   Template: {template.name} ({template.layout_type})")
        self.stdout.write(f"   Professor: {professor_name}")
        self.stdout.write(f"   Courses: {courses.count()}")
        self.stdout.write(f"   ID Docente: {id_docente}")
        
        self.stdout.write("\n✅ Certificate generation system test completed!")
