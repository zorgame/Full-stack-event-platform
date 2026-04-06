import argparse
import sys
from pathlib import Path


# Permite ejecutar este script por ruta directa sin fallar con "No module named app".
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models  # noqa: F401 - ensures SQLAlchemy models are registered
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.usuarios import Usuarios
from app.schemas.usuarios import UsuarioCreate
from app.utils.security import generar_hash_password


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap or promote an admin user for a fresh environment.",
    )
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--nombre", default="Admin", help="Admin first name")
    parser.add_argument("--apellido", default="Principal", help="Admin last name")
    parser.add_argument("--pais", default="DO", help="Admin country code/name")
    parser.add_argument("--telefono", default=None, help="Admin phone")
    parser.add_argument(
        "--reset-password-if-exists",
        action="store_true",
        help="Reset password if the user already exists.",
    )
    parser.add_argument(
        "--skip-create-schema",
        action="store_true",
        help="Skip schema creation (Base.metadata.create_all).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    email = str(args.email or "").strip().lower()

    try:
        payload = UsuarioCreate(
            email=email,
            password=args.password,
            nombre=args.nombre,
            apellido=args.apellido,
            pais=args.pais,
            telefono=args.telefono,
            is_admin=True,
        )
    except Exception as exc:
        print(f"ERROR: invalid input data: {exc}", file=sys.stderr)
        return 1

    if not args.skip_create_schema:
        Base.metadata.create_all(bind=engine)
        print("Schema verified/created successfully.")

    db = SessionLocal()
    try:
        existing = db.query(Usuarios).filter(Usuarios.email == payload.email).first()

        if existing is None:
            usuario = Usuarios(
                email=payload.email,
                telefono=payload.telefono,
                nombre=payload.nombre,
                apellido=payload.apellido,
                pais=payload.pais,
                hashed_password=generar_hash_password(payload.password),
                is_active=True,
                is_admin=True,
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
            print(f"Admin user created successfully. user_id={usuario.id} email={usuario.email}")
            return 0

        changes = False

        if not existing.is_active:
            existing.is_active = True
            changes = True

        if not existing.is_admin:
            existing.is_admin = True
            changes = True

        if args.reset_password_if_exists:
            existing.hashed_password = generar_hash_password(payload.password)
            changes = True

        if not existing.nombre and payload.nombre:
            existing.nombre = payload.nombre
            changes = True

        if not existing.apellido and payload.apellido:
            existing.apellido = payload.apellido
            changes = True

        if not existing.pais and payload.pais:
            existing.pais = payload.pais
            changes = True

        if not existing.telefono and payload.telefono:
            existing.telefono = payload.telefono
            changes = True

        if changes:
            db.add(existing)
            db.commit()
            db.refresh(existing)
            print(f"Existing user promoted/updated as admin. user_id={existing.id} email={existing.email}")
        else:
            print(f"Existing admin already up to date. user_id={existing.id} email={existing.email}")

        return 0
    except Exception as exc:
        db.rollback()
        print(f"ERROR: could not bootstrap admin user: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
