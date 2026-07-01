-- PASO 1: Ver qué existe actualmente
SELECT 
    f.id AS finca_id,
    f.nombre AS finca,
    s.id AS silo_id,
    s.codigo,
    s.nombre AS silo,
    sen.id AS sensor_id,
    sen.device_id,
    sen.api_key,
    sen.activo AS sensor_activo
FROM fincas f
LEFT JOIN silos s ON s.finca_id = f.id
LEFT JOIN sensores sen ON sen.silo_id = s.id
ORDER BY f.nombre, s.codigo;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 2 (solo si faltan sensores en algún silo):
-- Reemplazá SILO_ID_AQUI con el id real del silo sin sensor.
-- Repetí el bloque por cada silo que falte.
-- ─────────────────────────────────────────────────────────────────────────────

-- INSERT INTO sensores (silo_id, device_id, api_key, modelo, fecha_instalacion)
-- VALUES (
--     SILO_ID_AQUI,
--     'ESP32-SILO-0X',
--     encode(gen_random_bytes(24), 'hex'),
--     'DYP-A01-V2.0',
--     CURRENT_DATE
-- )
-- RETURNING id, silo_id, device_id, api_key;

-- ─────────────────────────────────────────────────────────────────────────────
-- PASO 3: Confirmar estado final
-- ─────────────────────────────────────────────────────────────────────────────
-- SELECT s.id AS silo_id, s.nombre, sen.id AS sensor_id, sen.device_id
-- FROM silos s
-- JOIN sensores sen ON sen.silo_id = s.id
-- ORDER BY s.codigo;
