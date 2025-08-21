# certificates/serializers.py
from rest_framework import serializers
from .models import CertificateTemplate, GeneratedCertificate, CoursesHistory


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = '__all__'


class GeneratedCertificateSerializer(serializers.ModelSerializer):
    professor_name = serializers.SerializerMethodField()
    template_name = serializers.CharField(source='template.name', read_only=True)
    id_docente = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedCertificate
        fields = '__all__'

    def get_professor_name(self, obj):
        if obj.professor:
            return obj.professor.get_full_name()
        # Get name from metadata if no user account
        return obj.metadata.get('professor_name', 'Unknown')

    def get_id_docente(self, obj):
        return obj.metadata.get('id_docente', '')


class CoursesHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursesHistory
        fields = '__all__'


class GenerateCertificateSerializer(serializers.Serializer):
    """Simplified serializer for certificate generation using only id_docente"""
    id_docente = serializers.CharField(
        required=True,
        help_text="ID del docente en el sistema (requerido)",
        label='ID Docente'
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="ID del template a usar (opcional - usa default si no se especifica)",
        label="Plantilla"
    )
    destinatario = serializers.CharField(
        default="A QUIEN CORRESPONDA",
        help_text="Destinatario del certificado",
        label="Destinatario"
    )
    periodos_filtro = serializers.CharField(
        required=False,
        help_text="Períodos separados por comas (ej: 202525,202535) - dejar vacío para todos",
        label="Filtrar Períodos (opcional)"
    )
    periodo_actual = serializers.CharField(
        required=False,
        help_text="Período actual para separar (ej: 202525)",
        label="Período Actual (opcional)"
    )
    incluir_qr = serializers.BooleanField(
        default=True,
        help_text="Incluir código QR de verificación",
        label="Incluir QR"
    )

    # Convert comma-separated periods to list in validation
    def validate_periodos_filtro(self, value):
        if value:
            return [p.strip() for p in value.split(',') if p.strip()]
        return None

    def validate_id_docente(self, value):
        """Validate that the id_docente exists in course history"""
        if not CoursesHistory.objects.filter(id_docente=value).exists():
            raise serializers.ValidationError(
                f"No se encontraron cursos para el ID docente: {value}"
            )
        return value


class QuickGenerateSerializer(serializers.Serializer):
    """Super simple serializer for quick certificate generation"""
    id_docente = serializers.CharField(
        help_text="ID del docente",
        label="ID Docente"
    )

    def validate_id_docente(self, value):
        if not CoursesHistory.objects.filter(id_docente=value).exists():
            raise serializers.ValidationError(
                f"No se encontraron cursos para el ID docente: {value}"
            )
        return value


class VerifyCertificateSerializer(serializers.Serializer):
    """Serializer for certificate verification"""
    verification_code = serializers.CharField(required=True)


class ProfessorListSerializer(serializers.Serializer):
    """Serializer for listing available professors from course history"""
    id_docente = serializers.CharField()
    name = serializers.CharField()
    course_count = serializers.IntegerField()
    latest_period = serializers.CharField()


class BulkGenerateSerializer(serializers.Serializer):
    """Serializer for bulk certificate generation"""
    docente_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="Lista de IDs de docentes"
    )
    template_id = serializers.IntegerField(required=False, help_text="ID del template a usar")
    destinatario = serializers.CharField(default="A QUIEN CORRESPONDA")
    incluir_qr = serializers.BooleanField(default=True)
    periodos_filtro = serializers.ListField(child=serializers.CharField(), required=False)
    periodo_actual = serializers.CharField(required=False)

    def validate_docente_ids(self, value):
        """Validate that all docente IDs exist"""
        invalid_ids = []
        for id_docente in value:
            if not CoursesHistory.objects.filter(id_docente=id_docente).exists():
                invalid_ids.append(id_docente)

        if invalid_ids:
            raise serializers.ValidationError(
                f"Los siguientes IDs de docente no tienen cursos: {', '.join(invalid_ids)}"
            )
        return value


# Add/Update in certificates/serializers.py

