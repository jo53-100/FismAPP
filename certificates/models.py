# certificates/models.py
from django.db import models
from core.models import CustomUser


class CertificateTemplate(models.Model):
    """Enhanced template for different types of certificates"""
    LAYOUT_CHOICES = (
        ('standard', 'Standard Layout'),
        ('formal', 'Formal Layout'),
        ('modern', 'Modern Layout'),
        ('minimal', 'Minimal Layout'),
    )

    # Basic Info
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layout_type = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='standard')

    # Images
    logo = models.ImageField(upload_to='certificate_logos/', null=True, blank=True)
    signature = models.ImageField(upload_to='certificate_signatures/', null=True, blank=True)
    background_image = models.ImageField(upload_to='certificate_backgrounds/', null=True, blank=True)

    # Header Information
    department_name = models.CharField(max_length=200, default="Facultad de Ciencias Físico Matemáticas")
    university_name = models.CharField(max_length=200, default="Benemérita Universidad Autónoma de Puebla")
    address = models.TextField(
        default="Av. San Claudio y 18 Sur, edif. FM1\nCiudad Universitaria, Col. San Manuel, Puebla, Pue. C.P. 72570\n01 (222) 229 55 00 Ext. 7550 y 7552"
    )

    # Certificate Content (with variables)
    title_text = models.CharField(
        max_length=100,
        default="CONSTANCIA DE CARGA ACADÉMICA",
        help_text="Título principal del certificado"
    )

    recipient_line = models.CharField(
        max_length=100,
        default="A QUIEN CORRESPONDA",
        help_text="A quién se dirige el certificado"
    )

    intro_text = models.TextField(
        default="El que suscribe, {secretary_name}, {secretary_title} de la {department_name}, de la {university_name}, por este medio hace constar que el Profesor Investigador:",
        help_text="Texto introductorio. Use {variables} para contenido dinámico"
    )

    courses_intro = models.CharField(
        max_length=200,
        default="Impartió los siguientes cursos:",
        help_text="Texto antes de la tabla de cursos"
    )

    closing_text = models.TextField(
        default="Se expide la presente para los fines legales que el interesado estime necesarios.",
        help_text="Texto de cierre"
    )

    # Signature Information
    secretary_name = models.CharField(max_length=100, default="Dr. José Piña")
    secretary_title = models.CharField(max_length=100, default="Secretario Académico")

    # Styling Options
    primary_color = models.CharField(max_length=7, default="#000000", help_text="Color principal (hex)")
    secondary_color = models.CharField(max_length=7, default="#666666", help_text="Color secundario (hex)")
    font_family = models.CharField(
        max_length=50,
        default="Helvetica",
        choices=[
            ('Helvetica', 'Helvetica'),
            ('Times-Roman', 'Times New Roman'),
            ('Courier', 'Courier'),
        ]
    )

        # Table Configuration
    include_course_table = models.BooleanField(default=True)
    table_fields = models.JSONField(
        default=list,
        help_text="Campos a incluir en la tabla de cursos",
        blank=True
    )
    
    # Configurable Certificate Fields
    certificate_fields = models.JSONField(
        default=list,
        help_text="Campos a incluir en el certificado (seleccionables)",
        blank=True
    )
 
    # QR and Verification
    include_qr_by_default = models.BooleanField(default=True)
    verification_text = models.CharField(
        max_length=200,
        default="Verifique la autenticidad de este documento en:",
        help_text="Texto para verificación QR"
    )

    # Footer
    university_motto = models.CharField(
        max_length=100,
        default='"Pensar bien, para vivir mejor"',
        help_text="Lema de la universidad"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        # Ensure only one default template
        if self.is_default:
            CertificateTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

        # Set default table fields if empty
        if not self.table_fields:
            self.table_fields = ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
            super().save(update_fields=['table_fields'])

    def __str__(self):
        return f"{self.name} {'(Default)' if self.is_default else ''}"

    def get_available_variables(self):
        """Return list of available template variables"""
        return [
            'professor_name', 'department_name', 'university_name',
            'secretary_name', 'secretary_title', 'current_date',
            'recipient', 'course_table'
        ]

    def get_available_certificate_fields(self):
        """Return comprehensive list of all available fields for certificates"""
        try:
            from .field_config import CERTIFICATE_FIELD_CONFIG
            return CERTIFICATE_FIELD_CONFIG
        except ImportError:
            return {}

    def get_default_certificate_fields(self):
        """Return default field configuration for new templates"""
        try:
            from .field_config import DEFAULT_CERTIFICATE_FIELDS
            return DEFAULT_CERTIFICATE_FIELDS
        except ImportError:
            return ['periodo', 'materia', 'clave', 'nrc', 'hr_cont']

    def get_selected_fields(self):
        """Return currently selected fields or defaults if none selected"""
        if self.certificate_fields:
            return self.certificate_fields
        return self.get_default_certificate_fields()

    def validate_certificate_fields(self):
        """Validate the selected certificate fields"""
        try:
            from django.core.exceptions import ValidationError
            from .field_config import validate_field_selection
            selected_fields = self.get_selected_fields()
            is_valid, message = validate_field_selection(selected_fields)
            if not is_valid:
                raise ValidationError(message)
            return True
        except ImportError:
            return True


class TemplatePreview(models.Model):
    """Store template previews for quick loading"""
    template = models.OneToOneField(CertificateTemplate, on_delete=models.CASCADE)
    preview_image = models.ImageField(upload_to='template_previews/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preview for {self.template.name}"


class GeneratedCertificate(models.Model):
    """Record of generated certificates"""
    professor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'professor'}, null=True, blank=True)
    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=64, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='generated_certificates/')
    metadata = models.JSONField(default=dict)  # Store generation parameters

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        if self.professor:
            return f"Certificate for {self.professor.get_full_name()} - {self.generated_at}"
        else:
            # Get the name from metadata if no user account
            professor_name = self.metadata.get('professor_name', 'Unknown Professor')
            return f"Certificate for {professor_name} - {self.generated_at}"


