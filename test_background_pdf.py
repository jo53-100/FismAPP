#!/usr/bin/env python3
"""
Test script to verify background PDF functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/galen/PycharmProjects/FismAPP')

# Set Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'faculty_project.settings')
django.setup()

from certificates.models import CertificateTemplate, CoursesHistory
from certificates.services import CertificateService

def test_background_pdf():
    """Test certificate generation with background PDF"""
    print("🧪 Testing Background PDF Certificate Generation...")
    
    # Get the default template
    template = CertificateTemplate.objects.filter(is_default=True).first()
    if not template:
        print("❌ No default template found")
        return
    
    print(f"✅ Using template: {template.name}")
    print(f"📄 Background PDF: {template.background_pdf}")
    
    # Get a professor with courses
    course = CoursesHistory.objects.first()
    if not course:
        print("❌ No courses found")
        return
    
    id_docente = course.id_docente
    courses = CoursesHistory.objects.filter(id_docente=id_docente)
    
    print(f"👨‍🏫 Professor: {course.profesor}")
    print(f"📚 Courses found: {courses.count()}")
    
    # Test options
    options = {
        'id_docente': id_docente,
        'destinatario': 'A QUIEN CORRESPONDA (TEST)',
        'incluir_qr': True,
        'campos': ['periodo', 'materia', 'clave', 'nrc', 'fecha_inicio', 'fecha_fin', 'hr_cont']
    }
    
    try:
        # Generate certificate
        print("\n🔄 Generating certificate...")
        pdf_content, verification_code = CertificateService.generate_pdf(
            id_docente=id_docente,
            courses=courses,
            template=template,
            options=options
        )
        
        print(f"✅ Certificate generated successfully!")
        print(f"🔑 Verification code: {verification_code[:8]}...")
        print(f"📊 PDF size: {len(pdf_content.read())} bytes")
        
        # Save test file
        test_filename = f"test_certificate_background_{verification_code[:8]}.pdf"
        with open(test_filename, 'wb') as f:
            pdf_content.seek(0)
            f.write(pdf_content.read())
        
        print(f"💾 Test certificate saved as: {test_filename}")
        
    except Exception as e:
        print(f"❌ Error generating certificate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_background_pdf()

