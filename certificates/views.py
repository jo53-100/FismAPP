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
    serializer_class = GeneratedCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_administrator():
            return GeneratedCertificate.objects.all()
        elif user.is_professor():
            return GeneratedCertificate.objects.filter(professor=user)
        return GeneratedCertificate.objects.none()

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new certificate"""
        serializer = GenerateCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Get professor
        if request.user.is_professor():
            professor = request.user
        else:
            professor_id = request.data.get('professor_id')
            if not professor_id:
                return Response({'error': 'Professor ID is required'},
                                status=status.HTTP_400_BAD_REQUEST)
            professor = get_object_or_404(CustomUser, id=professor_id, user_type='professor')

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
            # Generate PDF
            pdf_content, verification_code = CertificateService.generate_pdf(
                professor=professor,
                template=template,
                options=data
            )

            # Save certificate record
            certificate = GeneratedCertificate.objects.create(
                professor=professor,
                template=template,
                verification_code=verification_code,
                metadata=data
            )

            # Save PDF file
            filename = f"certificate_{professor.username}_{verification_code[:8]}.pdf"
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

    @action(detail=False, methods=['post'])
    @user_type_required(['administrator'])
    def bulk_generate(self, request):
        """Generate certificates for multiple professors"""
        professor_ids = request.data.get('professor_ids', [])
        if not professor_ids:
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
            'campos': request.data.get('campos', ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'])
        }

        generated_certificates = []
        errors = []

        for professor_id in professor_ids:
            try:
                professor = CustomUser.objects.get(id=professor_id, user_type='professor')

                # Generate PDF
                pdf_content, verification_code = CertificateService.generate_pdf(
                    professor=professor,
                    template=template,
                    options=options
                )

                # Save certificate record
                certificate = GeneratedCertificate.objects.create(
                    professor=professor,
                    template=template,
                    verification_code=verification_code,
                    metadata=options
                )

                # Save PDF file
                filename = f"certificate_{professor.username}_{verification_code[:8]}.pdf"
                certificate.file.save(filename, pdf_content)

                generated_certificates.append(certificate)

            except Exception as e:
                errors.append({
                    'professor_id': professor_id,
                    'error': str(e)
                })

        return Response({
            'generated': len(generated_certificates),
            'errors': errors,
            'certificates': GeneratedCertificateSerializer(generated_certificates, many=True).data
        }, status=status.HTTP_201_CREATED)
