# certificates/models.py
from django.db import models
from core.models import CustomUser


class CertificateTemplate(models.Model):
    """Template for different types of certificates"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='certificate_logos/', null=True, blank=True)
    signature = models.ImageField(upload_to='certificate_signatures/', null=True, blank=True)
    department_name = models.CharField(max_length=200, default="Facultad de Ciencias Físico Matemáticas")
    address = models.TextField(
        default="Av. San Claudio y 18 Sur, edif. FM1\nCiudad Universitaria, Col. San Manuel, Puebla, Pue. C.P. 72570\n01 (222) 229 55 00 Ext. 7550 y 7552")
    secretary_name = models.CharField(max_length=100, default="Dr. Gabriel Kantún Montiel")
    secretary_title = models.CharField(max_length=100, default="Secretario Académico")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class GeneratedCertificate(models.Model):
    """Record of generated certificates"""
    professor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'professor'})
    template = models.ForeignKey(CertificateTemplate, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=64, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='generated_certificates/')
    metadata = models.JSONField(default=dict)  # Store generation parameters

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Certificate for {self.professor.get_full_name()} - {self.generated_at}"


class CoursesHistory(models.Model):
    """Model to store professor's course history data"""
    id_docente = models.CharField(max_length=9)
    profesor = models.CharField(max_length=60)
    periodo = models.CharField(max_length=6)
    materia = models.CharField(max_length=80)
    clave = models.CharField(max_length=50)
    nrc = models.CharField(max_length=5)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    hr_cont = models.IntegerField()

    class Meta:
        verbose_name_plural = "Courses histories"
        ordering = ['periodo', 'materia']

    def __str__(self):
        return f"{self.profesor} - {self.materia} ({self.periodo})"
