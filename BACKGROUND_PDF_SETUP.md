# Background PDF Setup for Certificates

This document explains how to set up and use the background PDF functionality for generating certificates with custom backgrounds.

## Overview

The certificate system now supports using a background PDF template that will be overlaid with the certificate content. This allows you to use pre-designed letterhead or certificate backgrounds while maintaining all the existing functionality for course tables, QR codes, and verification.

## Features

- ✅ **Background PDF Support**: Use any PDF as a background template
- ✅ **Content Overlay**: Certificate content is overlaid on top of the background
- ✅ **Fallback Support**: If background PDF fails, falls back to standard generation
- ✅ **Maintains All Features**: Course tables, QR codes, signatures, etc. remain unchanged
- ✅ **Admin Interface**: Easy setup through Django admin

## Setup Instructions

### 1. Prepare Your Background PDF

Place your background PDF file in the `media/certificate_pdf_templates/` directory. The system will automatically detect and use it.

**Recommended Background PDF:**
- Use the "Hoja membretada.pdf" file that's already in your media folder
- Ensure the PDF is single-page (first page will be used as template)
- Use A4 or Letter size for best compatibility

### 2. Configure Certificate Template

1. **Access Django Admin**: Go to `/admin/certificates/certificatetemplate/`
2. **Select Template**: Choose the template you want to use (or create a new one)
3. **Upload Background PDF**: In the "Images and Backgrounds" section, upload your background PDF
4. **Save Template**: Save the template

### 3. Set as Default (Optional)

If you want this template to be used by default:
1. In the admin list view, select your template
2. Use the "Make template default" action
3. Or set `is_default = True` in the template form

## How It Works

### Background PDF Processing

1. **Content Generation**: First, the certificate content is generated as a separate PDF using ReportLab
2. **PDF Overlay**: The content PDF is then overlaid on top of your background PDF using PyPDF2
3. **Final Output**: The result is a single PDF with your background and the certificate content

### Fallback Mechanism

If the background PDF overlay fails for any reason:
- The system automatically falls back to standard certificate generation
- An error message is logged
- The certificate is still generated successfully

### Technical Details

- **Library**: Uses PyPDF2 for PDF manipulation
- **Format**: Supports any PDF format as background
- **Size**: Automatically handles different page sizes
- **Content**: All certificate elements (tables, text, QR codes) are preserved

## Usage Examples

### Command Line

```bash
# Generate certificate with background PDF
python manage.py generate_certificate "100224988" --template 1

# The system will automatically use the background PDF if configured
```

### API Usage

```python
# The API automatically detects and uses background PDFs
from certificates.services import CertificateService

pdf_content, verification_code = CertificateService.generate_pdf(
    id_docente="100224988",
    courses=courses,
    template=template,
    options=options
)
```

### Programmatic Usage

```python
# Check if template has background PDF
if template.background_pdf:
    print("Template uses background PDF:", template.background_pdf.name)
else:
    print("Template uses standard generation")
```

## File Structure

```
media/
├── certificate_pdf_templates/          # Background PDFs go here
│   └── Hoja membretada.pdf           # Your background template
├── certificate_logos/                 # Logo images
├── certificate_signatures/            # Signature images
├── certificate_backgrounds/           # Background images (legacy)
└── generated_certificates/            # Generated certificates
```

## Troubleshooting

### Common Issues

1. **Background PDF Not Working**
   - Check if PyPDF2 is installed: `pip install PyPDF2`
   - Verify the PDF file is valid and not corrupted
   - Ensure the PDF is accessible in the media directory

2. **Fallback to Standard Generation**
   - Check Django logs for error messages
   - Verify file permissions on the background PDF
   - Ensure the PDF path is correct in the template

3. **Large File Sizes**
   - Optimize your background PDF (compress images, remove unnecessary elements)
   - Consider using vector graphics for better quality and smaller size

### Debug Mode

To see detailed information about background PDF processing:

```python
# In Django shell
from certificates.services import CertificateService
import logging
logging.basicConfig(level=logging.DEBUG)

# Generate certificate and watch for debug output
```

## Best Practices

1. **PDF Quality**: Use high-quality, vector-based PDFs when possible
2. **File Size**: Keep background PDFs under 5MB for optimal performance
3. **Testing**: Always test with sample data before using in production
4. **Backup**: Keep backup copies of your background PDFs
5. **Version Control**: Consider versioning your background PDFs

## Migration Notes

- **Existing Templates**: Continue to work unchanged
- **New Field**: `background_pdf` field added to CertificateTemplate model
- **Backward Compatible**: All existing functionality preserved
- **Admin Interface**: Enhanced with background PDF upload capability

## Support

If you encounter issues:

1. Check the Django logs for error messages
2. Verify the background PDF file is valid
3. Test with a simple PDF first
4. Ensure PyPDF2 is properly installed
5. Check file permissions and paths

The system is designed to be robust and will always generate certificates even if the background PDF feature fails.

