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

try:
    from PyPDF2 import PdfReader, PdfWriter

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("PyPDF2 not installed. Template-based certificates will not work.")

import qrcode
from PIL import Image as PILImage
from io import BytesIO


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
    TEMPLATE_POSITIONS = {
        'default': {
            'recipient': {'x': 72, 'y_from_top': 200, 'font': 'Helvetica-Bold', 'size': 12},
            'professor_name': {'x': 'center', 'y_from_top': 280, 'font': 'Helvetica-Bold', 'size': 14},
            'course_table': {'x': 72, 'y_from_top': 350, 'max_width': 468, 'max_height': 250},
            'date': {'x': 400, 'y_from_bottom': 120, 'font': 'Helvetica', 'size': 11},
            'signature': {'x': 250, 'y_from_bottom': 150, 'width': 144, 'height': 54},
            'qr_code': {'x_from_right': 150, 'y_from_bottom': 50, 'size': 108}
        }
    }

    @classmethod
    def group_courses_by_listas_cruzadas(cls, courses):

        from collections import defaultdict

        # Group courses by listas_cruzadas
        grouped = defaultdict(list)

        for course in courses:
            # Use listas_cruzadas as key, or course ID if listas_cruzadas is empty
            key = course.listas_cruzadas if course.listas_cruzadas else f"single_{course.id}"
            grouped[key].append(course)

        # Process each group
        processed_courses = []

        for listas_cruzadas_code, course_list in grouped.items():
            if len(course_list) == 1:
                # Single course, no grouping needed
                course = course_list[0]
                processed_courses.append({
                    'periodo': cls.formatear_periodo(course.periodo),
                    'materia': course.materia,
                    'clave': course.clave,
                    'nrc': course.nrc,
                    'fecha_inicio': course.fecha_inicio,
                    'fecha_fin': course.fecha_fin,
                    'hr_cont': course.hr_cont,
                    'listas_cruzadas': course.listas_cruzadas,
                    'is_grouped': False,
                    'course_count': 1
                })
            else:
                # Multiple courses with same listas_cruzadas
                # Sort courses for consistent display
                course_list = sorted(course_list, key=lambda x: x.materia)

                # Create multi-line formatted strings for each field
                materias = []
                claves = []
                nrcs = []

                for course in course_list:
                    materias.append(course.materia)
                    claves.append(course.clave)
                    nrcs.append(course.nrc)

                # Use data from first course as base
                base_course = course_list[0]

                # Sum hr_cont
                total_hr_cont = sum(course.hr_cont for course in course_list)

                processed_courses.append({
                    'periodo': cls.formatear_periodo(base_course.periodo),
                    'materia': materias,  # List of course names
                    'clave': claves,  # Always use list of all claves, even if they're the same
                    'nrc': nrcs,  # List of NRCs
                    'fecha_inicio': base_course.fecha_inicio,
                    'fecha_fin': base_course.fecha_fin,
                    'hr_cont': total_hr_cont,
                    'listas_cruzadas': base_course.listas_cruzadas,
                    'is_grouped': True,
                    'course_count': len(course_list),
                    'grouped_courses': course_list  # Keep reference to original courses
                })

        return processed_courses

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

    @classmethod
    def generate_pdf(cls, id_docente, courses, template, options):
        # Obtener datos del profesor de los cursos
        profesor_data = courses.first()
        if not profesor_data:
            raise ValueError("No se encontraron cursos para el profesor")

        nombre_profesor = profesor_data.profesor

        # Aplicar filtros de periodo si existen
        periodos_filtro = options.get('periodos_filtro')
        if periodos_filtro:
            filtered_courses = courses.filter(periodo__in=periodos_filtro)
            if filtered_courses.exists():
                courses = filtered_courses

        # Separar cursos actuales si se especifica
        periodo_actual = options.get('periodo_actual')
        cursos_actuales = None
        if periodo_actual:
            cursos_actuales = courses.filter(periodo=periodo_actual)
            courses = courses.exclude(periodo=periodo_actual)

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
        elementos.append(Paragraph(nombre_profesor, styles['TextoCentrado']))

        # Group courses by listas_cruzadas
        grouped_courses = cls.group_courses_by_listas_cruzadas(courses)

        if grouped_courses:
            elementos.append(Paragraph("Impartió los siguientes cursos:", styles['Texto']))

            # Preparar datos para la tabla
            campos = options.get('campos',
                                 ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'])
            encabezados = []
            anchos_columna = []

            # Mapeo de campos a encabezados con anchos ajustados para contenido multi-línea
            mapeo_campos = {
                'periodo': ('Periodo', 1.1 * inch),
                'materia': ('Nombre de la Materia', 2.5 * inch),  # Increased width for multi-line content
                'clave': ('Clave', 1.0 * inch),  # Slightly increased
                'nrc': ('NRC', 0.9 * inch),  # Increased for multi-line NRCs
                'fecha_inicio': ('Fecha Inicio', 1 * inch),
                'fecha_fin': ('Fecha Fin', 1 * inch),
                'hr_cont': ('Horas \\ Totales', 0.8 * inch)
            }

            for campo in campos:
                if campo in mapeo_campos:
                    encabezados.append(mapeo_campos[campo][0])
                    anchos_columna.append(mapeo_campos[campo][1])

            datos_tabla = [encabezados]

            # Agregar filas con datos agrupados y soporte multi-línea
            for course_data in grouped_courses:
                fila = []
                for campo in campos:
                    if campo == 'periodo':
                        # Always use the already formatted periodo from grouped_courses
                        fila.append(course_data['periodo'])
                    elif campo == 'materia':
                        if course_data['is_grouped'] and isinstance(course_data['materia'], list):
                            # Create Paragraph for multi-line content with proper formatting
                            materia_lines = course_data['materia']
                            if len(materia_lines) <= 3:  # If 3 or fewer lines, show all
                                materia_text = '<br/>'.join(materia_lines)
                            else:  # If more than 3, show first 2 and indicate more
                                shown_lines = materia_lines[:2]
                                remaining = len(materia_lines) - 2
                                materia_text = '<br/>'.join(shown_lines) + f'<br/><i>(+{remaining} más)</i>'

                            # Create a paragraph with smaller font for grouped content
                            para_style = ParagraphStyle(
                                'MultiLineCourse',
                                fontName='Helvetica',
                                fontSize=8,
                                alignment=TA_CENTER,
                                leading=10
                            )
                            fila.append(Paragraph(materia_text, para_style))
                        else:
                            fila.append(course_data['materia'])
                    elif campo == 'clave':
                        if course_data['is_grouped'] and isinstance(course_data['clave'], list):
                            # Always show all claves for grouped courses, even if they're the same
                            clave_text = '<br/>'.join(course_data['clave'])
                            para_style = ParagraphStyle(
                                'MultiLineClave',
                                fontName='Helvetica',
                                fontSize=8,
                                alignment=TA_CENTER,
                                leading=10
                            )
                            fila.append(Paragraph(clave_text, para_style))
                        else:
                            fila.append(course_data['clave'])
                    elif campo == 'nrc':
                        if course_data['is_grouped'] and isinstance(course_data['nrc'], list):
                            nrc_text = '<br/>'.join(course_data['nrc'])
                            para_style = ParagraphStyle(
                                'MultiLineNRC',
                                fontName='Helvetica',
                                fontSize=8,
                                alignment=TA_CENTER,
                                leading=10
                            )
                            fila.append(Paragraph(nrc_text, para_style))
                        else:
                            fila.append(course_data['nrc'])
                    elif campo == 'fecha_inicio':
                        fila.append(course_data['fecha_inicio'].strftime('%d/%m/%Y'))
                    elif campo == 'fecha_fin':
                        fila.append(course_data['fecha_fin'].strftime('%d/%m/%Y'))
                    elif campo == 'hr_cont':
                        if course_data['is_grouped']:
                            # Show total hours with breakdown if grouped
                            total_hrs = course_data['hr_cont']
                            course_count = course_data['course_count']
                            fila.append(f"{total_hrs}\n({course_count} cursos)")
                        else:
                            fila.append(str(course_data['hr_cont']))
                datos_tabla.append(fila)

            # Crear tabla con mejor soporte para contenido multi-línea
            tabla = Table(datos_tabla, colWidths=anchos_columna)
            estilo_tabla = TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # TOP alignment for multi-line content
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),

                # Content styling with better padding for multi-line content
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),

                # Increased padding to accommodate multi-line content
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),

                # Grid and borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LINEABOVE', (0, 1), (-1, -1), 0.5, colors.black),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ])

            # Add conditional formatting for grouped rows
            for i, course_data in enumerate(grouped_courses):
                row_index = i + 1  # +1 because row 0 is header
                if course_data['is_grouped']:
                    # Highlight grouped rows with light blue background
                    estilo_tabla.add('BACKGROUND', (0, row_index), (-1, row_index), colors.Color(0.95, 0.98, 1.0))
                    # Increase row height for grouped content
                    estilo_tabla.add('ROWBACKGROUNDS', (0, row_index), (-1, row_index), [colors.Color(0.95, 0.98, 1.0)])

            tabla.setStyle(estilo_tabla)
            elementos.append(tabla)

            # Add explanation for grouped courses if any exist
            if any(course['is_grouped'] for course in grouped_courses):
                elementos.append(Spacer(1, 0.2 * inch))
                explanation_style = ParagraphStyle(
                    'Explanation',
                    fontName='Helvetica-Oblique',
                    fontSize=9,
                    alignment=TA_LEFT,
                    textColor=colors.Color(0.3, 0.3, 0.3)
                )
                elementos.append(Paragraph(
                    "<i>Nota: Los cursos con fondo azul claro representan materias con listas cruzadas que se imparten de forma conjunta.</i>",
                    explanation_style
                ))

        # Tabla de cursos actuales si aplica (similar logic for current courses)
        if cursos_actuales and cursos_actuales.exists():
            elementos.append(Spacer(1, 0.3 * inch))
            elementos.append(Paragraph("Actualmente imparte los siguientes cursos:", styles['Texto']))

            # Apply same grouping logic for current courses
            grouped_current = cls.group_courses_by_listas_cruzadas(cursos_actuales)

            # Similar table creation logic as above...
            # (You can apply the same multi-line logic here if needed)

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
        verification_code = cls.generar_codigo_autenticacion(
            nombre_profesor,
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

    @classmethod
    def _generate_pdf_standard(cls, id_docente, courses, template, options, nombre_profesor):
        """Generate PDF using standard ReportLab method with improved page handling"""
        # Separar cursos actuales si se especifica
        periodo_actual = options.get('periodo_actual')
        cursos_actuales = None
        if periodo_actual:
            cursos_actuales = courses.filter(periodo=periodo_actual)
            courses = courses.exclude(periodo=periodo_actual)
        
        # Configurar el documento PDF con márgenes más pequeños para aprovechar mejor el espacio
        from io import BytesIO
        buffer = BytesIO()

        # Use A4 size for better international compatibility and more space
        from reportlab.lib.pagesizes import A4
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,  # Reduced margins
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
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
        elementos.append(Paragraph(nombre_profesor, styles['TextoCentrado']))

        # Group courses by listas_cruzadas
        grouped_courses = cls.group_courses_by_listas_cruzadas(courses)

        if grouped_courses:
            elementos.append(Paragraph("Impartió los siguientes cursos:", styles['Texto']))

            # Preparar datos para la tabla
            campos = options.get('campos',
                                 ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'])
            encabezados = []
            anchos_columna = []

            # Mapeo de campos a encabezados con anchos ajustados para contenido multi-línea
            # Calculate total width based on A4 page width minus margins
            total_width = A4[0] - 100  # 100 = left + right margins
            mapeo_campos = {
                'periodo': ('Periodo', 0.9 * inch),
                'materia': ('Nombre de la Materia', 2.2 * inch),  # Adjusted for better fit
                'clave': ('Clave', 0.9 * inch),
                'nrc': ('NRC', 0.8 * inch),
                'fecha_inicio': ('Fecha Inicio', 0.9 * inch),
                'fecha_fin': ('Fecha Fin', 0.9 * inch),
                'hr_cont': ('Horas Totales', 0.8 * inch)
            }

            for campo in campos:
                if campo in mapeo_campos:
                    encabezados.append(mapeo_campos[campo][0])
                    anchos_columna.append(mapeo_campos[campo][1])

            datos_tabla = [encabezados]

            # Agregar filas con datos agrupados y soporte multi-línea
            for course_data in grouped_courses:
                fila = []
                for campo in campos:
                    if campo == 'periodo':
                        # Always use the already formatted periodo from grouped_courses
                        fila.append(course_data['periodo'])
                    elif campo == 'materia':
                        if course_data['is_grouped'] and isinstance(course_data['materia'], list):
                            # Create Paragraph for multi-line content with proper formatting
                            materia_lines = course_data['materia']
                            if len(materia_lines) <= 3:  # If 3 or fewer lines, show all
                                materia_text = '<br/>'.join(materia_lines)
                            else:  # If more than 3, show first 2 and indicate more
                                shown_lines = materia_lines[:2]
                                remaining = len(materia_lines) - 2
                                materia_text = '<br/>'.join(shown_lines) + f'<br/><i>(+{remaining} más)</i>'

                            # Create a paragraph with smaller font for grouped content
                            para_style = ParagraphStyle(
                                'MultiLineCourse',
                                fontName='Helvetica',
                                fontSize=8,
                                alignment=TA_CENTER,
                                leading=10
                            )
                            fila.append(Paragraph(materia_text, para_style))
                        else:
                            fila.append(course_data['materia'])
                    elif campo == 'clave':
                        if course_data['is_grouped'] and isinstance(course_data['clave'], list):
                            # Always show all claves for grouped courses, even if they're the same
                            clave_text = '<br/>'.join(course_data['clave'])
                            para_style = ParagraphStyle(
                                'MultiLineClave',
                                fontName='Helvetica',
                                fontSize=8,
                                alignment=TA_CENTER,
                                leading=10
                            )
                            fila.append(Paragraph(clave_text, para_style))
                        else:
                            fila.append(course_data['clave'])
                    elif campo == 'nrc':
                        if course_data['is_grouped'] and isinstance(course_data['nrc'], list):
                            nrc_text = '<br/>'.join(course_data['nrc'])
                            para_style = ParagraphStyle(
                                'MultiLineNRC',
                                fontName='Helvetica',
                                fontSize=8,
                                alignment=TA_CENTER,
                                leading=10
                            )
                            fila.append(Paragraph(nrc_text, para_style))
                        else:
                            fila.append(course_data['nrc'])
                    elif campo == 'fecha_inicio':
                        fila.append(course_data['fecha_inicio'].strftime('%d/%m/%Y'))
                    elif campo == 'fecha_fin':
                        fila.append(course_data['fecha_fin'].strftime('%d/%m/%Y'))
                    elif campo == 'hr_cont':
                        if course_data['is_grouped']:
                            # Show total hours with breakdown if grouped
                            total_hrs = course_data['hr_cont']
                            course_count = course_data['course_count']
                            fila.append(f"{total_hrs}\n({course_count} cursos)")
                        else:
                            fila.append(str(course_data['hr_cont']))
                datos_tabla.append(fila)

            # Crear tabla con mejor soporte para contenido multi-línea
            tabla = Table(datos_tabla, colWidths=anchos_columna)
            estilo_tabla = TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # TOP alignment for multi-line content
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),

                # Content styling with better padding for multi-line content
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),

                # Increased padding to accommodate multi-line content
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),

                # Grid and borders
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LINEABOVE', (0, 1), (-1, -1), 0.5, colors.black),
                ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ])

            # Add conditional formatting for grouped rows
            for i, course_data in enumerate(grouped_courses):
                row_index = i + 1  # +1 because row 0 is header
                if course_data['is_grouped']:
                    # Highlight grouped rows with light blue background
                    estilo_tabla.add('BACKGROUND', (0, row_index), (-1, row_index), colors.Color(0.95, 0.98, 1.0))
                    # Increase row height for grouped content
                    estilo_tabla.add('ROWBACKGROUNDS', (0, row_index), (-1, row_index), [colors.Color(0.95, 0.98, 1.0)])

            tabla.setStyle(estilo_tabla)
            elementos.append(tabla)

            # Add explanation for grouped courses if any exist
            if any(course['is_grouped'] for course in grouped_courses):
                elementos.append(Spacer(1, 0.2 * inch))
                explanation_style = ParagraphStyle(
                    'Explanation',
                    fontName='Helvetica-Oblique',
                    fontSize=9,
                    alignment=TA_LEFT,
                    textColor=colors.Color(0.3, 0.3, 0.3)
                )
                elementos.append(Paragraph(
                    "<i>Nota: Los cursos con fondo azul claro representan materias con listas cruzadas que se imparten de forma conjunta.</i>",
                    explanation_style
                ))

        # Tabla de cursos actuales si aplica (similar logic for current courses)
        if cursos_actuales and cursos_actuales.exists():
            elementos.append(Spacer(1, 0.3 * inch))
            elementos.append(Paragraph("Actualmente imparte los siguientes cursos:", styles['Texto']))

            # Apply same grouping logic for current courses
            grouped_current = cls.group_courses_by_listas_cruzadas(cursos_actuales)

            # Create table for current courses (similar to above)
            if grouped_current:
                campos = options.get('campos', ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont'])
                encabezados = []
                anchos_columna = []

                # Mapeo de campos a encabezados
                mapeo_campos = {
                    'periodo': ('Periodo', 0.9 * inch),
                    'materia': ('Nombre de la Materia', 2.2 * inch),
                    'clave': ('Clave', 0.9 * inch),
                    'nrc': ('NRC', 0.8 * inch),
                    'fecha_inicio': ('Fecha Inicio', 0.9 * inch),
                    'fecha_fin': ('Fecha Fin', 0.9 * inch),
                    'hr_cont': ('Horas Totales', 0.8 * inch)
                }

                for campo in campos:
                    if campo in mapeo_campos:
                        encabezados.append(mapeo_campos[campo][0])
                        anchos_columna.append(mapeo_campos[campo][1])

                datos_tabla_actual = [encabezados]

                # Add rows for current courses
                for course_data in grouped_current:
                    fila = []
                    for campo in campos:
                        if campo == 'periodo':
                            fila.append(course_data['periodo'])
                        elif campo == 'materia':
                            if course_data['is_grouped'] and isinstance(course_data['materia'], list):
                                materia_text = '<br/>'.join(course_data['materia'][:3])
                                if len(course_data['materia']) > 3:
                                    materia_text += f'<br/><i>(+{len(course_data["materia"]) - 3} más)</i>'
                                para_style = ParagraphStyle(
                                    'MultiLineCourse',
                                    fontName='Helvetica',
                                    fontSize=8,
                                    alignment=TA_CENTER,
                                    leading=10
                                )
                                fila.append(Paragraph(materia_text, para_style))
                            else:
                                fila.append(course_data['materia'])
                        elif campo == 'clave':
                            if course_data['is_grouped'] and isinstance(course_data['clave'], list):
                                clave_text = '<br/>'.join(course_data['clave'])
                                para_style = ParagraphStyle(
                                    'MultiLineClave',
                                    fontName='Helvetica',
                                    fontSize=8,
                                    alignment=TA_CENTER,
                                    leading=10
                                )
                                fila.append(Paragraph(clave_text, para_style))
                            else:
                                fila.append(course_data['clave'])
                        elif campo == 'nrc':
                            if course_data['is_grouped'] and isinstance(course_data['nrc'], list):
                                nrc_text = '<br/>'.join(course_data['nrc'])
                                para_style = ParagraphStyle(
                                    'MultiLineNRC',
                                    fontName='Helvetica',
                                    fontSize=8,
                                    alignment=TA_CENTER,
                                    leading=10
                                )
                                fila.append(Paragraph(nrc_text, para_style))
                            else:
                                fila.append(course_data['nrc'])
                        elif campo == 'fecha_inicio':
                            fila.append(course_data['fecha_inicio'].strftime('%d/%m/%Y'))
                        elif campo == 'fecha_fin':
                            fila.append(course_data['fecha_fin'].strftime('%d/%m/%Y'))
                        elif campo == 'hr_cont':
                            if course_data['is_grouped']:
                                total_hrs = course_data['hr_cont']
                                course_count = course_data['course_count']
                                fila.append(f"{total_hrs}\n({course_count} cursos)")
                            else:
                                fila.append(str(course_data['hr_cont']))
                    datos_tabla_actual.append(fila)

                # Create table for current courses
                tabla_actual = Table(datos_tabla_actual, colWidths=anchos_columna)
                estilo_tabla_actual = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LINEABOVE', (0, 1), (-1, -1), 0.5, colors.black),
                    ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
                ])

                # Highlight grouped rows
                for i, course_data in enumerate(grouped_current):
                    row_index = i + 1
                    if course_data['is_grouped']:
                        estilo_tabla_actual.add('BACKGROUND', (0, row_index), (-1, row_index), colors.Color(0.95, 0.98, 1.0))

                tabla_actual.setStyle(estilo_tabla_actual)
                elementos.append(tabla_actual)

        # Add more space before closing section to ensure it's on the same page
        elementos.append(Spacer(1, 0.3 * inch))

        # Fecha y cierre
        fecha_actual = datetime.today().strftime('%d de %B de %Y')
        elementos.append(Paragraph("Se expide la presente para los fines legales que el interesado estime necesarios.",
                                   styles['Texto']))
        elementos.append(Spacer(1, 0.2 * inch))
        elementos.append(Paragraph("A T E N T A M E N T E", styles['Firma']))
        elementos.append(Paragraph('"Pensar bien, para vivir mejor"', styles['Firma']))
        elementos.append(Paragraph(f"Puebla, Pue., a {fecha_actual}", styles['Firma']))
        elementos.append(Spacer(1, 0.5 * inch))

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
        verification_code = cls.generar_codigo_autenticacion(
            nombre_profesor,
            fecha_actual,
            id_docente
        )

        if options.get('incluir_qr', True):
            # Add space before QR section
            elementos.append(Spacer(1, 0.3 * inch))
            
            # Create a container for QR and verification text
            qr_container = []
            
            # QR Code
            url_verificacion = options.get('url_verificacion', f"{settings.SITE_URL}/api/certificates/verify/")
            url_completa = f"{url_verificacion}{verification_code}"

            qr = QRCodeFlowable(url_completa, size=1.2 * inch)  # Slightly smaller QR
            qr.hAlign = 'RIGHT'
            qr_container.append(qr)

            # Texto de verificación
            estilo_verificacion = ParagraphStyle(
                name='Verificacion',
                fontName='Helvetica',
                fontSize=8,
                alignment=TA_CENTER
            )
            
            # Add verification text below QR
            qr_container.append(Spacer(1, 0.1 * inch))
            qr_container.append(Paragraph("Verifique la autenticidad de este documento en:", estilo_verificacion))
            qr_container.append(Paragraph(f"{url_verificacion}", estilo_verificacion))
            qr_container.append(Paragraph(f"Código de verificación: {verification_code}", estilo_verificacion))
            
            # Add the QR container to main elements
            elementos.extend(qr_container)

        # Generar PDF - ReportLab will automatically handle page breaks
        doc.build(elementos)
        buffer.seek(0)

        # Crear archivo de contenido
        pdf_content = ContentFile(buffer.getvalue())
        buffer.close()

        return pdf_content, verification_code
