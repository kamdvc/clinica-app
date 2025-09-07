-- Agregar campos de motivo de consulta
ALTER TABLE consulta ADD COLUMN motivo_consulta TEXT;
ALTER TABLE consulta ADD COLUMN historia_enfermedad TEXT;
ALTER TABLE consulta ADD COLUMN revision_sistemas TEXT;

-- Agregar campos de antecedentes gineco-obstetricos
ALTER TABLE consulta ADD COLUMN gestas VARCHAR(10);
ALTER TABLE consulta ADD COLUMN partos VARCHAR(10);
ALTER TABLE consulta ADD COLUMN abortos VARCHAR(10);
ALTER TABLE consulta ADD COLUMN hijos_vivos VARCHAR(10);
ALTER TABLE consulta ADD COLUMN hijos_muertos VARCHAR(10);
ALTER TABLE consulta ADD COLUMN fecha_ultima_regla DATE;
ALTER TABLE consulta ADD COLUMN antecedentes TEXT;

-- Agregar campos de examen físico
ALTER TABLE consulta ADD COLUMN presion_arterial VARCHAR(20);
ALTER TABLE consulta ADD COLUMN frecuencia_respiratoria VARCHAR(10);
ALTER TABLE consulta ADD COLUMN temperatura VARCHAR(10);
ALTER TABLE consulta ADD COLUMN peso VARCHAR(10);
ALTER TABLE consulta ADD COLUMN talla VARCHAR(10);
ALTER TABLE consulta ADD COLUMN frecuencia_cardiaca VARCHAR(10);
ALTER TABLE consulta ADD COLUMN saturacion_oxigeno VARCHAR(10);
ALTER TABLE consulta ADD COLUMN imc VARCHAR(10); 