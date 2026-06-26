-- Migración: agrega autenticación por API key a nivel de dispositivo
-- Ejecutar después de schema.sql
-- Nota: se agrega como nullable primero por seguridad (si ya hay sensores
-- cargados, no truena el ALTER). Si la tabla todavía está vacía, los tres
-- pasos igual corren sin problema.

ALTER TABLE sensores ADD COLUMN api_key VARCHAR(64) UNIQUE;

-- backfill manual: generar una key por cada sensor existente antes del siguiente paso
-- ejemplo: UPDATE sensores SET api_key = encode(gen_random_bytes(24), 'hex') WHERE api_key IS NULL;

ALTER TABLE sensores ALTER COLUMN api_key SET NOT NULL;
