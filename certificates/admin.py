# certificates/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.response import TemplateResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import logging
from django.db import transaction
import json

from .models import CertificateTemplate, GeneratedCertificate, CoursesHistory, TemplatePreview
from .services import CertificateService

logger = logging.getLogger(__name__)


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'layout_type', 'is_default', 'is_active', 'test_certificate', 'created_at')
    list_filter = ('layout_type', 'is_default', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'department_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    actions = ['make_default']

    def test_certificate(self, obj):
        if obj.id:
            return format_html(
                '<a href="{}" class="button">🧪 Generar Prueba</a>',
                reverse('admin:certificates_certificatetemplate_test', args=[obj.id])
            )
        return "-"

    test_certificate.short_description = "Certificado de Prueba"

    def make_default(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Por favor seleccione exactamente un template.", level=messages.ERROR)
            return

        template = queryset.first()
        CertificateTemplate.objects.filter(is_default=True).update(is_default=False)
        template.is_default = True
        template.save()
        self.message_user(request, f"'{template.name}' ahora es el template por defecto.")

    make_default.short_description = "Hacer template por defecto"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('test/<int:template_id>/', self.admin_site.admin_view(self.test_certificate_view),
                 name='certificates_certificatetemplate_test'),
            path('wizard/', self.admin_site.admin_view(self.template_wizard_view),
                 name='certificates_certificatetemplate_wizard'),
        ]
        return custom_urls + urls

    def template_wizard_view(self, request):
        """Template creation wizard"""
        if request.method == 'POST':
            try:
                # Extract form data
                data = {
                    'name': request.POST.get('name'),
                    'layout_type': request.POST.get('layout_type', 'standard'),
                    'department_name': request.POST.get('department_name', 'Facultad de Ciencias Físico Matemáticas'),
                    'university_name': request.POST.get('university_name', 'Benemérita Universidad Autónoma de Puebla'),
                    'address': request.POST.get('address', ''),
                    'secretary_name': request.POST.get('secretary_name', 'Dr. José Piña'),
                    'secretary_title': request.POST.get('secretary_title', 'Secretario Académico'),
                    'primary_color': request.POST.get('primary_color', '#000000'),
                    'secondary_color': request.POST.get('secondary_color', '#666666'),
                    'font_family': request.POST.get('font_family', 'Helvetica'),
                }

                # Create template
                template = CertificateTemplate.objects.create(
                    created_by=request.user,
                    **data
                )

                messages.success(request, f'✅ Plantilla "{template.name}" creada exitosamente.')
                return redirect('admin:certificates_certificatetemplate_changelist')

            except Exception as e:
                messages.error(request, f'❌ Error creando plantilla: {str(e)}')

        # GET request - show wizard form
        context = {
            'title': '🧙‍♂️ Asistente de Creación de Plantillas',
            'opts': self.model._meta,
            'layout_choices': CertificateTemplate.LAYOUT_CHOICES,
            'font_choices': [
                ('Helvetica', 'Helvetica'),
                ('Times-Roman', 'Times New Roman'),
                ('Courier', 'Courier'),
            ]
        }
        return TemplateResponse(request, 'admin/certificates/template_wizard.html', context)

    def test_certificate_view(self, request, template_id):
        """Generate a test certificate using real data"""
        try:
            template = CertificateTemplate.objects.get(id=template_id)

            # Get a random professor with courses
            course = CoursesHistory.objects.first()
            if not course:
                messages.error(request, "No hay datos de cursos disponibles para generar certificado de prueba.")
                return redirect('admin:certificates_certificatetemplate_changelist')

            # Get courses for this professor
            courses = CoursesHistory.objects.filter(id_docente=course.id_docente)

            # Generate test certificate
            options = {
                'id_docente': course.id_docente,
                'destinatario': 'A QUIEN CORRESPONDA (PRUEBA)',
                'incluir_qr': True,
                'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
            }

            pdf_content, verification_code = CertificateService.generate_pdf(
                id_docente=course.id_docente,
                courses=courses,
                template=template,
                options=options
            )

            # Return PDF directly
            response = HttpResponse(pdf_content.read(), content_type='application/pdf')
            response[
                'Content-Disposition'] = f'inline; filename="test_certificate_{template.name}_{verification_code[:8]}.pdf"'
            return response

        except Exception as e:
            messages.error(request, f"Error generando certificado de prueba: {str(e)}")
            return redirect('admin:certificates_certificatetemplate_changelist')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['wizard_url'] = reverse('admin:certificates_certificatetemplate_wizard')
        return super().changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new template
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CoursesHistory)
class CoursesHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'profesor', 'materia', 'periodo', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont',
                    'listas_cruzadas')
    list_filter = ('periodo', 'fecha_inicio', 'listas_cruzadas')
    search_fields = ('profesor', 'materia', 'clave', 'nrc', 'id_docente')
    date_hierarchy = 'fecha_inicio'
    list_per_page = 50
    actions = ['generate_certificate_for_selected']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-data/', self.admin_site.admin_view(self.import_data_view),
                 name='certificates_courseshistory_import'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_url'] = reverse('admin:certificates_courseshistory_import')
        return super().changelist_view(request, extra_context)

    def import_data_view(self, request):
        """Import course data from Excel/CSV file"""
        if request.method == 'POST':
            if 'file' not in request.FILES:
                messages.error(request, 'Por favor seleccione un archivo.')
                return redirect('admin:certificates_courseshistory_changelist')

            uploaded_file = request.FILES['file']

            # Validate file type
            if not uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
                messages.error(request, 'El archivo debe ser Excel (.xlsx, .xls) o CSV (.csv)')
                return redirect('admin:certificates_courseshistory_changelist')

            try:
                # Read file based on type
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                else:
                    df = pd.read_excel(uploaded_file, sheet_name=0)

                # Clean column names
                df.columns = df.columns.str.strip()

                # Column mapping for Historia PA.csv format
                column_mapping = {
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
                }

                # Check available columns
                available_columns = list(df.columns)
                mapped_fields = {}

                for csv_col, model_field in column_mapping.items():
                    if csv_col in available_columns:
                        mapped_fields[model_field] = csv_col

                # Required fields
                required_fields = ['id_docente', 'profesor', 'periodo', 'materia', 'clave', 'nrc',
                                   'fecha_inicio', 'fecha_fin', 'hr_cont']

                missing_required = [field for field in required_fields if field not in mapped_fields]

                if missing_required:
                    messages.error(request, f'Faltan columnas requeridas: {missing_required}')
                    return redirect('admin:certificates_courseshistory_changelist')

                # Process data
                imported_count = 0
                updated_count = 0
                errors = []

                with transaction.atomic():
                    for index, row in df.iterrows():
                        try:
                            course_data = {}

                            for model_field, csv_column in mapped_fields.items():
                                value = row[csv_column]

                                # Handle different data types
                                if model_field in ['fecha_inicio', 'fecha_fin']:
                                    if pd.isna(value):
                                        raise ValueError(f"Missing date in {model_field}")
                                    date_val = pd.to_datetime(value, errors='coerce')
                                    if pd.isna(date_val):
                                        raise ValueError(f"Invalid date format in {model_field}: {value}")
                                    course_data[model_field] = date_val.date()

                                elif model_field == 'hr_cont':
                                    if pd.isna(value):
                                        raise ValueError(f"Missing required field: {model_field}")
                                    try:
                                        course_data[model_field] = int(float(value))
                                    except (ValueError, TypeError):
                                        raise ValueError(f"Invalid number format in {model_field}: {value}")

                                else:
                                    # Handle text fields
                                    if pd.isna(value):
                                        course_data[model_field] = None
                                    else:
                                        str_value = str(value).strip()
                                        course_data[model_field] = str_value if str_value else None

                            # Validate required fields
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
                            error_msg = f"Fila {index + 2}: {str(e)}"
                            errors.append(error_msg)
                            if len(errors) < 10:
                                logger.error(error_msg)

                # Show results
                success_message = f"Importación completada: {imported_count} nuevos registros, {updated_count} actualizados"
                if errors:
                    success_message += f", {len(errors)} errores"
                    if len(errors) <= 5:
                        for error in errors:
                            messages.warning(request, error)
                    else:
                        messages.warning(request, f"Se encontraron {len(errors)} errores. Revise los logs para más detalles.")

                messages.success(request, success_message)

            except Exception as e:
                logger.error(f"Import failed: {str(e)}")
                messages.error(request, f"Error en la importación: {str(e)}")

            return redirect('admin:certificates_courseshistory_changelist')

        # GET request - show import form
        context = {
            'title': 'Importar Datos de Cursos',
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/certificates/import_form.html', context)

    def generate_certificate_for_selected(self, request, queryset):
        """Generate certificates for selected professors"""
        id_docentes = list(queryset.values_list('id_docente', flat=True).distinct())

        if not id_docentes:
            self.message_user(request, "No se encontraron profesores válidos.", level=messages.ERROR)
            return

        # Get default template
        template = CertificateTemplate.objects.filter(is_default=True).first()
        if not template:
            template = CertificateTemplate.objects.first()

        if not template:
            self.message_user(request, "No hay templates disponibles.", level=messages.ERROR)
            return

        generated_count = 0
        for id_docente in id_docentes:
            try:
                courses = CoursesHistory.objects.filter(id_docente=id_docente)
                if courses.exists():
                    options = {
                        'id_docente': id_docente,
                        'destinatario': 'A QUIEN CORRESPONDA',
                        'incluir_qr': True,
                        'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
                    }

                    professor_name = courses.first().profesor

                    pdf_content, verification_code = CertificateService.generate_pdf(
                        id_docente=id_docente,
                        courses=courses,
                        template=template,
                        options=options
                    )

                    certificate = GeneratedCertificate.objects.create(
                        template=template,
                        verification_code=verification_code,
                        metadata={**options, 'professor_name': professor_name}
                    )

                    filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
                    certificate.file.save(filename, pdf_content)
                    generated_count += 1

            except Exception as e:
                self.message_user(request, f"Error generando certificado para {id_docente}: {str(e)}",
                                  level=messages.ERROR)

        self.message_user(request, f"Se generaron {generated_count} certificados exitosamente.")

    generate_certificate_for_selected.short_description = "Generar certificados para profesores seleccionados"


@admin.register(GeneratedCertificate)
class GeneratedCertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_professor_name', 'get_id_docente', 'template', 'verification_code_short',
                    'get_period_info', 'generated_at', 'download_link')
    list_filter = ('template', 'generated_at')
    search_fields = ('verification_code', 'metadata__professor_name', 'metadata__id_docente')
    readonly_fields = ('id', 'verification_code', 'generated_at', 'metadata_display')
    actions = ['regenerate_certificates']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('quick-generate/', self.admin_site.admin_view(self.quick_generate_view),
                 name='certificates_generatedcertificate_quick_generate'),
            path('bulk-generate/', self.admin_site.admin_view(self.bulk_generate_view),
                 name='certificates_generatedcertificate_bulk_generate'),
            path('get-periods/', self.admin_site.admin_view(self.get_periods_ajax),
                 name='certificates_generatedcertificate_get_periods'),
            path('preview-bulk/', self.admin_site.admin_view(self.preview_bulk_ajax),
                 name='certificates_generatedcertificate_preview_bulk'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['quick_generate_url'] = reverse('admin:certificates_generatedcertificate_quick_generate')
        extra_context['bulk_generate_url'] = reverse('admin:certificates_generatedcertificate_bulk_generate')
        return super().changelist_view(request, extra_context)

    def get_periods_ajax(self, request):
        """AJAX endpoint to get periods for a professor"""
        id_docente = request.GET.get('id_docente')
        if not id_docente:
            return JsonResponse({'error': 'id_docente required'})

        from .services import CertificateService
        periods = CoursesHistory.objects.filter(
            id_docente=id_docente
        ).values_list('periodo', flat=True).distinct().order_by('-periodo')

        formatted_periods = []
        for periodo in periods:
            formatted_periods.append({
                'codigo': periodo,
                'descripcion': CertificateService.formatear_periodo(periodo),
                'cursos_count': CoursesHistory.objects.filter(
                    id_docente=id_docente, periodo=periodo
                ).count()
            })

        return JsonResponse({'periods': formatted_periods})

    def preview_bulk_ajax(self, request):
        """AJAX endpoint for bulk generation preview"""
        periodo = request.GET.get('periodo')
        if not periodo:
            return JsonResponse({'error': 'periodo required'})

        from django.db import models
        professors = CoursesHistory.objects.filter(
            periodo=periodo
        ).values('id_docente', 'profesor').annotate(
            courses_count=models.Count('id')
        ).distinct().order_by('profesor')

        return JsonResponse({'professors': list(professors)})

    def quick_generate_view(self, request):
        """Enhanced quick certificate generation form"""
        if request.method == 'POST':
            id_docente = request.POST.get('id_docente')
            template_id = request.POST.get('template_id')
            destinatario = request.POST.get('destinatario', 'A QUIEN CORRESPONDA')
            periodo_especifico = request.POST.get('periodo_especifico')

            if not id_docente:
                messages.error(request, 'ID Docente es requerido.')
                return redirect('admin:certificates_generatedcertificate_changelist')

            try:
                # Verify courses exist
                courses = CoursesHistory.objects.filter(id_docente=id_docente)
                if not courses.exists():
                    messages.error(request, f'No se encontraron cursos para el ID docente: {id_docente}')
                    return redirect('admin:certificates_generatedcertificate_changelist')

                # Apply period filter if specified
                if periodo_especifico:
                    filtered_courses = courses.filter(periodo=periodo_especifico)
                    if not filtered_courses.exists():
                        messages.error(request, f'No se encontraron cursos para el período: {periodo_especifico}')
                        return redirect('admin:certificates_generatedcertificate_changelist')
                    courses = filtered_courses

                # Get template
                template = self.get_template_for_generation(template_id)
                if not template:
                    messages.error(request, 'No hay plantillas de certificado disponibles.')
                    return redirect('admin:certificates_generatedcertificate_changelist')

                professor_name = courses.first().profesor

                # Generate certificate
                options = {
                    'id_docente': id_docente,
                    'destinatario': destinatario,
                    'periodo_especifico': periodo_especifico,
                    'incluir_qr': True,
                    'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
                }

                from .services import CertificateService
                pdf_content, verification_code = CertificateService.generate_pdf(
                    id_docente=id_docente,
                    courses=courses,
                    template=template,
                    options=options
                )

                # Save certificate
                certificate = GeneratedCertificate.objects.create(
                    template=template,
                    verification_code=verification_code,
                    metadata={**options, 'professor_name': professor_name}
                )

                filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
                certificate.file.save(filename, pdf_content)

                period_info = f" para el período {CertificateService.formatear_periodo(periodo_especifico)}" if periodo_especifico else ""
                messages.success(request, f'✅ Certificado generado exitosamente para {professor_name}{period_info}')
                return redirect('admin:certificates_generatedcertificate_changelist')

            except Exception as e:
                messages.error(request, f'❌ Error generando certificado: {str(e)}')
                return redirect('admin:certificates_generatedcertificate_changelist')

        # GET request - show enhanced form
        context = {
            'title': '⚡ Generar Certificado Rápido',
            'opts': self.model._meta,
            'templates': CertificateTemplate.objects.filter(is_active=True),
            'professors': CoursesHistory.objects.values('id_docente', 'profesor').distinct().order_by('profesor')[:100],
            'available_periods': CoursesHistory.objects.values_list('periodo', flat=True).distinct().order_by(
                '-periodo')
        }
        return TemplateResponse(request, 'admin/certificates/generate_form.html', context)

    def bulk_generate_view(self, request):
        """Bulk certificate generation interface"""
        if request.method == 'POST':
            template_id = request.POST.get('template_id')
            periodo_filtro = request.POST.get('periodo_filtro')
            destinatario = request.POST.get('destinatario', 'A QUIEN CORRESPONDA')

            # Get professors based on criteria
            professors_query = CoursesHistory.objects.values('id_docente', 'profesor').distinct()
            if periodo_filtro:
                professors_query = professors_query.filter(periodo=periodo_filtro)

            generated_count = 0
            error_count = 0

            # Get template
            template = self.get_template_for_generation(template_id)
            if not template:
                messages.error(request, 'No hay plantillas de certificado disponibles.')
                return redirect('admin:certificates_generatedcertificate_changelist')

            for prof_data in professors_query:
                try:
                    id_docente = prof_data['id_docente']
                    courses = CoursesHistory.objects.filter(id_docente=id_docente)

                    if periodo_filtro:
                        courses = courses.filter(periodo=periodo_filtro)

                    if courses.exists():
                        options = {
                            'id_docente': id_docente,
                            'destinatario': destinatario,
                            'periodo_especifico': periodo_filtro,
                            'incluir_qr': True,
                            'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
                        }

                        from .services import CertificateService
                        pdf_content, verification_code = CertificateService.generate_pdf(
                            id_docente=id_docente,
                            courses=courses,
                            template=template,
                            options=options
                        )

                        certificate = GeneratedCertificate.objects.create(
                            template=template,
                            verification_code=verification_code,
                            metadata={**options, 'professor_name': prof_data['profesor']}
                        )

                        filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
                        certificate.file.save(filename, pdf_content)
                        generated_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error generating certificate for {prof_data['id_docente']}: {e}")

            messages.success(request,
                             f'Generación masiva completada: {generated_count} certificados generados, {error_count} errores')
            return redirect('admin:certificates_generatedcertificate_changelist')

        context = {
            'title': '📦 Generación Masiva de Certificados',
            'opts': self.model._meta,
            'templates': CertificateTemplate.objects.filter(is_active=True),
            'available_periods': CoursesHistory.objects.values_list('periodo', flat=True).distinct().order_by(
                '-periodo')
        }
        return TemplateResponse(request, 'admin/certificates/bulk_generate_form.html', context)

    def get_template_for_generation(self, template_id):
        """Helper method to get template"""
        if template_id:
            try:
                return CertificateTemplate.objects.get(id=template_id)
            except CertificateTemplate.DoesNotExist:
                return None
        else:
            template = CertificateTemplate.objects.filter(is_default=True).first()
            if not template:
                template = CertificateTemplate.objects.first()
            return template

    def get_period_info(self, obj):
        """Display period information from metadata"""
        periodo = obj.metadata.get('periodo_especifico')
        if periodo:
            from .services import CertificateService
            return CertificateService.formatear_periodo(periodo)

        periodos = obj.metadata.get('periodos_incluidos', [])
        if periodos:
            if len(periodos) == 1:
                from .services import CertificateService
                return CertificateService.formatear_periodo(periodos[0])
            else:
                return f"{len(periodos)} períodos"
        return "Todos los períodos"

    get_period_info.short_description = "Período(s)"

    def get_professor_name(self, obj):
        if obj.professor:
            return obj.professor.get_full_name()
        return obj.metadata.get('professor_name', 'Unknown')

    get_professor_name.short_description = "Profesor"

    def get_id_docente(self, obj):
        return obj.metadata.get('id_docente', 'N/A')

    get_id_docente.short_description = "ID Docente"

    def verification_code_short(self, obj):
        return f"{obj.verification_code[:8]}..."

    verification_code_short.short_description = "Código (abrev.)"

    def download_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" class="button">📥 Descargar</a>',
                obj.file.url
            )
        return "-"

    download_link.short_description = "Archivo"

    def metadata_display(self, obj):
        return format_html(
            '<pre>{}</pre>',
            json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        )

    metadata_display.short_description = "Metadata"

    def regenerate_certificates(self, request, queryset):
        """Regenerate selected certificates"""
        regenerated_count = 0
        for certificate in queryset:
            try:
                id_docente = certificate.metadata.get('id_docente')
                if not id_docente:
                    continue

                courses = CoursesHistory.objects.filter(id_docente=id_docente)
                if not courses.exists():
                    continue

                options = certificate.metadata.copy()
                from .services import CertificateService
                pdf_content, verification_code = CertificateService.generate_pdf(
                    id_docente=id_docente,
                    courses=courses,
                    template=certificate.template,
                    options=options
                )

                # Update existing certificate
                certificate.verification_code = verification_code
                filename = f"certificate_{id_docente}_{verification_code[:8]}.pdf"
                certificate.file.save(filename, pdf_content)
                certificate.save()

                regenerated_count += 1

            except Exception as e:
                self.message_user(request, f"Error regenerando certificado {certificate.id}: {str(e)}",
                                  level=messages.ERROR)

        self.message_user(request, f"Se regeneraron {regenerated_count} certificados exitosamente.")

    regenerate_certificates.short_description = "Regenerar certificados seleccionados"