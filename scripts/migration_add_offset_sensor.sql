-- Agrega silos.offset_sensor_cm: distancia horizontal (cm) entre el eje
-- central del silo y la posición real del sensor. NULL o 0 = sensor centrado.
--
-- create_all() al arrancar NO agrega columnas a tablas que ya existen, así
-- que esto se corre a mano una vez en cada base (producción y staging) ANTES
-- de desplegar el backend nuevo. Sin la columna, cualquier endpoint que lea
-- silos falla con error 500.

ALTER TABLE silos
    ADD COLUMN IF NOT EXISTS offset_sensor_cm NUMERIC(6, 2);

-- Ejemplo para el silo real (sensor a 135 cm del eje central):
-- UPDATE silos SET offset_sensor_cm = 135 WHERE codigo = 'CODIGO_DEL_SILO';
