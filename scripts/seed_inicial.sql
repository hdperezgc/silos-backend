-- Carga inicial: 1 finca, 3 silos piloto (dimensiones reales del SP-0248-1),
-- y 1 sensor por silo con su api_key generada automáticamente.
--
-- ÚNICO valor que tenés que cambiar antes de correr esto: el nombre de la finca,
-- en la primera línea del WITH. Reemplazá REEMPLAZAR_NOMBRE_FINCA por el nombre
-- real (ej. Amatitlan) - sin dejar ningún símbolo extra alrededor.

WITH nueva_finca AS (
    INSERT INTO fincas (nombre)
    VALUES ('REEMPLAZAR_NOMBRE_FINCA')
    RETURNING id
),
silo_1 AS (
    INSERT INTO silos (
        finca_id, codigo, nombre, diametro_m, altura_total_m,
        altura_cono_m, altura_cilindro_m, angulo_cono_grados,
        altura_zona_ciega_cm, capacidad_kg, densidad_alimento_kg_m3
    )
    SELECT id, 'SILO-01', 'Silo 1', 2.48, 4.45, 2.15, 1.19, 60, 28, 7400, 804
    FROM nueva_finca
    RETURNING id, codigo
),
silo_2 AS (
    INSERT INTO silos (
        finca_id, codigo, nombre, diametro_m, altura_total_m,
        altura_cono_m, altura_cilindro_m, angulo_cono_grados,
        altura_zona_ciega_cm, capacidad_kg, densidad_alimento_kg_m3
    )
    SELECT id, 'SILO-02', 'Silo 2', 2.48, 4.45, 2.15, 1.19, 60, 28, 7400, 804
    FROM nueva_finca
    RETURNING id, codigo
),
silo_3 AS (
    INSERT INTO silos (
        finca_id, codigo, nombre, diametro_m, altura_total_m,
        altura_cono_m, altura_cilindro_m, angulo_cono_grados,
        altura_zona_ciega_cm, capacidad_kg, densidad_alimento_kg_m3
    )
    SELECT id, 'SILO-03', 'Silo 3', 2.48, 4.45, 2.15, 1.19, 60, 28, 7400, 804
    FROM nueva_finca
    RETURNING id, codigo
),
sensor_1 AS (
    INSERT INTO sensores (silo_id, device_id, api_key, modelo, fecha_instalacion)
    SELECT id, 'ESP32-SILO-01', encode(gen_random_bytes(24), 'hex'), 'DYP-A01-V2.0', CURRENT_DATE
    FROM silo_1
    RETURNING silo_id, device_id, api_key
),
sensor_2 AS (
    INSERT INTO sensores (silo_id, device_id, api_key, modelo, fecha_instalacion)
    SELECT id, 'ESP32-SILO-02', encode(gen_random_bytes(24), 'hex'), 'DYP-A01-V2.0', CURRENT_DATE
    FROM silo_2
    RETURNING silo_id, device_id, api_key
),
sensor_3 AS (
    INSERT INTO sensores (silo_id, device_id, api_key, modelo, fecha_instalacion)
    SELECT id, 'ESP32-SILO-03', encode(gen_random_bytes(24), 'hex'), 'DYP-A01-V2.0', CURRENT_DATE
    FROM silo_3
    RETURNING silo_id, device_id, api_key
)
SELECT * FROM sensor_1
UNION ALL
SELECT * FROM sensor_2
UNION ALL
SELECT * FROM sensor_3;

-- IMPORTANTE: copiá y guardá los api_key que te devuelve esta consulta en un
-- lugar seguro (gestor de contraseñas, no un chat) - son los que vas a
-- programar en cada ESP32 para que pueda autenticarse al mandar lecturas.
-- Esta consulta no los vuelve a mostrar después de corrida.
