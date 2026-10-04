from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Organization, User, UserRole


def seed_admin_user() -> None:
    if not settings.seed_admin_email or not settings.seed_admin_password:
        return

    email = settings.seed_admin_email.lower().strip()
    organization_name = settings.seed_admin_organization.strip()
    full_name = settings.seed_admin_full_name.strip() or "Administrador"

    with SessionLocal() as db:
        organization = db.scalar(select(Organization).where(Organization.name == organization_name))
        if not organization:
            organization = Organization(name=organization_name, country_code="BR")
            db.add(organization)
            db.flush()

        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                organization_id=organization.id,
                email=email,
                full_name=full_name,
                password_hash=hash_password(settings.seed_admin_password),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(user)
        else:
            user.organization_id = organization.id
            user.full_name = full_name
            user.password_hash = hash_password(settings.seed_admin_password)
            user.role = UserRole.admin
            user.is_active = True

        db.commit()
