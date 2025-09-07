-- Migración para agregar el campo estado a la tabla consulta
-- Fecha: 2025-01-07

-- Agregar la columna estado con valor por defecto 'en_progreso'
ALTER TABLE consulta ADD COLUMN estado VARCHAR(20) DEFAULT 'en_progreso';

-- Actualizar las consultas existentes que ya tienen diagnóstico y tratamiento como completadas
UPDATE consulta 
SET estado = 'completada' 
WHERE diagnostico IS NOT NULL 
AND diagnostico != '' 
AND tratamiento IS NOT NULL 
AND tratamiento != '';

-- Actualizar las consultas que no tienen diagnóstico o tratamiento como en progreso
UPDATE consulta 
SET estado = 'en_progreso' 
WHERE estado IS NULL 
OR (diagnostico IS NULL OR diagnostico = '') 
OR (tratamiento IS NULL OR tratamiento = '');