class EnhancedGenerateCertificateSerializer(serializers.Serializer):
    """Enhanced serializer with period range support"""

    # Single or bulk mode
    generation_mode = serializers.ChoiceField(
        choices=['single', 'bulk'],
        default='single',
        help_text="Modo de generación: 'single' para un certificado, 'bulk' para múltiples"
    )

    # For single mode
    id_docente = serializers.CharField(
        required=False,
        help_text="ID del docente (requerido para modo single)"
    )

    # For bulk mode
    id_docentes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de IDs de docentes (requerido para modo bulk)"
    )

    # Common fields
    template_id = serializers.IntegerField(
        required=False,
        help_text="ID del template a usar (opcional - usa default si no se especifica)"
    )

    destinatario = serializers.CharField(
        default="A QUIEN CORRESPONDA",
        help_text="Destinatario del certificado"
    )

    # Period filtering options
    period_type = serializers.ChoiceField(
        choices=['all', 'list', 'range'],
        default='all',
        help_text="Tipo de filtro de períodos: 'all', 'list', o 'range'"
    )

    # For period list
    periods_list = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Períodos separados por comas (ej: 202525,202535)"
    )

    # For period range
    period_start = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Período inicial del rango (ej: 202425)"
    )

    period_end = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Período final del rango (ej: 202535)"
    )

    # Current period (optional)
    periodo_actual = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Período actual para separar (ej: 202535)"
    )

    incluir_qr = serializers.BooleanField(
        default=True,
        help_text="Incluir código QR de verificación"
    )

    def validate(self, data):
        """Custom validation for the serializer"""
        generation_mode = data.get('generation_mode', 'single')

        # Validate based on generation mode
        if generation_mode == 'single':
            if not data.get('id_docente'):
                raise serializers.ValidationError({
                    'id_docente': 'Este campo es requerido para modo single'
                })

            # Verify the professor exists
            if not CoursesHistory.objects.filter(id_docente=data['id_docente']).exists():
                raise serializers.ValidationError({
                    'id_docente': f"No se encontraron cursos para el ID docente: {data['id_docente']}"
                })

        elif generation_mode == 'bulk':
            if not data.get('id_docentes'):
                raise serializers.ValidationError({
                    'id_docentes': 'Este campo es requerido para modo bulk'
                })

            # Verify all professors exist
            invalid_ids = []
            for id_docente in data['id_docentes']:
                if not CoursesHistory.objects.filter(id_docente=id_docente).exists():
                    invalid_ids.append(id_docente)

            if invalid_ids:
                raise serializers.ValidationError({
                    'id_docentes': f"Los siguientes IDs no tienen cursos: {', '.join(invalid_ids)}"
                })

        # Validate period filtering
        period_type = data.get('period_type', 'all')

        if period_type == 'list':
            periods_list = data.get('periods_list', '')
            if not periods_list:
                raise serializers.ValidationError({
                    'periods_list': 'Este campo es requerido cuando period_type es "list"'
                })

            # Parse and validate periods
            periods = [p.strip() for p in periods_list.split(',') if p.strip()]
            data['periodos_filtro'] = periods

        elif period_type == 'range':
            period_start = data.get('period_start', '')
            period_end = data.get('period_end', '')

            if not period_start or not period_end:
                raise serializers.ValidationError({
                    'period_range': 'Ambos period_start y period_end son requeridos para period_type "range"'
                })

            # Validate format (6 digits)
            if len(period_start) != 6 or not period_start.isdigit():
                raise serializers.ValidationError({
                    'period_start': 'El período debe tener 6 dígitos (ej: 202425)'
                })

            if len(period_end) != 6 or not period_end.isdigit():
                raise serializers.ValidationError({
                    'period_end': 'El período debe tener 6 dígitos (ej: 202535)'
                })

            # Generate period range
            periods = self.generate_period_range(period_start, period_end)
            if not periods:
                raise serializers.ValidationError({
                    'period_range': 'No se pudo generar el rango de períodos'
                })

            data['periodos_filtro'] = periods

        else:  # period_type == 'all'
            data['periodos_filtro'] = None

        return data

    def generate_period_range(self, start_period, end_period):
        """Generate a list of periods between start and end"""
        periods = []

        try:
            start_year = int(start_period[:4])
            start_code = int(start_period[4:])
            end_year = int(end_period[:4])
            end_code = int(end_period[4:])

            current_year = start_year
            current_code = start_code

            while (current_year < end_year) or (current_year == end_year and current_code <= end_code):
                periods.append(f"{current_year:04d}{current_code:02d}")

                # Move to next period
                if current_code == 25:  # Spring -> Inter
                    current_code = 30
                elif current_code == 30:  # Inter -> Fall
                    current_code = 35
                elif current_code == 35:  # Fall -> Spring next year
                    current_code = 25
                    current_year += 1
                else:
                    break

                # Safety limit
                if len(periods) > 50:
                    break

        except (ValueError, IndexError):
            return []

        return periods
