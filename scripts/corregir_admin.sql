-- Corrige el usuario admin que quedó con los símbolos <<< >>> incluidos
-- por error en el email, nombre y contraseña.
-- Reemplazá los 3 valores de abajo con los reales, SIN los símbolos < y >.

UPDATE usuarios
SET
    nombre = 'Hector Perez',
    email = 'hdperez@grupocresta.com.gt',
    password_hash = crypt('TU_CONTRASEÑA_REAL_AQUI', gen_salt('bf'))
WHERE id = 1;

-- Verificación: el email no debe tener < ni > al inicio o final
SELECT id, nombre, email, length(email) AS largo_email FROM usuarios WHERE id = 1;
