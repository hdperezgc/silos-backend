-- Crear el primer usuario admin.
-- Correr esto en el SQL Editor de Neon (o cualquier cliente conectado a tu DB).
-- Reemplazá los 3 valores marcados con <<<>>> antes de ejecutar.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

INSERT INTO usuarios (nombre, email, password_hash, rol, activo)
VALUES (
    '<<<TU NOMBRE>>>',
    '<<<tu_email@tudominio.com>>>',
    crypt('<<<TU_CONTRASEÑA>>>', gen_salt('bf')),
    'admin'::rol_usuario,
    true
);

-- Verificación: confirma que se creó (sin mostrar el hash completo)
SELECT id, nombre, email, rol, activo FROM usuarios WHERE email = '<<<tu_email@tudominio.com>>>';
