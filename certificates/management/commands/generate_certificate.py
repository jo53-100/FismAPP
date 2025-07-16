from django.core.management.base import BaseCommand
from certificates.models import CoursesHistory, CertificateTemplate
from certificates.services import CertificateService


class Command(BaseCommand):
    help = 'Generate certificate for a professor by ID'

    def add_arguments(self, parser):
        parser.add_argument('id_docente', type=str, help='Professor ID')
        parser.add_argument('--destinatario', type=str, default='A QUIEN CORRESPONDA')
        parser.add_argument('--template', type=int, help='Template ID')

    def handle(self, *args, **options):
        id_docente = options['id_docente']

        # Find courses
        courses = CoursesHistory.objects.filter(id_docente=id_docente)
        if not courses.exists():
            self.stdout.write(
                self.style.ERROR(f'No courses found for professor ID: {id_docente}')
            )
            return

        professor_name = courses.first().profesor

        # Get template
        template_id = options.get('template')
        if template_id:
            template = CertificateTemplate.objects.get(id=template_id)
        else:
            template = CertificateTemplate.objects.filter(is_default=True).first()

        # Generate
        options_dict = {
            'id_docente': id_docente,
            'destinatario': options['destinatario'],
            'incluir_qr': True,
            'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
        }

        pdf_content, verification_code = CertificateService.generate_pdf(
            id_docente=id_docente,
            courses=courses,
            template=template,
            options=options_dict
        )

        # Save to file
        filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_content.read())

        self.stdout.write(
            self.style.SUCCESS(f'Certificate generated: {filename} for {professor_name}')
        )