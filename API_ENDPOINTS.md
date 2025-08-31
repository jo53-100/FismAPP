# 🎓 API de Certificados FCFM - Endpoints Públicos

Esta documentación describe los endpoints públicos de la API de certificados que **NO requieren autenticación**. Estos endpoints están diseñados para ser simples y fáciles de usar.

## 🚀 Endpoints Disponibles

### 1. 📋 Información de la API
**GET** `/api/certificates/api-info/`

Obtiene información completa sobre todos los endpoints disponibles y ejemplos de uso.

**Respuesta:**
```json
{
  "success": true,
  "message": "API de Certificados FCFM - Endpoints Públicos",
  "endpoints": {
    "request_certificate": {
      "url": "/api/certificates/request-public/",
      "method": "POST",
      "description": "Solicitar un certificado",
      "required_fields": ["id_docente"],
      "optional_fields": ["template_id", "destinatario", "periodos_filtro", "periodo_actual", "incluir_qr"]
    }
  }
}
```

### 2. 👥 Lista de Profesores
**GET** `/api/certificates/professors-public/`

Obtiene la lista de todos los profesores disponibles en el sistema con información básica.

**Respuesta:**
```json
{
  "success": true,
  "count": 2,
  "professors": [
    {
      "id_docente": "100224988",
      "name": "Dr. Juan Pérez",
      "course_count": 15,
      "latest_period": "202535"
    }
  ]
}
```

### 3. 📄 Plantillas Disponibles
**GET** `/api/certificates/templates-public/`

Obtiene la lista de plantillas de certificado disponibles.

**Respuesta:**
```json
{
  "success": true,
  "count": 1,
  "templates": [
    {
      "id": 1,
      "name": "Plantilla Estándar",
      "description": "Plantilla predeterminada para certificados",
      "layout_type": "standard",
      "is_default": true
    }
  ]
}
```

### 4. 📜 Solicitar Certificado
**POST** `/api/certificates/request-public/`

Genera un nuevo certificado para un profesor específico.

**Campos requeridos:**
- `id_docente`: ID único del profesor en el sistema

**Campos opcionales:**
- `template_id`: ID de la plantilla a usar (usa la predeterminada si no se especifica)
- `destinatario`: Destinatario del certificado (default: "A QUIEN CORRESPONDA")
- `periodos_filtro`: Lista de períodos específicos (ej: "202525,202535")
- `periodo_actual`: Período actual para separar
- `incluir_qr`: Si incluir código QR de verificación (default: true)

**Ejemplo de solicitud:**
```json
{
  "id_docente": "100224988",
  "destinatario": "A QUIEN CORRESPONDA",
  "incluir_qr": true
}
```

**Respuesta exitosa (201):**
```json
{
  "success": true,
  "message": "Certificado generado exitosamente para Dr. Juan Pérez",
  "certificate": {
    "id": 1,
    "verification_code": "abc123def456...",
    "professor_name": "Dr. Juan Pérez",
    "id_docente": "100224988",
    "template_name": "Plantilla Estándar",
    "file_url": "/media/generated_certificates/certificate_100224988_abc123.pdf",
    "generated_at": "2025-01-15T10:30:00Z",
    "verification_url": "/api/certificates/verify-public/?code=abc123def456..."
  }
}
```

### 5. 🔍 Verificar Certificado
**GET** `/api/certificates/verify-public/?code=VERIFICATION_CODE`

Verifica la autenticidad de un certificado usando su código de verificación.

**Parámetros:**
- `code`: Código de verificación del certificado

**Ejemplo de URL:**
```
/api/certificates/verify-public/?code=abc123def456...
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "valid": true,
  "message": "Certificado válido",
  "certificate": {
    "id": 1,
    "verification_code": "abc123def456...",
    "professor_name": "Dr. Juan Pérez",
    "id_docente": "100224988",
    "template_name": "Plantilla Estándar",
    "generated_at": "2025-01-15T10:30:00Z",
    "file_url": "/media/generated_certificates/certificate_100224988_abc123.pdf",
    "metadata": {
      "id_docente": "100224988",
      "destinatario": "A QUIEN CORRESPONDA",
      "incluir_qr": true
    }
  }
}
```

