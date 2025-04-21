from app import create_app, db
from app.models import Clinica

# Este script revierte los cambios realizados por modificar_clinicas.py
# y restaura todas las clínicas que existían originalmente

app = create_app()
with app.app_context():
    # Verificar cuántas clínicas hay actualmente
    clinicas = Clinica.query.all()
    print(f"Actualmente hay {len(clinicas)} clínicas en el sistema:")
    for c in clinicas:
        print(f"ID: {c.id}, Nombre: {c.nombre}, Disponible: {c.disponible}")
    
    # Restaurar todas las clínicas a su estado original
    # Primero, asegurarse de que las clínicas 1 y 2 existen
    if len(clinicas) < 2:
        nombres = ['Clínica 1', 'Clínica 2']
        for i in range(len(clinicas), 2):
            nueva_clinica = Clinica(nombre=nombres[i], disponible=True)
            db.session.add(nueva_clinica)
            print(f"Creando clínica: {nombres[i]}")
    
    # Ya no creamos clínicas adicionales, solo mantenemos las 2 primeras
    # Eliminamos cualquier clínica adicional que pueda existir
    clinicas_adicionales = Clinica.query.filter(Clinica.id > 2).all()
    for clinica in clinicas_adicionales:
        print(f"Eliminando clínica adicional: {clinica.nombre}")
        db.session.delete(clinica)
    
    db.session.commit()
    print("\nClínicas restauradas correctamente.")
    
    # Mostrar las clínicas actuales
    clinicas_actualizadas = Clinica.query.all()
    print("\nClínicas actuales en el sistema:")
    for c in clinicas_actualizadas:
        print(f"ID: {c.id}, Nombre: {c.nombre}, Disponible: {c.disponible}")