class CoursesHistory(models.Model):
    """Enhanced model to store professor's course history data"""
    # Core required fields
    id_docente = models.CharField(max_length=9, help_text="ID único del docente")
    profesor = models.CharField(max_length=60, help_text="Nombre completo del profesor")
    periodo = models.CharField(max_length=6, help_text="Período académico (ej: 202525)")
    materia = models.CharField(max_length=80, help_text="Nombre de la materia")
    clave = models.CharField(max_length=50, help_text="Clave de la materia")
    nrc = models.CharField(max_length=5, help_text="Número de referencia del curso")
    fecha_inicio = models.DateField(help_text="Fecha de inicio del curso")
    fecha_fin = models.DateField(help_text="Fecha de finalización del curso")
    hr_cont = models.IntegerField(help_text="Horas contacto del curso")
    listas_cruzadas = models.CharField(max_length=5, blank=True, null=True, help_text="Código de listas cruzadas")

    # Additional fields from Historia PA.csv
    source_name = models.CharField(max_length=100, blank=True, null=True, help_text="Nombre de la fuente")
    pp = models.CharField(max_length=10, blank=True, null=True, help_text="Código PP")
    nivel = models.CharField(max_length=20, blank=True, null=True, help_text="Nivel académico")
    ua = models.CharField(max_length=10, blank=True, null=True, help_text="Unidad académica")
    claves_programas = models.CharField(max_length=50, blank=True, null=True, help_text="Claves de programas")
    secc = models.CharField(max_length=5, blank=True, null=True, help_text="Sección")
    campus = models.IntegerField(blank=True, null=True, help_text="Campus")
    tipo_hr = models.CharField(max_length=20, blank=True, null=True, help_text="Tipo de horas")
    cred = models.IntegerField(blank=True, null=True, help_text="Créditos")
    modo_calif = models.CharField(max_length=20, blank=True, null=True, help_text="Modo de calificación")
    hr_semana = models.FloatField(blank=True, null=True, help_text="Horas por semana")
    dias = models.CharField(max_length=20, blank=True, null=True, help_text="Días de clase")
    hora = models.CharField(max_length=50, blank=True, null=True, help_text="Horario")
    metodo_asistencia = models.IntegerField(blank=True, null=True, help_text="Método de asistencia")
    salon = models.CharField(max_length=20, blank=True, null=True, help_text="Salón")
    ubicacion = models.CharField(max_length=50, blank=True, null=True, help_text="Ubicación")
    edo = models.CharField(max_length=10, blank=True, null=True, help_text="Estado")
    cupo = models.IntegerField(blank=True, null=True, help_text="Cupo máximo")
    insc = models.IntegerField(blank=True, null=True, help_text="Inscritos")
    disp = models.IntegerField(blank=True, null=True, help_text="Disponibles")
    ligas = models.FloatField(blank=True, null=True, help_text="Ligas")
    bloque = models.CharField(max_length=20, blank=True, null=True, help_text="Bloque")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Courses histories"
        ordering = ['periodo', 'materia']
        # Unique constraint to prevent duplicates
        unique_together = ['id_docente', 'nrc', 'periodo']

    def __str__(self):
        return f"{self.profesor} - {self.materia} ({self.periodo})"

    @classmethod
    def get_professors_summary(cls):
        """Get summary of professors and their course counts"""
        return cls.objects.values('id_docente', 'profesor').annotate(
            course_count=models.Count('id'),
            latest_period=models.Max('periodo'),
            total_hours=models.Sum('hr_cont')
        ).order_by('profesor')
