# certificates/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from core.models import CustomUser
from core.decorators import user_type_required
from .models import CertificateTemplate, GeneratedCertificate, CoursesHistory
from .serializers import (
    CertificateTemplateSerializer,
    GeneratedCertificateSerializer,
    CoursesHistorySerializer,
    GenerateCertificateSerializer,
    VerifyCertificateSerializer
)
from .services import CertificateService


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    queryset = CertificateTemplate.objects.all()
    serializer_class = CertificateTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class CoursesHistoryViewSet(viewsets.ModelViewSet):
    queryset = CoursesHistory.objects.all()
    serializer_class = CoursesHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by id_docente if provided
        id_docente = self.request.query_params.get('id_docente', None)
        if id_docente:
            queryset = queryset.filter(id_docente=id_docente)

        # Filter by profesor if provided
        profesor = self.request.query_params.get('profesor', None)
        if profesor:
            queryset = queryset.filter(profesor__icontains=profesor)

        return queryset

    @action(detail=False, methods=['post'])
    @user_type_required(['administrator'])
    def import_from_excel(self, request):
        """Import courses history from Excel file"""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        excel_file = request.FILES['file']

        try:
            import pandas as pd
            df = pd.read_excel(excel_file)

            # Validate required columns
            required_columns = ['ID_Docente', 'Profesor', 'Periodo', 'Materia', 'Clave', 'NRC', 'Fecha_Inicio',
                                'Fecha_Fin', 'Hr_Cont']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return Response({'error': f'Missing columns: {", ".join(missing_columns)}'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Import data
            imported_count = 0
            for _, row in df.iterrows():
                CoursesHistory.objects.update_or_create(
                    id_docente=row['ID_Docente'],
                    nrc=row['NRC'],
                    periodo=row['Periodo'],
                    defaults={
                        'profesor': row['Profesor'],
                        'materia': row['Materia'],
                        'clave': row['Clave'],
                        'fecha_inicio': row['Fecha_Inicio'],
                        'fecha_fin': row['Fecha_Fin'],
                        'hr_cont': row['Hr_Cont']
                    }
                )
                imported_count += 1

            return Response({'message': f'Successfully imported {imported_count} records'})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = GeneratedCertificate.objects.all()
    serializer_class = GenerateCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_administrator():
            return GeneratedCertificate.objects.all()
        elif user.is_professor():
            id_docente = self.get_id_docente(user)
            if id_docente:
                return GeneratedCertificate.objects.filter(metadata_id_docente=id_docente)
            return GeneratedCertificate.objects.filter(professor=user)
        return GeneratedCertificate.objects.none()

    def get_id_docente(self, user):
        """Get the professor's id_docente from their profile or course history"""
        # Try to get from professor profile first
        try:
            if hasattr(user, 'professorprofile') and user.professorprofile.id_docente:
                return user.professorprofile.id_docente
        except:
            pass

        # If not in profile, try to find in course history by name
        course = CoursesHistory.objects.filter(
            profesor__icontains=user.get_full_name()
        ).first()

        if course:
            return course.id_docente

        return None

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new certificate"""
        serializer = GenerateCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        id_docente = data.get('id_docente')

        if not id_docente:
            return Response({'error': 'id_docente is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify that courses exist for this id
        courses = CoursesHistory.objects.filter(id_docente=id_docente)
        if not courses.exists():
            return Response({'error': f'Courses not found for id {id_docente}'}, status=status.HTTP_404_NOT_FOUND)

        # Get professor name from course history
        professor_name = courses.first().profesor

        # Try to find matching user account
        professor_user = None
        try:
            name_parts = professor_name.split()
            if len(name_parts) >= 2:
                # Last name is always the last two words
                last_name = " ".join(name_parts[-2:])
                # First name is everything before the last two words
                first_name = " ".join(name_parts[:-2])

                professor_user = CustomUser.objects.filter(
                    first_name__icontains=first_name.strip(),
                    last_name__icontains=last_name.strip(),
                    user_type='professor'
                ).first()
        except:
            pass
            # If no user found, create a virtual professor object for certificate generation
        if not professor_user:
            # Create a simple object with the required methods
            class VirtualProfessor:
                def __init__(self, name):
                    self.full_name = name
                    self.username = id_docente

                def get_full_name(self):
                    return self.full_name

            professor_user = VirtualProfessor(professor_name)

            # Get or create default template
        template_id = data.get('template_id')
        if template_id:
            template = get_object_or_404(CertificateTemplate, id=template_id)
        else:
            template, _ = CertificateTemplate.objects.get_or_create(
                name="Default Template",
                defaults={
                    'description': "Default certificate template"
                }
            )

        try:
            # Add id_docente to options
            options = dict(data)
            options['id_docente'] = id_docente

            # Generate PDF
            pdf_content, verification_code = CertificateService.generate_pdf(
                professor=professor_user,
                template=template,
                options=options
            )

            # Save certificate record
            certificate = GeneratedCertificate.objects.create(
                professor=professor_user if hasattr(professor_user, 'id') else None,
                template=template,
                verification_code=verification_code,
                metadata=options
            )

            # Save PDF file
            filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
            certificate.file.save(filename, pdf_content)

            # Return certificate info
            return Response(
                GeneratedCertificateSerializer(certificate).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a certificate PDF"""
        certificate = self.get_object()

        if not certificate.file:
            return Response({'error': 'Certificate file not found'},
                            status=status.HTTP_404_NOT_FOUND)

        # Return file response
        response = FileResponse(certificate.file.open(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{certificate.file.name}"'
        return response

    @action(detail=False, methods=['post'])
    def verify(self, request):
        """Verify a certificate by its code"""
        serializer = VerifyCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        verification_code = serializer.validated_data['verification_code']

        try:
            certificate = GeneratedCertificate.objects.get(verification_code=verification_code)
            return Response({
                'valid': True,
                'certificate': GeneratedCertificateSerializer(certificate).data
            })
        except GeneratedCertificate.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Certificate not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def professors_list(self, request):
        """Get list of available professors from course history"""
        professors = CoursesHistory.objects.values('id_docente', 'profesor').distinct().order_by('profesor')

        professor_list = []
        for prof in professors:
            professor_list.append({
                'id_docente': prof['id_docente'],
                'name': prof['profesor']
            })

        return Response(professor_list)

    @action(detail=False, methods=['post'])
    @user_type_required(['administrator'])
    def bulk_generate(self, request):
        """Generate certificates for multiple professors"""
        id_docentes = request.data.get('id_docentes', [])
        if not id_docentes:
            return Response({'error': 'No professor IDs provided'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Get template
        template_id = request.data.get('template_id')
        if template_id:
            template = get_object_or_404(CertificateTemplate, id=template_id)
        else:
            template, _ = CertificateTemplate.objects.get_or_create(
                name="Default Template",
                defaults={
                    'description': "Default certificate template"
                }
            )

        # Common options
        options = {
            'destinatario': request.data.get('destinatario', 'A QUIEN CORRESPONDA'),
            'incluir_qr': request.data.get('incluir_qr', True),
            'url_verificacion': request.data.get('url_verificacion'),
            'periodos_filtro': request.data.get('periodos_filtro'),
            'periodo_actual': request.data.get('periodo_actual'),
            'campos': request.data.get('campos',
                                       ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'])
        }

        generated_certificates = []
        errors = []

        for id_docente in id_docentes:
            try:
                # Get professor info from course history
                courses = CoursesHistory.objects.filter(id_docente=id_docente)
                if not courses.exists():
                    errors.append({
                        'id_docente': id_docente,
                        'error': 'No course history found'
                    })
                    continue

                professor_name = courses.first().profesor

                # Create virtual professor
                class VirtualProfessor:
                    def __init__(self, name, docente_id):
                        self.full_name = name
                        self.username = docente_id

                    def get_full_name(self):
                        return self.full_name

                professor = VirtualProfessor(professor_name, id_docente)

                # Add id_docente to options
                current_options = dict(options)
                current_options['id_docente'] = id_docente

                # Generate PDF
                pdf_content, verification_code = CertificateService.generate_pdf(
                    professor=professor,
                    template=template,
                    options=current_options
                )

                # Save certificate record
                certificate = GeneratedCertificate.objects.create(
                    professor=None,  # No user account required
                    template=template,
                    verification_code=verification_code,
                    metadata=current_options
                )

                # Save PDF file
                filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
                certificate.file.save(filename, pdf_content)

                generated_certificates.append(certificate)

            except Exception as e:
                errors.append({
                    'id_docente': id_docente,
                    'error': str(e)
                })

        return Response({
            'generated': len(generated_certificates),
            'errors': errors,
            'certificates': GeneratedCertificateSerializer(generated_certificates, many=True).data
        }, status=status.HTTP_201_CREATED)
