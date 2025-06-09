# certificates/serializers.py
from rest_framework import serializers
from .models import CertificateTemplate, GeneratedCertificate, CoursesHistory


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = '__all__'


class GeneratedCertificateSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.get_full_name', read_only=True)
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
    """Serializer for certificate generation request"""
    template_id = serializers.IntegerField(
        required=True,
        help_text="ID del template a usar",
        label="Plantilla"
    )
    id_docente = serializers.CharField(
        required=True,
        help_text="ID del docente en el sistema",
        label='ID docente'
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


class VerifyCertificateSerializer(serializers.Serializer):
    """Serializer for certificate verification"""
    verification_code = serializers.CharField(required=True)


class ProfessorListSerializer(serializers.Serializer):
    """Serializer for listing available professors"""
    id_docente = serializers.CharField()
    name = serializers.CharField()


class BulkGenerateSerializer(serializers.Serializer):
    """Serializer for bulk certificate generation"""
    docente_ids = serializers.ListField(
        child=serializers.CharField(),
        help_text="Lista de IDs de docentes"
    )
    template_id = serializers.IntegerField(required=False, help_text="ID del template a usar")
    destinatario = serializers.CharField(default="A QUIEN CORRESPONDA")
    incluir_qr = serializers.BooleanField(default=True)
    url_verificacion = serializers.URLField(required=False)
    periodos_filtro = serializers.ListField(child=serializers.CharField(), required=False)
    periodo_actual = serializers.CharField(required=False)
    campos = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('periodo', 'Periodo'),
            ('materia', 'Materia'),
            ('clave', 'Clave'),
            ('nrc', 'NRC'),
            ('fecha_inicio', 'Fecha Inicio'),
            ('fecha_fin', 'Fecha Fin'),
            ('hr_cont', 'Horas Totales')
        ]),
        default=['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
    )