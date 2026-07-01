"""
Crea el primer usuario admin en la base de datos.
Correr DESDE la carpeta granjazul-backend, con el entorno virtual activado
y el archivo .env apuntando a tu Neon real:

    python scripts/create_admin.py

Pide el email y la contraseña por consola - no los escribas en ningún
archivo ni los compartas en chat.
"""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import RolUsuario, Usuario
from app.security import hash_password


def main():
    nombre = input("Nombre completo: ").strip()
    email = input("Email: ").strip().lower()
    password = getpass.getpass("Contraseña (no se muestra al escribir): ")
    password_confirm = getpass.getpass("Confirmá la contraseña: ")

    if password != password_confirm:
        print("Las contraseñas no coinciden. Corré el script de nuevo.")
        sys.exit(1)

    if len(password) < 8:
        print("Usá una contraseña de al menos 8 caracteres.")
        sys.exit(1)

    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.email == email).first()
        if existente:
            print(f"Ya existe un usuario con ese email (id={existente.id}).")
            sys.exit(1)

        usuario = Usuario(
            nombre=nombre,
            email=email,
            password_hash=hash_password(password),
            rol=RolUsuario.admin,
            activo=True,
        )
        db.add(usuario)
        db.commit()
        print(f"Usuario admin creado: {email} (id={usuario.id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
