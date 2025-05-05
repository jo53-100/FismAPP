# certificates/services.py
import os
import hashlib
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.platypus import Flowable
from django.conf import settings
from django.core.files.base import ContentFile
from .models import GeneratedCertificate, CoursesHistory


class QRCodeFlowable(Flowable):
    """Flowable para insertar un código QR en el PDF"""

    def __init__(self, qr_value, size=1.5 * inch):
        Flowable.__init__(self)
        self.qr_code = QrCodeWidget(qr_value)
        self.size = size

    def draw(self):
        drawing = Drawing(self.size, self.size)
        drawing.add(self.qr_code)
        drawing.scale(1, 1)
        renderPDF.draw(drawing, self.canv, 0, 0)


class CertificateService:
    @staticmethod
    def formatear_periodo(periodo):
        """Convierte el código de periodo a un formato legible."""
        str_periodo = str(periodo)

        if "Primavera" in str_periodo or "Otoño" in str_periodo or "Interperiodo" in str_periodo:
            return str_periodo

        try:
            año = str_periodo[:4]
            codigo = str_periodo[-2:]
            if codigo == "25":
                return f"Primavera {año}"
            elif codigo == "35":
                return f"Otoño {año}"
            elif codigo == "30":
                return f"Interperiodo {año}"
            else:
                return str_periodo
        except:
            return str_periodo

    @staticmethod
    def generar_codigo_autenticacion(profesor, fecha, id_docente):
        """Genera un código único para autenticar el documento"""
        cadena = f"{profesor}_{id_docente}_{fecha}_{uuid.uuid4()}"
        return hashlib.md5(cadena.encode()).hexdigest()

    @staticmethod
    def generate_pdf(professor, template, options):
        """
        Genera un certificado PDF para un profesor

        Args:
            professor: Instancia del usuario profesor
            template: Template de certificado a usar
            options: Diccionario con opciones de generación

        Returns:
            Tupla (content_file, verification_code)
        """
        # Obtener cursos del profesor
        id_docente = options.get('id_docente')
        if not id_docente:
            # Intentar obtener del perfil del profesor si existe
            if hasattr(professor, 'professorprofile'):
                id_docente = professor.professorprofile.id_docente
            else:
                raise ValueError("ID de docente no proporcionado")

        # Filtrar cursos
        cursos = CoursesHistory.objects.filter(id_docente=id_docente)

        # Aplicar filtros de periodo si existen
        periodos_filtro = options.get('periodos_filtro')
        if periodos_filtro:
            cursos = cursos.filter(periodo__in=periodos_filtro)

        if not cursos.exists():
            raise ValueError("No se encontraron cursos para el profesor")

        # Separar cursos actuales si se especifica
        periodo_actual = options.get('periodo_actual')
        cursos_actuales = None
        if periodo_actual:
            cursos_actuales = cursos.filter(periodo=periodo_actual)
            cursos = cursos.exclude(periodo=periodo_actual)

        # Configurar el documento PDF
        from io import BytesIO
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Definir estilos
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Titulo',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=6
        ))

        styles.add(ParagraphStyle(
            name='Direccion',
            fontName='Helvetica',
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=6
        ))

        styles.add(ParagraphStyle(
            name='Encabezado',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=12
        ))

        styles.add(ParagraphStyle(
            name='Texto',
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))

        styles.add(ParagraphStyle(
            name='TextoCentrado',
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=12
        ))

        styles.add(ParagraphStyle(
            name='Firma',
            fontName='Helvetica',
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=0
        ))

        # Crear elementos del documento
        elementos = []

        # Encabezado
        elementos.append(Paragraph(template.department_name, styles['Titulo']))
        elementos.append(Paragraph(template.address.replace('\n', '<br/>'), styles['Direccion']))

        # Logo si existe
        if template.logo:
            try:
                img = Image(template.logo.path)
                img.drawHeight = 1.5 * inch
                img.drawWidth = 1.5 * inch
                img.hAlign = 'CENTER'
                elementos.append(img)
            except:
                pass

        elementos.append(Spacer(1, 0.5 * inch))

        # Destinatario
        destinatario = options.get('destinatario', 'A QUIEN CORRESPONDA')
        elementos.append(Paragraph(destinatario, styles['Encabezado']))
        elementos.append(Paragraph("P R E S E N T E", styles['Encabezado']))
        elementos.append(Spacer(1, 0.25 * inch))

        # Texto introductorio
        texto_intro = f"El que suscribe, {template.secretary_name}, {template.secretary_title} de la {template.department_name}, de la Benemérita Universidad Autónoma de Puebla, por este medio hace constar que el Profesor Investigador:"
        elementos.append(Paragraph(texto_intro, styles['Texto']))

        # Nombre del profesor
        elementos.append(Paragraph(professor.get_full_name(), styles['TextoCentrado']))

        # Tabla de cursos impartidos
        if cursos.exists():
            elementos.append(Paragraph("Impartió los siguientes cursos:", styles['Texto']))

            # Preparar datos para la tabla
            campos = options.get('campos',
                                 ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'])
            encabezados = []
            anchos_columna = []

            # Mapeo de campos a encabezados
            mapeo_campos = {
                'periodo': ('Periodo', 1.1 * inch),
                'materia': ('Nombre de la Materia', 2 * inch),
                'clave': ('Clave', 0.9 * inch),
                'nrc': ('NRC', 0.7 * inch),
                'fecha_inicio': ('Fecha Inicio', 1 * inch),
                'fecha_fin': ('Fecha Fin', 1 * inch),
                'hr_cont': ('Horas Totales', 0.8 * inch)
            }

            for campo in campos:
                if campo in mapeo_campos:
                    encabezados.append(mapeo_campos[campo][0])
                    anchos_columna.append(mapeo_campos[campo][1])

            datos_tabla = [encabezados]

            # Agregar filas con datos
            for curso in cursos:
                fila = []
                for campo in campos:
                    if campo == 'periodo':
                        fila.append(CertificateService.formatear_periodo(curso.periodo))
                    elif campo == 'materia':
                        fila.append(curso.materia)
                    elif campo == 'clave':
                        fila.append(curso.clave)
                    elif campo == 'nrc':
                        fila.append(curso.nrc)
                    elif campo == 'fecha_inicio':
                        fila.append(curso.fecha_inicio.strftime('%d/%m/%Y'))
                    elif campo == 'fecha_fin':
                        fila.append(curso.fecha_fin.strftime('%d/%m/%Y'))
                    elif campo == 'hr_cont':
                        fila.append(str(curso.hr_cont))
                datos_tabla.append(fila)

            # Crear tabla
            tabla = Table(datos_tabla, colWidths=anchos_columna)
            estilo_tabla = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ])
            tabla.setStyle(estilo_tabla)
            elementos.append(tabla)

        # Tabla de cursos actuales si aplica
        if cursos_actuales and cursos_actuales.exists():
            elementos.append(Spacer(1, 0.3 * inch))
            elementos.append(Paragraph("Actualmente imparte los siguientes cursos:", styles['Texto']))

            # Similar a la tabla anterior pero con cursos actuales
            # ... (código similar para la tabla de cursos actuales)

        elementos.append(Spacer(1, 0.5 * inch))

        # Fecha y cierre
        fecha_actual = datetime.today().strftime('%d de %B de %Y')
        elementos.append(Paragraph("Se expide la presente para los fines legales que el interesado estime necesarios.",
                                   styles['Texto']))
        elementos.append(Spacer(1, 0.25 * inch))
        elementos.append(Paragraph("A T E N T A M E N T E", styles['Firma']))
        elementos.append(Paragraph('"Pensar bien, para vivir mejor"', styles['Firma']))
        elementos.append(Paragraph(f"Puebla, Pue., a {fecha_actual}", styles['Firma']))
        elementos.append(Spacer(1, 0.75 * inch))

        # Firma electrónica si existe
        if template.signature:
            try:
                firma = Image(template.signature.path)
                firma.drawHeight = 0.75 * inch
                firma.drawWidth = 2 * inch
                firma.hAlign = 'CENTER'
                elementos.append(firma)
                elementos.append(Spacer(1, 0.1 * inch))
            except:
                pass

        elementos.append(Paragraph(template.secretary_name, styles['Firma']))
        elementos.append(Paragraph(template.secretary_title, styles['Firma']))

        # Generar código de verificación y QR si se solicita
        verification_code = CertificateService.generar_codigo_autenticacion(
            professor.get_full_name(),
            fecha_actual,
            id_docente
        )

        if options.get('incluir_qr', True):
            url_verificacion = options.get('url_verificacion', f"{settings.SITE_URL}/api/certificates/verify/")
            url_completa = f"{url_verificacion}{verification_code}"

            elementos.append(Spacer(1, 0.5 * inch))
            qr = QRCodeFlowable(url_completa, size=1.5 * inch)
            qr.hAlign = 'RIGHT'
            elementos.append(qr)

            # Texto de verificación
            estilo_verificacion = ParagraphStyle(
                name='Verificacion',
                fontName='Helvetica',
                fontSize=8,
                alignment=TA_CENTER
            )
            elementos.append(Spacer(1, 0.1 * inch))
            elementos.append(Paragraph("Verifique la autenticidad de este documento en:", estilo_verificacion))
            elementos.append(Paragraph(f"{url_verificacion}", estilo_verificacion))
            elementos.append(Paragraph(f"Código de verificación: {verification_code}", estilo_verificacion))

        # Generar PDF
        doc.build(elementos)
        buffer.seek(0)

        # Crear archivo de contenido
        pdf_content = ContentFile(buffer.getvalue())
        buffer.close()

        return pdf_content, verification_code