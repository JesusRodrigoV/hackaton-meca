import argparse
import getpass
import sys
from datetime import datetime, timezone

from email_validator import EmailNotValidError, validate_email

from app.core.password_policy import validate_password_strength_func
from app.core.security import get_password_hash
from app.crud import role as crud_role
from app.crud import user as crud_user
from app.db.session import SessionLocal


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the initial administrator user for Enseña por Bolivia."
    )
    parser.add_argument("--email", required=True, help="Administrator email")
    parser.add_argument(
        "--full-name",
        default="Administrador General",
        help="Administrator full name",
    )
    parser.add_argument(
        "--password",
        help="Password. If omitted, it is requested interactively.",
    )
    return parser.parse_args()


def _read_password(password: str | None) -> str:
    if password:
        return password
    first = getpass.getpass("Password: ")
    second = getpass.getpass("Repeat password: ")
    if first != second:
        raise ValueError("Las contraseñas no coinciden")
    return first


def main() -> int:
    args = _parse_args()
    try:
        email = validate_email(args.email, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        print(f"Error: correo inválido: {exc}", file=sys.stderr)
        return 1

    if not args.full_name.strip():
        print("Error: el nombre completo es obligatorio", file=sys.stderr)
        return 1

    try:
        password = _read_password(args.password)
        validate_password_strength_func(password)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        admin_role = crud_role.get_role_by_name(db, "Administrador")
        if not admin_role:
            print(
                "Error: el rol Administrador no existe. "
                "Ejecuta primero 'uv run alembic upgrade head'.",
                file=sys.stderr,
            )
            return 1

        email = crud_user.normalize_email(email)
        if crud_user.get_user_by_email(db, email):
            print(f"Error: ya existe un usuario con el correo {email}", file=sys.stderr)
            return 1

        user = crud_user.create_user(
            db,
            email=email,
            full_name=args.full_name,
            password_hash=get_password_hash(password),
            is_active=True,
            must_change_password=False,
        )
        user.password_changed_at = datetime.now(timezone.utc)
        crud_user.set_user_roles(db, user, [admin_role])
        db.commit()
        print(f"Administrador creado: {user.email} (id={user.id})")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"Error creando el administrador: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())