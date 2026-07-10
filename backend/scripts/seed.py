"""Seed the super admin user and the default service categories.

Idempotent: running it multiple times will not create duplicates. Admin
credentials come from environment variables, never hard-coded in source.

Usage:  python -m scripts.seed
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.catalog import ServiceCategory  # noqa: E402
from app.models.enums import UserRole, AuthProvider  # noqa: E402
from app.models.user import AuthIdentity, User  # noqa: E402
from app.security import hash_password  # noqa: E402

# (slug, name_th, name_en, requires_certification)
DEFAULT_CATEGORIES = [
    ("car-repair", "ช่างซ่อมรถยนต์", "Car Repair", False),
    ("motorcycle-repair", "ช่างซ่อมรถจักรยานยนต์", "Motorcycle Repair", False),
    ("car-battery", "แบตเตอรี่รถยนต์", "Car Battery", False),
    ("tires", "ยางรถยนต์และรถจักรยานยนต์", "Tires", False),
    ("towing", "รถยกและรถลาก", "Towing", False),
    ("electrician", "ช่างไฟฟ้า", "Electrician", True),
    ("plumber", "ช่างประปา", "Plumber", False),
    ("air-conditioner", "ช่างแอร์", "Air Conditioner", False),
    ("appliance-repair", "ช่างเครื่องใช้ไฟฟ้า", "Appliance Repair", False),
    ("locksmith", "ช่างกุญแจ", "Locksmith", False),
    ("glass", "ช่างกระจก", "Glazier", False),
    ("aluminum", "ช่างอะลูมิเนียม", "Aluminum Work", False),
    ("carpenter", "ช่างไม้", "Carpenter", False),
    ("furniture", "ช่างเฟอร์นิเจอร์", "Furniture", False),
    ("masonry", "ช่างก่อ ฉาบ และปูน", "Masonry", False),
    ("painting", "ช่างทาสี", "Painting", False),
    ("roofing", "ช่างหลังคา", "Roofing", False),
    ("tiling", "ช่างปูกระเบื้อง", "Tiling", False),
    ("handyman", "ช่างจิปาถะ", "Handyman", False),
    ("home-extension", "งานต่อเติมบ้าน", "Home Extension", False),
    ("renovation", "งานรีโนเวต", "Renovation", False),
    ("housekeeping", "แม่บ้าน", "Housekeeping", False),
    ("big-cleaning", "Big Cleaning", "Big Cleaning", False),
    ("sofa-carpet-cleaning", "ล้างโซฟาและพรม", "Sofa & Carpet Cleaning", False),
    ("gardening", "ดูแลสวน", "Gardening", False),
    ("lawn-mowing", "ตัดหญ้า", "Lawn Mowing", False),
    ("tree-trimming", "ตัดแต่งต้นไม้", "Tree Trimming", False),
    ("pest-control", "กำจัดปลวกและแมลง", "Pest Control", False),
    ("water-tank-cleaning", "ล้างถังน้ำ", "Water Tank Cleaning", False),
    ("solar-cleaning", "ล้างโซลาร์เซลล์", "Solar Panel Cleaning", False),
    ("cctv", "กล้องวงจรปิด", "CCTV", False),
    ("internet-wifi", "อินเทอร์เน็ตและ Wi-Fi", "Internet & Wi-Fi", False),
    ("smart-home", "Smart Home", "Smart Home", False),
]


def seed_admin(db) -> None:
    existing = db.query(User).filter(User.email == settings.SEED_ADMIN_EMAIL).first()
    if existing:
        print(f"[seed] super admin already exists: {settings.SEED_ADMIN_EMAIL}")
        return
    admin = User(
        email=settings.SEED_ADMIN_EMAIL,
        email_verified=True,
        password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
        full_name=settings.SEED_ADMIN_NAME,
        display_name=settings.SEED_ADMIN_NAME,
        role=UserRole.super_admin.value,
        onboarding_completed=True,
    )
    db.add(admin)
    db.flush()
    db.add(
        AuthIdentity(
            user_id=admin.id,
            provider=AuthProvider.password.value,
            provider_user_id=settings.SEED_ADMIN_EMAIL,
            provider_email=settings.SEED_ADMIN_EMAIL,
        )
    )
    print(f"[seed] created super admin: {settings.SEED_ADMIN_EMAIL}")


def seed_categories(db) -> None:
    created = 0
    for order, (slug, name_th, name_en, cert) in enumerate(DEFAULT_CATEGORIES):
        if db.query(ServiceCategory).filter(ServiceCategory.slug == slug).first():
            continue
        db.add(
            ServiceCategory(
                slug=slug,
                name_th=name_th,
                name_en=name_en,
                sort_order=order,
                is_active=True,
                requires_certification=cert,
            )
        )
        created += 1
    print(f"[seed] created {created} service categories")


def main() -> None:
    db = SessionLocal()
    try:
        seed_admin(db)
        seed_categories(db)
        db.commit()
        print("[seed] done")
    finally:
        db.close()


if __name__ == "__main__":
    main()