**Respuesta de certificado no encontrado (404):**
```json
{
  "success": false,
  "valid": false,
  "message": "Certificado no encontrado o código inválido",
  "verification_code": "invalid_code"
}
```

## 🧪 Ejemplos de Uso

### cURL

#### 1. Solicitar un Certificado
```bash
curl -X POST http://localhost:8000/api/certificates/request-public/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_docente": "100224988",
    "destinatario": "A QUIEN CORRESPONDA",
    "incluir_qr": true
  }'
```

#### 2. Verificar un Certificado
```bash
curl "http://localhost:8000/api/certificates/verify-public/?code=abc123def456..."
```

#### 3. Listar Profesores
```bash
curl "http://localhost:8000/api/certificates/professors-public/"
```

#### 4. Listar Plantillas
```bash
curl "http://localhost:8000/api/certificates/templates-public/"
```

### JavaScript (Fetch API)

#### 1. Solicitar un Certificado
```javascript
const response = await fetch('/api/certificates/request-public/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    id_docente: '100224988',
    destinatario: 'A QUIEN CORRESPONDA',
    incluir_qr: true
  })
});

const data = await response.json();
console.log('Certificado generado:', data.certificate);
```

#### 2. Verificar un Certificado
```javascript
const verificationCode = 'abc123def456...';
const response = await fetch(`/api/certificates/verify-public/?code=${verificationCode}`);
const data = await response.json();

if (data.valid) {
  console.log('Certificado válido:', data.certificate);
} else {
  console.log('Certificado inválido:', data.message);
}
```

### Python (requests)

#### 1. Solicitar un Certificado
```python
import requests

response = requests.post('http://localhost:8000/api/certificates/request-public/', json={
    'id_docente': '100224988',
    'destinatario': 'A QUIEN CORRESPONDA',
    'incluir_qr': True
})

if response.status_code == 201:
    data = response.json()
    print(f"Certificado generado: {data['certificate']['verification_code']}")
else:
    print(f"Error: {response.text}")
```

#### 2. Verificar un Certificado
```python
import requests

verification_code = 'abc123def456...'
response = requests.get(f'http://localhost:8000/api/certificates/verify-public/?code={verification_code}')

if response.status_code == 200:
    data = response.json()
    if data['valid']:
        print(f"Certificado válido para: {data['certificate']['professor_name']}")
    else:
        print("Certificado inválido")
else:
    print(f"Error: {response.text}")
```

## 📱 Demo Interactivo

Para probar los endpoints de forma interactiva, visita:
```
http://localhost:8000/static/api_demo.html
```

Esta página HTML te permite:
- Ver información de la API
- Listar profesores y plantillas
- Solicitar certificados
- Verificar certificados
- Ver ejemplos de código

## 🔧 Flujo de Trabajo Típico

1. **Obtener lista de profesores** → `/professors-public/`
2. **Obtener lista de plantillas** → `/templates-public/`
3. **Solicitar certificado** → `/request-public/` (POST)
4. **Guardar el código de verificación** del certificado generado
5. **Verificar certificado** → `/verify-public/?code=VERIFICATION_CODE`

## ⚠️ Notas Importantes

- **No se requiere autenticación** para estos endpoints
- Todos los endpoints devuelven respuestas en formato JSON
- Los códigos de verificación son únicos y seguros
- Los certificados se generan como archivos PDF
- Los archivos se almacenan en `/media/generated_certificates/`
- Las URLs de archivos son relativas al dominio del servidor

## 🚨 Códigos de Estado HTTP

- **200**: Solicitud exitosa (GET)
- **201**: Recurso creado exitosamente (POST)
- **400**: Error en la solicitud (datos inválidos)
- **404**: Recurso no encontrado
- **500**: Error interno del servidor

## 📞 Soporte

Si tienes problemas con la API:
1. Verifica que el servidor esté ejecutándose
2. Revisa los logs del servidor Django
3. Asegúrate de que los datos enviados sean válidos
4. Verifica que el profesor exista en el sistema
