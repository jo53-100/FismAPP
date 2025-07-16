# certificates/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.db import models, transaction
from django.http import FileResponse
import pandas as pd
import logging
from core.decorators import user_type_required
from .models import CertificateTemplate, GeneratedCertificate, CoursesHistory
from .serializers import (
    CertificateTemplateSerializer,
    GeneratedCertificateSerializer,
    CoursesHistorySerializer,
    GenerateCertificateSerializer,
    VerifyCertificateSerializer,
    QuickGenerateSerializer,
    BulkGenerateSerializer
)
from .services import CertificateService

# Set up logging
logger = logging.getLogger(__name__)


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

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    @user_type_required(['administrator'])
    def import_from_excel(self, request):
        """Enhanced Excel/CSV import specifically for Historia PA format"""

        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']

        # Validate file type - support both Excel and CSV
        if not uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
            return Response({'error': 'File must be Excel (.xlsx, .xls) or CSV (.csv)'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read file based on type
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            else:
                df = pd.read_excel(uploaded_file, sheet_name=0)

            # Clean column names - remove spaces and normalize
            df.columns = df.columns.str.strip()

            # Exact mapping for Historia PA.csv format
            column_mapping = {
                # Core required fields (map to your existing model fields)
                'ID_Docente': 'id_docente',
                'Profesor': 'profesor',
                'Periodo': 'periodo',
                'Materia': 'materia',
                'Clave': 'clave',
                'NRC': 'nrc',
                'Fecha_Inicio': 'fecha_inicio',
                'Fecha_Fin': 'fecha_fin',
                'Hr_Cont': 'hr_cont',
                'Listas_cruzadas': 'listas_cruzadas',

                # Additional fields from Historia PA.csv
                'Source.Name': 'source_name',
                'PP': 'pp',
                'Nivel': 'nivel',
                'UA': 'ua',
                'Claves_Programas': 'claves_programas',
                'Secc': 'secc',
                'Campus': 'campus',
                'Tipo_Hr': 'tipo_hr',
                'Cred': 'cred',
                'Modo_calif': 'modo_calif',
                'Hr_Semana': 'hr_semana',
                'Dias': 'dias',
                'Hora': 'hora',
                'Metodo_Asistencia': 'metodo_asistencia',
                'Salon': 'salon',
                'Ubicacion': 'ubicacion',
                'Edo': 'edo',
                'Cupo': 'cupo',
                'Insc': 'insc',
                'Disp': 'disp',
                'Ligas': 'ligas',
                'Bloque': 'bloque'
            }

            # Check which columns are available
            available_columns = list(df.columns)
            mapped_fields = {}

            for csv_col, model_field in column_mapping.items():
                if csv_col in available_columns:
                    mapped_fields[model_field] = csv_col

            # Required fields for basic functionality
            required_fields = ['id_docente', 'profesor', 'periodo', 'materia', 'clave', 'nrc',
                               'fecha_inicio', 'fecha_fin', 'hr_cont']

            missing_required = [field for field in required_fields if field not in mapped_fields]

            if missing_required:
                return Response({
                    'error': f'Missing required columns: {missing_required}',
                    'available_columns': available_columns,
                    'expected_columns': list(column_mapping.keys())
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Processing {len(df)} rows from Historia PA file")

            # Data validation and import
            imported_count = 0
            updated_count = 0
            errors = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Prepare data for the model
                        course_data = {}

                        for model_field, csv_column in mapped_fields.items():
                            value = row[csv_column]

                            # Handle different data types
                            if model_field in ['fecha_inicio', 'fecha_fin']:
                                # Handle date conversion
                                if pd.isna(value):
                                    raise ValueError(f"Missing date in {model_field}")
                                date_val = pd.to_datetime(value, errors='coerce')
                                if pd.isna(date_val):
                                    raise ValueError(f"Invalid date format in {model_field}: {value}")
                                course_data[model_field] = date_val.date()

                            elif model_field in ['hr_cont', 'cred', 'cupo', 'insc', 'disp']:
                                # Handle integer fields
                                if pd.isna(value):
                                    if model_field == 'hr_cont':  # Required field
                                        raise ValueError(f"Missing required field: {model_field}")
                                    course_data[model_field] = None
                                else:
                                    try:
                                        course_data[model_field] = int(float(value))
                                    except (ValueError, TypeError):
                                        if model_field == 'hr_cont':
                                            raise ValueError(f"Invalid number format in {model_field}: {value}")
                                        course_data[model_field] = None

                            elif model_field in ['hr_semana']:
                                # Handle float fields
                                if pd.isna(value):
                                    course_data[model_field] = None
                                else:
                                    try:
                                        course_data[model_field] = float(value)
                                    except (ValueError, TypeError):
                                        course_data[model_field] = None

                            else:
                                # Handle text fields
                                if pd.isna(value):
                                    course_data[model_field] = None
                                else:
                                    # Convert to string and clean
                                    str_value = str(value).strip()
                                    course_data[model_field] = str_value if str_value else None

                        # Validate required fields have values
                        for req_field in required_fields:
                            if req_field in course_data and course_data[req_field] is None:
                                raise ValueError(f"Missing required field: {req_field}")

                        # Create or update record
                        course, created = CoursesHistory.objects.update_or_create(
                            id_docente=course_data['id_docente'],
                            nrc=course_data['nrc'],
                            periodo=course_data['periodo'],
                            defaults=course_data
                        )

                        if created:
                            imported_count += 1
                        else:
                            updated_count += 1

                    except Exception as e:
                        error_msg = f"Row {index + 2}: {str(e)}"
                        errors.append(error_msg)
                        if len(errors) < 10:  # Log first 10 errors in detail
                            logger.error(error_msg)

            # Prepare response
            response_data = {
                'message': 'Import completed',
                'total_processed': len(df),
                'imported': imported_count,
                'updated': updated_count,
                'errors_count': len(errors),
                'success_rate': f"{((imported_count + updated_count) / len(df) * 100):.1f}%"
            }

            if errors:
                response_data['errors'] = errors[:10]  # Return first 10 errors
                response_data['warning'] = f'Import completed with {len(errors)} errors'
                if len(errors) > 10:
                    response_data['additional_errors'] = f'{len(errors) - 10} more errors not shown'

            logger.info(f"Import completed: {imported_count} new, {updated_count} updated, {len(errors)} errors")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return Response({'error': f'Import failed: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = GeneratedCertificate.objects.all()
    serializer_class = GeneratedCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_administrator():
            return GeneratedCertificate.objects.all()
        elif user.is_professor():
            id_docente = self.get_id_docente(user)
            if id_docente:
                return GeneratedCertificate.objects.filter(metadata__id_docente=id_docente)
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
        """Generate a new certificate using only id_docente"""
        serializer = GenerateCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        id_docente = data.get('id_docente')

        # Get courses for this professor
        courses = CoursesHistory.objects.filter(id_docente=id_docente)
        if not courses.exists():
            return Response({
                'error': f'No se encontraron cursos para el ID docente: {id_docente}'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get professor name from course history
        professor_name = courses.first().profesor

        # Get template
        template_id = data.get('template_id')
        if template_id:
            try:
                template = CertificateTemplate.objects.get(id=template_id)
            except CertificateTemplate.DoesNotExist:
                return Response({
                    'error': f'Template con ID {template_id} no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            template = CertificateTemplate.objects.filter(is_default=True).first()
            if not template:
                template = CertificateTemplate.objects.first()
            if not template:
                return Response({
                    'error': 'No hay plantillas de certificado disponibles'
                }, status=status.HTTP_404_NOT_FOUND)

        try:
            # Prepare options for PDF generation
            options = {
                'id_docente': id_docente,
                'destinatario': data.get('destinatario', 'A QUIEN CORRESPONDA'),
                'periodos_filtro': data.get('periodos_filtro'),
                'periodo_actual': data.get('periodo_actual'),
                'incluir_qr': data.get('incluir_qr', True),
                'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
            }

            # Generate PDF using the service method
            pdf_content, verification_code = CertificateService.generate_pdf(
                id_docente=id_docente,
                courses=courses,
                template=template,
                options=options
            )

            # Save certificate record (no professor user required)
            certificate = GeneratedCertificate.objects.create(
                professor=None,  # No user account required
                template=template,
                verification_code=verification_code,
                metadata={
                    **options,
                    'professor_name': professor_name
                }
            )

            # Save PDF file
            filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
            certificate.file.save(filename, pdf_content)

            # Return certificate info
            return Response({
                'id': certificate.id,
                'verification_code': verification_code,
                'professor_name': professor_name,
                'id_docente': id_docente,
                'template_name': template.name,
                'file_url': certificate.file.url if certificate.file else None,
                'generated_at': certificate.generated_at,
                'message': f'Certificado generado exitosamente para {professor_name}'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'Error generando certificado: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def quick_generate(self, request):
        """Super quick certificate generation with minimal data"""
        serializer = QuickGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        id_docente = serializer.validated_data['id_docente']

        # Use default options for quick generation
        generate_data = {
            'id_docente': id_docente,
            'destinatario': 'A QUIEN CORRESPONDA',
            'incluir_qr': True
        }

        # Create a new request with the expanded data
        from rest_framework.request import Request
        from django.http import HttpRequest

        # Create new request object with the data
        new_request = Request(HttpRequest())
        new_request._full_data = generate_data
        new_request.user = request.user
        new_request.auth = request.auth

        # Call the main generate method
        return self.generate(new_request)

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
        professors = CoursesHistory.objects.values('id_docente', 'profesor').annotate(
            course_count=models.Count('id'),
            latest_period=models.Max('periodo')
        ).distinct().order_by('profesor')

        professor_list = []
        for prof in professors:
            professor_list.append({
                'id_docente': prof['id_docente'],
                'name': prof['profesor'],
                'course_count': prof['course_count'],
                'latest_period': prof['latest_period']
            })

        return Response(professor_list)

    @action(detail=False, methods=['post'])
    @user_type_required(['administrator'])
    def bulk_generate(self, request):
        """Generate certificates for multiple professors"""
        serializer = BulkGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        id_docentes = data.get('docente_ids', [])

        # Get template
        template_id = data.get('template_id')
        if template_id:
            try:
                template = CertificateTemplate.objects.get(id=template_id)
            except CertificateTemplate.DoesNotExist:
                return Response({
                    'error': f'Template con ID {template_id} no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            template = CertificateTemplate.objects.filter(is_default=True).first()
            if not template:
                template = CertificateTemplate.objects.first()
            if not template:
                return Response({
                    'error': 'No hay plantillas de certificado disponibles'
                }, status=status.HTTP_404_NOT_FOUND)

        # Common options
        common_options = {
            'destinatario': data.get('destinatario', 'A QUIEN CORRESPONDA'),
            'incluir_qr': True,
            'periodos_filtro': data.get('periodos_filtro'),
            'periodo_actual': data.get('periodo_actual'),
            'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
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
                        'error': 'No se encontraron cursos'
                    })
                    continue

                professor_name = courses.first().profesor

                # Add id_docente to options
                current_options = dict(common_options)
                current_options['id_docente'] = id_docente

                # Generate PDF
                pdf_content, verification_code = CertificateService.generate_pdf(
                    id_docente=id_docente,
                    courses=courses,
                    template=template,
                    options=current_options
                )

                # Save certificate record
                certificate = GeneratedCertificate.objects.create(
                    professor=None,  # No user account required
                    template=template,
                    verification_code=verification_code,
                    metadata={
                        **current_options,
                        'professor_name': professor_name
                    }
                )

                # Save PDF file
                filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
                certificate.file.save(filename, pdf_content)

                generated_certificates.append({
                    'id': certificate.id,
                    'id_docente': id_docente,
                    'professor_name': professor_name,
                    'verification_code': verification_code,
                    'file_url': certificate.file.url if certificate.file else None
                })

            except Exception as e:
                errors.append({
                    'id_docente': id_docente,
                    'error': str(e)
                })

        return Response({
            'generated': len(generated_certificates),
            'errors': len(errors),
            'certificates': generated_certificates,
            'error_details': errors
        }, status=status.HTTP_201_CREATED)