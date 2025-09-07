#!/usr/bin/env python3
"""
Script para crear pacientes ficticios con historiales médicos completos
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.abspath('.'))

from app import create_app, db
from app.models import Usuario, Paciente, Consulta, SignosVitales, Clinica
from werkzeug.security import generate_password_hash

def crear_datos_ficticios():
    """Crear pacientes ficticios con historiales médicos completos"""
    
    app = create_app()
    
    with app.app_context():
        print("🏥 Creando datos ficticios para la clínica...")
        
        # Crear médicos ficticios si no existen
        crear_medicos_ficticios()
        
        # Crear pacientes ficticios
        paciente_masculino = crear_paciente_masculino()
        paciente_femenino = crear_paciente_femenino()
        
        # Crear historiales médicos completos
        crear_historial_paciente_masculino(paciente_masculino)
        crear_historial_paciente_femenino(paciente_femenino)
        
        # Confirmar cambios
        db.session.commit()
        print("✅ Datos ficticios creados exitosamente!")
        print("\n📋 Pacientes creados para pruebas:")
        print(f"👨 Paciente masculino: {paciente_masculino.nombre_completo} (DNI: {paciente_masculino.dni})")
        print(f"👩 Paciente femenino: {paciente_femenino.nombre_completo} (DNI: {paciente_femenino.dni})")
        print("\n🔍 Puedes buscarlos por nombre o DNI en el sistema")

def crear_medicos_ficticios():
    """Crear médicos ficticios para las consultas"""
    
    medicos_data = [
        {
            'nombre_completo': 'Dr. Carlos Mendoza',
            'usuario': 'cmendoza',
            'email': 'cmendoza@clinica.com',
            'rol': 'medico'
        },
        {
            'nombre_completo': 'Dra. Ana Patricia Ruiz',
            'usuario': 'apruiz',
            'email': 'apruiz@clinica.com', 
            'rol': 'medico'
        },
        {
            'nombre_completo': 'Dr. Roberto Silva',
            'usuario': 'rsilva',
            'email': 'rsilva@clinica.com',
            'rol': 'medico'
        }
    ]
    
    for medico_data in medicos_data:
        # Verificar si el médico ya existe
        medico_existente = Usuario.query.filter_by(usuario=medico_data['usuario']).first()
        if not medico_existente:
            medico = Usuario(
                nombre_completo=medico_data['nombre_completo'],
                usuario=medico_data['usuario'],
                email=medico_data['email'],
                password_hash=generate_password_hash('medico123'),
                rol=medico_data['rol'],
                activo=True
            )
            db.session.add(medico)
            print(f"👨‍⚕️ Médico creado: {medico_data['nombre_completo']}")

def crear_paciente_masculino():
    """Crear paciente masculino ficticio"""
    
    # Verificar si ya existe
    paciente_existente = Paciente.query.filter_by(dni='12345678').first()
    if paciente_existente:
        print(f"👨 Paciente masculino ya existe: {paciente_existente.nombre_completo}")
        return paciente_existente
    
    paciente = Paciente(
        nombre_completo='Carlos Eduardo González Martínez',
        edad=45,
        sexo='Masculino',
        dni='12345678',
        direccion='Colonia San Benito, Calle Las Flores #123, San Salvador',
        telefono='2234-5678',
        estado_civil='Casado',
        religion='Católica',
        escolaridad='Universitaria',
        ocupacion='Ingeniero Civil',
        procedencia='San Salvador',
        numero_expediente='EXP-2024-001',
        fecha_nacimiento=datetime(1979, 3, 15).date(),
        expediente=True
    )
    
    db.session.add(paciente)
    db.session.flush()  # Para obtener el ID
    print(f"👨 Paciente masculino creado: {paciente.nombre_completo}")
    return paciente

def crear_paciente_femenino():
    """Crear paciente femenino ficticio"""
    
    # Verificar si ya existe
    paciente_existente = Paciente.query.filter_by(dni='87654321').first()
    if paciente_existente:
        print(f"👩 Paciente femenino ya existe: {paciente_existente.nombre_completo}")
        return paciente_existente
    
    paciente = Paciente(
        nombre_completo='María José Hernández López',
        edad=32,
        sexo='Femenino',
        dni='87654321',
        direccion='Residencial Los Alamos, Pasaje 2, Casa #45, Antiguo Cuscatlán',
        telefono='2765-4321',
        estado_civil='Soltera',
        religion='Católica',
        escolaridad='Técnica',
        ocupacion='Enfermera',
        procedencia='La Libertad',
        numero_expediente='EXP-2024-002',
        fecha_nacimiento=datetime(1992, 8, 22).date(),
        expediente=True
    )
    
    db.session.add(paciente)
    db.session.flush()  # Para obtener el ID
    print(f"👩 Paciente femenino creado: {paciente.nombre_completo}")
    return paciente

def crear_historial_paciente_masculino(paciente):
    """Crear historial médico completo para el paciente masculino"""
    
    print(f"📋 Creando historial médico para {paciente.nombre_completo}...")
    
    # Obtener médicos y clínica
    medicos = Usuario.query.filter_by(rol='medico').all()
    clinica = Clinica.query.first()
    
    if not medicos or not clinica:
        print("⚠️ No hay médicos o clínicas disponibles")
        return
    
    # Consulta 1: Primera consulta - Hipertensión (hace 6 meses)
    fecha_consulta1 = datetime.now() - timedelta(days=180)
    consulta1 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Primera consulta',
        clinica_id=clinica.id,
        medico_id=medicos[0].id,
        fecha_consulta=fecha_consulta1,
        motivo_consulta='Dolor de cabeza frecuente y mareos ocasionales. Refiere que los episodios han aumentado en frecuencia en las últimas 3 semanas.',
        historia_enfermedad='Paciente masculino de 45 años que consulta por cefalea frontal pulsátil de 3 semanas de evolución, asociada a mareos ocasionales, especialmente al levantarse. Niega náuseas, vómitos o alteraciones visuales. Refiere episodios de estrés laboral reciente.',
        revision_sistemas='Cabeza: cefalea frontal. Cardiovascular: palpitaciones ocasionales. Neurológico: mareos posturales. Resto de sistemas sin alteraciones.',
        antecedentes='Padre con hipertensión arterial. Madre diabética. No refiere alergias conocidas. Fumador social (5 cigarrillos/día). Consume alcohol ocasionalmente.',
        # Examen físico
        presion_arterial='160/95',
        frecuencia_respiratoria='18',
        temperatura='36.8',
        peso='85',
        talla='175',
        frecuencia_cardiaca='78',
        saturacion_oxigeno='98',
        imc='27.8',
        diagnostico='Hipertensión arterial etapa 1. Cefalea tensional secundaria a hipertensión.',
        tratamiento='Enalapril 10mg vía oral cada 12 horas. Modificaciones del estilo de vida: reducir consumo de sal, aumentar actividad física, control del estrés. Control en 2 semanas.'
    )
    db.session.add(consulta1)
    db.session.flush()
    
    # Signos vitales consulta 1
    signos1 = SignosVitales(
        presion_arterial='160/95',
        frecuencia_cardiaca=78,
        frecuencia_respiratoria=18,
        temperatura=36.8,
        saturacion=98,
        glucosa=110,
        consulta_id=consulta1.id,
        fecha_registro=fecha_consulta1
    )
    db.session.add(signos1)
    
    # Consulta 2: Seguimiento - Control de hipertensión (hace 4 meses)
    fecha_consulta2 = datetime.now() - timedelta(days=120)
    consulta2 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Seguimiento',
        clinica_id=clinica.id,
        medico_id=medicos[1].id,
        fecha_consulta=fecha_consulta2,
        motivo_consulta='Control de presión arterial. Paciente refiere mejoría de los episodios de cefalea.',
        historia_enfermedad='Paciente en tratamiento con Enalapril 10mg c/12h desde hace 2 meses. Refiere disminución significativa de la cefalea. Ha implementado cambios en la dieta y ejercicio regular (caminata 30 min, 3 veces por semana).',
        revision_sistemas='Cardiovascular: sin palpitaciones. Neurológico: cefalea ocasional, menos intensa. Digestivo: sin molestias. Resto sin alteraciones.',
        antecedentes='Igual que consulta anterior. Ha reducido el tabaquismo a 2-3 cigarrillos por día.',
        presion_arterial='142/88',
        frecuencia_respiratoria='16',
        temperatura='36.5',
        peso='83',
        talla='175',
        frecuencia_cardiaca='72',
        saturacion_oxigeno='99',
        imc='27.1',
        diagnostico='Hipertensión arterial en control parcial. Adherencia al tratamiento adecuada.',
        tratamiento='Continuar Enalapril 10mg c/12h. Aumentar dosis a 15mg c/12h. Continuar modificaciones del estilo de vida. Control en 1 mes.'
    )
    db.session.add(consulta2)
    db.session.flush()
    
    signos2 = SignosVitales(
        presion_arterial='142/88',
        frecuencia_cardiaca=72,
        frecuencia_respiratoria=16,
        temperatura=36.5,
        saturacion=99,
        glucosa=105,
        consulta_id=consulta2.id,
        fecha_registro=fecha_consulta2
    )
    db.session.add(signos2)
    
    # Consulta 3: Consulta por gripe (hace 2 meses)
    fecha_consulta3 = datetime.now() - timedelta(days=60)
    consulta3 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Consulta aguda',
        clinica_id=clinica.id,
        medico_id=medicos[2].id,
        fecha_consulta=fecha_consulta3,
        motivo_consulta='Fiebre, tos y malestar general de 2 días de evolución.',
        historia_enfermedad='Cuadro agudo de 48 horas de evolución caracterizado por fiebre hasta 38.5°C, tos seca, rinorrea, odinofagia y malestar general. Niega disnea o dolor torácico. Exposición a familiar con síntomas similares.',
        revision_sistemas='Respiratorio: tos seca, rinorrea. Orofaringe: hiperemia. Resto sin alteraciones significativas.',
        antecedentes='Hipertensión arterial en tratamiento con Enalapril 15mg c/12h.',
        presion_arterial='138/85',
        frecuencia_respiratoria='20',
        temperatura='38.2',
        peso='83',
        talla='175',
        frecuencia_cardiaca='85',
        saturacion_oxigeno='97',
        imc='27.1',
        diagnostico='Infección viral de vías respiratorias superiores (resfriado común).',
        tratamiento='Paracetamol 500mg c/8h PRN fiebre. Abundantes líquidos. Reposo relativo. Continuar antihipertensivo. Regresar si empeora o no mejora en 5 días.'
    )
    db.session.add(consulta3)
    db.session.flush()
    
    signos3 = SignosVitales(
        presion_arterial='138/85',
        frecuencia_cardiaca=85,
        frecuencia_respiratoria=20,
        temperatura=38.2,
        saturacion=97,
        glucosa=108,
        consulta_id=consulta3.id,
        fecha_registro=fecha_consulta3
    )
    db.session.add(signos3)
    
    # Consulta 4: Control reciente (hace 2 semanas)
    fecha_consulta4 = datetime.now() - timedelta(days=14)
    consulta4 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Seguimiento',
        clinica_id=clinica.id,
        medico_id=medicos[0].id,
        fecha_consulta=fecha_consulta4,
        motivo_consulta='Control de presión arterial y evaluación general.',
        historia_enfermedad='Paciente con buen control de presión arterial. Ha mantenido cambios en el estilo de vida. Ejercicio regular, dieta baja en sal. Se recuperó completamente del episodio viral. Sin cefaleas.',
        revision_sistemas='Cardiovascular: sin síntomas. Neurológico: sin cefaleas. General: se siente bien, energético.',
        antecedentes='Hipertensión arterial en tratamiento. Ha dejado completamente el tabaquismo hace 1 mes.',
        presion_arterial='128/82',
        frecuencia_respiratoria='16',
        temperatura='36.6',
        peso='81',
        talla='175',
        frecuencia_cardiaca='68',
        saturacion_oxigeno='99',
        imc='26.4',
        diagnostico='Hipertensión arterial controlada. Estado general excelente.',
        tratamiento='Continuar Enalapril 15mg c/12h. Mantener estilo de vida saludable. Felicitaciones por dejar el tabaco. Control en 3 meses.'
    )
    db.session.add(consulta4)
    db.session.flush()
    
    signos4 = SignosVitales(
        presion_arterial='128/82',
        frecuencia_cardiaca=68,
        frecuencia_respiratoria=16,
        temperatura=36.6,
        saturacion=99,
        glucosa=95,
        consulta_id=consulta4.id,
        fecha_registro=fecha_consulta4
    )
    db.session.add(signos4)
    
    print(f"✅ Historial médico creado para {paciente.nombre_completo} (4 consultas)")

def crear_historial_paciente_femenino(paciente):
    """Crear historial médico completo para el paciente femenino"""
    
    print(f"📋 Creando historial médico para {paciente.nombre_completo}...")
    
    # Obtener médicos y clínica
    medicos = Usuario.query.filter_by(rol='medico').all()
    clinica = Clinica.query.first()
    
    if not medicos or not clinica:
        print("⚠️ No hay médicos o clínicas disponibles")
        return
    
    # Consulta 1: Primera consulta ginecológica (hace 8 meses)
    fecha_consulta1 = datetime.now() - timedelta(days=240)
    consulta1 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Primera consulta',
        clinica_id=clinica.id,
        medico_id=medicos[1].id,  # Dra. Ana Patricia
        fecha_consulta=fecha_consulta1,
        motivo_consulta='Control ginecológico anual y planificación familiar.',
        historia_enfermedad='Paciente femenina de 32 años, soltera, sexualmente activa, consulta para control ginecológico de rutina. Refiere ciclos menstruales regulares, sin dismenorrea significativa. Interesada en métodos anticonceptivos.',
        revision_sistemas='Ginecológico: ciclos regulares 28-30 días, duración 5 días, cantidad normal. Mamas: sin masas palpables. Resto sin alteraciones.',
        antecedentes='Menarca a los 13 años. Nunca embarazada (G0P0). Sin antecedentes de ITS. Última citología hace 2 años (normal). Madre con cáncer de mama a los 55 años.',
        # Antecedentes gineco-obstétricos
        gestas='0',
        partos='0', 
        abortos='0',
        hijos_vivos='0',
        hijos_muertos='0',
        fecha_ultima_regla=(datetime.now() - timedelta(days=15)).date(),
        presion_arterial='110/70',
        frecuencia_respiratoria='16',
        temperatura='36.4',
        peso='58',
        talla='162',
        frecuencia_cardiaca='72',
        saturacion_oxigeno='99',
        imc='22.1',
        diagnostico='Mujer joven sana. Control ginecológico normal.',
        tratamiento='Anticonceptivos orales (Etinilestradiol/Levonorgestrel). Citología cervical. Control en 6 meses. Autoexamen de mamas mensual.'
    )
    db.session.add(consulta1)
    db.session.flush()
    
    signos1 = SignosVitales(
        presion_arterial='110/70',
        frecuencia_cardiaca=72,
        frecuencia_respiratoria=16,
        temperatura=36.4,
        saturacion=99,
        glucosa=85,
        consulta_id=consulta1.id,
        fecha_registro=fecha_consulta1
    )
    db.session.add(signos1)
    
    # Consulta 2: Infección urinaria (hace 5 meses)
    fecha_consulta2 = datetime.now() - timedelta(days=150)
    consulta2 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Consulta aguda',
        clinica_id=clinica.id,
        medico_id=medicos[2].id,  # Dr. Roberto
        fecha_consulta=fecha_consulta2,
        motivo_consulta='Disuria, urgencia miccional y dolor suprapúbico de 2 días de evolución.',
        historia_enfermedad='Cuadro de 48 horas caracterizado por disuria, polaquiuria, urgencia miccional y dolor suprapúbico. Niega fiebre, náuseas o dolor lumbar. Orina de aspecto turbio.',
        revision_sistemas='Genitourinario: disuria, polaquiuria, urgencia. Sin fiebre ni escalofríos. Resto sin alteraciones.',
        antecedentes='En tratamiento con anticonceptivos orales. Sin antecedentes de ITU recurrentes.',
        presion_arterial='115/75',
        frecuencia_respiratoria='18',
        temperatura='36.8',
        peso='59',
        talla='162',
        frecuencia_cardiaca='78',
        saturacion_oxigeno='98',
        imc='22.5',
        diagnostico='Infección del tracto urinario no complicada (cistitis aguda).',
        tratamiento='Nitrofurantoína 100mg c/6h por 7 días. Abundantes líquidos. Orinar después de relaciones sexuales. Urocultivo de control post-tratamiento.'
    )
    db.session.add(consulta2)
    db.session.flush()
    
    signos2 = SignosVitales(
        presion_arterial='115/75',
        frecuencia_cardiaca=78,
        frecuencia_respiratoria=18,
        temperatura=36.8,
        saturacion=98,
        glucosa=88,
        consulta_id=consulta2.id,
        fecha_registro=fecha_consulta2
    )
    db.session.add(signos2)
    
    # Consulta 3: Seguimiento ginecológico (hace 3 meses)
    fecha_consulta3 = datetime.now() - timedelta(days=90)
    consulta3 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Seguimiento',
        clinica_id=clinica.id,
        medico_id=medicos[1].id,  # Dra. Ana Patricia
        fecha_consulta=fecha_consulta3,
        motivo_consulta='Control ginecológico y resultados de citología.',
        historia_enfermedad='Paciente asintomática, viene a control ginecológico programado. Tolera bien anticonceptivos orales. Ciclos regulares. Se recuperó completamente de ITU.',
        revision_sistemas='Ginecológico: sin molestias, ciclos regulares. Genitourinario: sin síntomas urinarios. Mamas: sin cambios.',
        antecedentes='ITU resuelta completamente. Continúa con anticonceptivos orales sin efectos adversos.',
        gestas='0',
        partos='0',
        abortos='0',
        hijos_vivos='0',
        hijos_muertos='0',
        fecha_ultima_regla=(datetime.now() - timedelta(days=105)).date(),
        presion_arterial='108/68',
        frecuencia_respiratoria='16',
        temperatura='36.3',
        peso='58',
        talla='162',
        frecuencia_cardiaca='70',
        saturacion_oxigeno='99',
        imc='22.1',
        diagnostico='Mujer joven sana. Citología cervical normal. Control ginecológico satisfactorio.',
        tratamiento='Continuar anticonceptivos orales. Suplemento de ácido fólico 400mcg/día. Control anual de rutina.'
    )
    db.session.add(consulta3)
    db.session.flush()
    
    signos3 = SignosVitales(
        presion_arterial='108/68',
        frecuencia_cardiaca=70,
        frecuencia_respiratoria=16,
        temperatura=36.3,
        saturacion=99,
        glucosa=82,
        consulta_id=consulta3.id,
        fecha_registro=fecha_consulta3
    )
    db.session.add(signos3)
    
    # Consulta 4: Ansiedad y estrés laboral (hace 1 mes)
    fecha_consulta4 = datetime.now() - timedelta(days=30)
    consulta4 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Consulta general',
        clinica_id=clinica.id,
        medico_id=medicos[0].id,  # Dr. Carlos
        fecha_consulta=fecha_consulta4,
        motivo_consulta='Episodios de ansiedad, insomnio y estrés relacionado con el trabajo.',
        historia_enfermedad='Paciente refiere aumento del estrés laboral en las últimas 6 semanas debido a cambio de unidad hospitalaria. Presenta episodios de ansiedad, dificultad para conciliar el sueño, palpitaciones ocasionales sin causa aparente.',
        revision_sistemas='Neurológico: ansiedad, insomnio inicial. Cardiovascular: palpitaciones ocasionales. Digestivo: pérdida del apetito ocasional.',
        antecedentes='Sin antecedentes psiquiátricos previos. Personalidad perfeccionista. Buena red de apoyo familiar.',
        presion_arterial='118/78',
        frecuencia_respiratoria='18',
        temperatura='36.5',
        peso='56',
        talla='162',
        frecuencia_cardiaca='82',
        saturacion_oxigeno='98',
        imc='21.3',
        diagnostico='Trastorno adaptativo con ansiedad. Estrés laboral agudo.',
        tratamiento='Técnicas de relajación y manejo del estrés. Ejercicio regular. Higiene del sueño. Evaluación psicológica si persisten síntomas. Control en 2 semanas.'
    )
    db.session.add(consulta4)
    db.session.flush()
    
    signos4 = SignosVitales(
        presion_arterial='118/78',
        frecuencia_cardiaca=82,
        frecuencia_respiratoria=18,
        temperatura=36.5,
        saturacion=98,
        glucosa=90,
        consulta_id=consulta4.id,
        fecha_registro=fecha_consulta4
    )
    db.session.add(signos4)
    
    # Consulta 5: Seguimiento de ansiedad (hace 1 semana)
    fecha_consulta5 = datetime.now() - timedelta(days=7)
    consulta5 = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Seguimiento',
        clinica_id=clinica.id,
        medico_id=medicos[0].id,  # Dr. Carlos
        fecha_consulta=fecha_consulta5,
        motivo_consulta='Control de seguimiento por episodios de ansiedad.',
        historia_enfermedad='Paciente ha implementado técnicas de relajación y ejercicio regular. Refiere mejoría significativa del insomnio y reducción de episodios de ansiedad. Ha iniciado yoga y ha establecido mejor balance trabajo-vida personal.',
        revision_sistemas='Neurológico: mejoría del sueño, ansiedad controlada. Cardiovascular: sin palpitaciones recientes. Estado general: se siente mejor.',
        antecedentes='Episodio de estrés laboral agudo en resolución.',
        presion_arterial='112/72',
        frecuencia_respiratoria='16',
        temperatura='36.4',
        peso='57',
        talla='162',
        frecuencia_cardiaca='74',
        saturacion_oxigeno='99',
        imc='21.7',
        diagnostico='Trastorno adaptativo con ansiedad en resolución. Buen manejo del estrés.',
        tratamiento='Continuar técnicas de relajación y ejercicio. Mantener balance trabajo-vida. Control en 1 mes o PRN síntomas.'
    )
    db.session.add(consulta5)
    db.session.flush()
    
    signos5 = SignosVitales(
        presion_arterial='112/72',
        frecuencia_cardiaca=74,
        frecuencia_respiratoria=16,
        temperatura=36.4,
        saturacion=99,
        glucosa=87,
        consulta_id=consulta5.id,
        fecha_registro=fecha_consulta5
    )
    db.session.add(signos5)
    
    print(f"✅ Historial médico creado para {paciente.nombre_completo} (5 consultas)")

if __name__ == '__main__':
    crear_datos_ficticios()