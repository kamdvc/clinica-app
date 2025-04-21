from app import create_app, db
from app.models import Clinica

# Este script modifica la base de datos para mostrar solo 2 clínicas

app = create_app()
with app.app_context():
    # Verificar cuántas clínicas hay actualmente
    clinicas = Clinica.query.all()
    print(f"Actualmente hay {len(clinicas)} clínicas en el sistema:")
    for c in clinicas:
        print(f"ID: {c.id}, Nombre: {c.nombre}, Disponible: {c.disponible}")
    
    # Si hay más de 2 clínicas, eliminar las adicionales
    if len(clinicas) > 2:
        # Mantener solo las primeras 2 clínicas
        clinicas_a_eliminar = clinicas[2:]
        for clinica in clinicas_a_eliminar:
            print(f"Eliminando clínica: {clinica.nombre}")
            db.session.delete(clinica)
        
        db.session.commit()
        print("\nClínicas eliminadas correctamente.")
    elif len(clinicas) < 2:
        # Si hay menos de 2 clínicas, crear las necesarias
        nombres = ['Clínica 1', 'Clínica 2']
        for i in range(len(clinicas), 2):
            nueva_clinica = Clinica(nombre=nombres[i], disponible=True)
            db.session.add(nueva_clinica)
            print(f"Creando clínica: {nombres[i]}")
        
        db.session.commit()
        print("\nClínicas creadas correctamente.")
    else:
        print("\nYa hay exactamente 2 clínicas en el sistema. No se requieren cambios.")
    
    # Mostrar las clínicas actuales
    clinicas_actualizadas = Clinica.query.all()
    print("\nClínicas actuales en el sistema:")
    for c in clinicas_actualizadas:
        print(f"ID: {c.id}, Nombre: {c.nombre}, Disponible: {c.disponible}")