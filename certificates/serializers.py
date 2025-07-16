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