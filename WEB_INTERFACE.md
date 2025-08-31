# 🌐 Interfaz Web - Sistema de Certificados FCFM

## 🎯 Descripción

He creado una interfaz web simple y elegante que permite a los profesores solicitar y verificar certificados directamente desde su navegador, sin necesidad de autenticación.

## 🚀 URLs Disponibles

### Página Principal
```
http://localhost:8000/certificates/
```
- Landing page con enlaces a solicitar y verificar certificados
- Diseño moderno y responsive
- Información del sistema

### Solicitar Certificado
```
http://localhost:8000/certificates/request/
```
- Formulario simple con solo 3 campos:
  - **ID del Docente** (requerido)
  - **Destinatario** (requerido, con valor por defecto)
  - **Períodos Académicos** (opcional)
- Genera certificado inmediatamente
- Muestra código de verificación
- Enlace de descarga del PDF

### Verificar Certificado
```
http://localhost:8000/certificates/verify/
```
- Formulario para verificar autenticidad
- Solo requiere el código de verificación
- Muestra detalles completos del certificado
- Confirma validez o invalidez

## 📋 Campos del Formulario

### Solicitar Certificado
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| ID del Docente | Texto | ✅ | ID único del profesor (ej: 100224988) |
| Destinatario | Texto | ✅ | A quién se dirige (default: "A QUIEN CORRESPONDA") |
| Períodos Académicos | Texto | ❌ | Períodos separados por comas (ej: 202525,202535) |

### Verificar Certificado
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| Código de Verificación | Texto | ✅ | Código único del certificado |

## 🎨 Características de la Interfaz

### Diseño
- **Moderno y limpio** - Gradientes y sombras suaves
- **Responsive** - Funciona en móviles y tablets
- **Accesible** - Colores contrastantes y texto claro
- **Intuitivo** - Navegación simple y clara

### Funcionalidad
- **Sin autenticación** - Acceso directo sin registro
- **Validación en tiempo real** - Errores claros y específicos
- **Estados de carga** - Feedback visual durante las operaciones
- **Resultados claros** - Éxito y error bien diferenciados

### Experiencia de Usuario
- **Auto-focus** en el primer campo
- **Ejemplos** para cada campo
- **Mensajes de ayuda** contextuales
- **Navegación entre páginas** fácil

## 🔧 Cómo Usar

### Para Profesores

1. **Acceder al sistema**
   ```
   http://localhost:8000/certificates/
   ```

2. **Solicitar certificado**
   - Hacer clic en "Solicitar Certificado"
   - Ingresar ID de docente
   - Opcionalmente especificar períodos
   - Hacer clic en "Generar Certificado"

3. **Verificar certificado**
   - Hacer clic en "Verificar Certificado"
   - Pegar el código de verificación
   - Hacer clic en "Verificar Certificado"

### Para Administradores

- **Monitoreo** - Los certificados se guardan en la base de datos
- **Logs** - Errores registrados en los logs de Django
- **Archivos** - PDFs guardados en `/media/generated_certificates/`

## 📱 Compatibilidad

- ✅ **Chrome/Chromium** - Funciona perfectamente
- ✅ **Firefox** - Compatible
- ✅ **Safari** - Compatible
- ✅ **Edge** - Compatible
- ✅ **Móviles** - Diseño responsive
- ✅ **Tablets** - Optimizado

## 🚨 Notas Importantes

### Requisitos del Servidor
- Django server ejecutándose
- Base de datos con profesores cargados
- Plantillas de certificado configuradas
- Media files configurados

### Seguridad
- **Sin autenticación** - Cualquiera puede usar la interfaz
- **Validación** - Solo profesores existentes pueden generar certificados
- **Verificación** - Códigos únicos y seguros
- **Logs** - Todas las operaciones quedan registradas

### Limitaciones
- Solo funciona con profesores que tengan cursos en el sistema
- Requiere conexión a internet para generar PDFs
- Los archivos se almacenan localmente

## 🎯 Flujo Típico de Usuario

1. **Profesor accede** → `http://localhost:8000/certificates/`
2. **Hace clic en "Solicitar Certificado"**
3. **Llena el formulario** con su ID y destinatario
4. **Recibe certificado** con código de verificación
5. **Comparte código** para verificación
6. **Otros verifican** usando el código

## 💡 Próximos Pasos

1. **Probar la interfaz** con datos reales
2. **Personalizar colores** según la marca FCFM
3. **Agregar validaciones** adicionales si es necesario
4. **Implementar notificaciones** por email
5. **Agregar estadísticas** de uso

¡La interfaz está lista para usar! 🎉
