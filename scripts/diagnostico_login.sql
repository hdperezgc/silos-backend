-- Diagnóstico de login. Correr en el SQL Editor de Neon.

-- 1. Confirmar que el usuario existe y revisar el email EXACTO guardado
--    (ojo con mayúsculas/minúsculas o espacios, son comunes los typos acá)
SELECT id, nombre, email, rol, activo, length(email) AS largo_email
FROM usuarios;

-- 2. Probar si tu contraseña coincide con el hash guardado.
--    Reemplazá <<<EMAIL_EXACTO>>> y <<<CONTRASEÑA_QUE_ESTAS_PROBANDO>>>.
--    Si devuelve TRUE, la contraseña es correcta y el problema es el email
--    (o algo en cómo el backend está leyendo el dato).
--    Si devuelve FALSE, la contraseña no es la que quedó guardada.
SELECT
    email,
    password_hash = crypt('<<<CONTRASEÑA_QUE_ESTAS_PROBANDO>>>', password_hash) AS contraseña_coincide
FROM usuarios
WHERE email = '<<<EMAIL_EXACTO>>>';
