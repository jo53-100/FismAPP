# AppFCFM
Aplicación FCFM
Versión ALPHA
# Instalación

clonen el repositorio como dios les de a entender y sigan estas instrucciones en la terminal:

## activa el entorno virtual (`.venv`):
### Linux/MacOS:
```
python -m venv .venv
source .venv/bin/activate
```
### Windows:
```
python -m venv .venv
.venv\Scripts\activate
```
## Instala las dependencias:
```
pip install -r requirements.txt
```
## Establece la base de datos:
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
Sigue las instrucciones para crear un superusuario, un perfil con acceso a todo el backend. Te pedirá que escribas una contraseña y parecerá que no estás escribiendo nada, pero sí se está escribiendo solo que no aparece...

## Corre el servidor de desarrollo
```
python manage.py runserver
```

La API estará disponible como 
http://localhost:8000
el panel de admin:

http://localhost:8000/admin
