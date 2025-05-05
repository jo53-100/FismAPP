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

    class Meta:
        model = GeneratedCertificate
        fields = '__all__'


class CoursesHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursesHistory
        fields = '__all__'


class GenerateCertificateSerializer(serializers.Serializer):
    """Serializer for certificate generation request"""
    template_id = serializers.IntegerField(required=False, help_text="ID del template a usar")
    id_docente = serializers.CharField(required=False, help_text="ID del docente en el sistema")
    destinatario = serializers.CharField(default="A QUIEN CORRESPONDA", help_text="Destinatario del certificado")
    incluir_qr = serializers.BooleanField(default=True, help_text="Incluir código QR de verificación")
    url_verificacion = serializers.URLField(required=False, help_text="URL base para verificación")
    periodos_filtro = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Lista de períodos a filtrar"
    )
    periodo_actual = serializers.CharField(required=False, help_text="Período actual para separar cursos actuales")
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
        default=['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'],
        help_text="Campos a incluir en la tabla de cursos"
    )


class VerifyCertificateSerializer(serializers.Serializer):
    """Serializer for certificate verification"""
    verification_code = serializers.CharField(required=True)