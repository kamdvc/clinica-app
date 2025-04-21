# Sistema Clínico - Facultad de Ciencias Médicas

Sistema de gestión clínica para la Facultad de Ciencias Médicas de la Universidad de San Carlos de Guatemala.

## Características

- Registro y autenticación de usuarios
- Gestión de pacientes
- Registro de signos vitales
- Gestión de consultas médicas
- Asignación de clínicas
- Generación de reportes

## Tecnologías

- Backend: Python (Flask)
- Base de datos: MySQL
- Frontend: HTML, CSS, JavaScript, Bootstrap

## Estructura del Proyecto

```
clinica_/
├── app/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   ├── templates/
│   ├── models.py
│   ├── routes.py
│   └── __init__.py
├── config.py
├── requirements.txt
└── run.py
```

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual: `python -m venv venv`
3. Activar el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Configurar la base de datos MySQL
6. Ejecutar la aplicación: `python run.py`