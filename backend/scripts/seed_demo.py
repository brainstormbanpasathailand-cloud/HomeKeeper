"""Seed realistic demo data so the platform looks like it is in real use.

Creates: a super admin, customers with properties/assets, approved technicians
with skills, and jobs across several statuses — including one fully completed
job that flows through the real completion logic so a Home Health Record +
Warranty are generated, plus a review.

Idempotent: if the demo customer already exists it does nothing. To reset demo
data, drop/recreate the database (or delete the demo users) and re-run.

Usage:  python -m scripts.seed_demo

All demo accounts share the password below — change or delete them before any
real launch.
"""
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.enums import (  # noqa: E402
    AssignmentStatus,
    AuthProvider,
    AvailabilityStatus,
    JobStatus,
    MediaKind,
    OnlineStatus,
    PartAuthenticity,
    QuotationStatus,
    Urgency,
    UserRole,
    VerificationStatus,
)
from app.models.catalog import ServiceCategory  # noqa: E402
from app.models.job import JobAssignment, JobMedia, JobRequest  # noqa: E402
from app.models.misc import Review  # noqa: E402
from app.models.property import Asset, Property  # noqa: E402
from app.models.quotation import Part, Quotation  # noqa: E402
from app.models.technician import TechnicianProfile, TechnicianServiceCategory  # noqa: E402
from app.models.user import AuthIdentity, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services.jobs import change_status, generate_job_number  # noqa: E402
from scripts.seed import seed_admin, seed_categories  # noqa: E402

DEMO_PASSWORD = "Demo123456"
DEMO_MARKER_EMAIL = "somchai@demo.homekeeper"


def now() -> datetime:
    return datetime.now(timezone.utc)


def make_user(db, *, email, name, role, phone, province, district) -> User:
    user = User(
        email=email,
        email_verified=True,
        phone=phone,
        phone_verified=True,
        password_hash=hash_password(DEMO_PASSWORD),
        full_name=name,
        display_name=name,
        role=role,
        language="th",
        province=province,
        district=district,
        onboarding_completed=True,
        last_login_at=now(),
    )
    db.add(user)
    db.flush()
    db.add(
        AuthIdentity(
            user_id=user.id,
            provider=AuthProvider.password.value,
            provider_user_id=email,
            provider_email=email,
            last_login_at=now(),
        )
    )
    return user


def cat(db, slug: str) -> ServiceCategory:
    return db.query(ServiceCategory).filter(ServiceCategory.slug == slug).first()


def make_technician(db, user: User, admin_id: int, *, lat, lng, radius, exp, rating, jobs_done, bio, category_slugs):
    profile = TechnicianProfile(
        user_id=user.id,
        legal_name=user.full_name,
        display_name=user.display_name,
        phone_verified=True,
        email_verified=True,
        province=user.province,
        district=user.district,
        latitude=lat,
        longitude=lng,
        location_updated_at=now(),
        service_radius_km=radius,
        years_of_experience=exp,
        languages=["th", "en"],
        bio=bio,
        verification_status=VerificationStatus.approved.value,
        average_rating=rating,
        completed_jobs=jobs_done,
        acceptance_rate=0.95,
        cancellation_rate=0.02,
        online_status=OnlineStatus.online.value,
        availability_status=AvailabilityStatus.available.value,
        approved_at=now(),
        approved_by=admin_id,
    )
    db.add(profile)
    db.flush()
    for slug in category_slugs:
        c = cat(db, slug)
        if c:
            db.add(
                TechnicianServiceCategory(
                    technician_id=profile.id,
                    service_category_id=c.id,
                    skill_level="expert",
                    min_call_fee=300,
                    accepts_emergency=True,
                    accepts_scheduled=True,
                )
            )
    return profile


def make_job(db, *, customer, category_slug, title, problem, urgency, status,
             property_id=None, asset_id=None, technician_id=None):
    c = cat(db, category_slug)
    job = JobRequest(
        job_number=generate_job_number(db),
        customer_id=customer.id,
        property_id=property_id,
        asset_id=asset_id,
        service_category_id=c.id,
        urgency=urgency,
        title=title,
        problem_description=problem,
        status=JobStatus.requested.value,
        address=customer.province,
        contact_phone=customer.phone,
        preferred_date=now() + timedelta(days=1),
    )
    db.add(job)
    db.flush()
    if technician_id:
        job.assigned_technician_id = technician_id
        db.add(
            JobAssignment(
                job_id=job.id,
                technician_id=technician_id,
                assigned_by=None,
                status=AssignmentStatus.accepted.value if status != JobStatus.assigned.value else AssignmentStatus.offered.value,
                responded_at=now(),
            )
        )
    if status != JobStatus.requested.value:
        change_status(db, job, status, actor_id=technician_id, force=True)
    return job


def main() -> None:
    db = SessionLocal()
    try:
        # Prerequisites: admin + categories.
        seed_admin(db)
        seed_categories(db)
        db.flush()

        if db.query(User).filter(User.email == DEMO_MARKER_EMAIL).first():
            print("[demo] demo data already present — nothing to do")
            return

        admin = db.query(User).filter(User.role == UserRole.super_admin.value).first()

        # ---- Customers ----
        somchai = make_user(db, email=DEMO_MARKER_EMAIL, name="สมชาย ใจดี", role=UserRole.customer.value,
                            phone="0812345678", province="กรุงเทพมหานคร", district="จตุจักร")
        nida = make_user(db, email="nida@demo.homekeeper", name="นิดา รักบ้าน", role=UserRole.customer.value,
                        phone="0898765432", province="กรุงเทพมหานคร", district="ห้วยขวาง")

        # ---- Technicians (approved) ----
        chai_u = make_user(db, email="chai.tech@demo.homekeeper", name="ช่างชัย มือโปร", role=UserRole.technician.value,
                          phone="0861112222", province="กรุงเทพมหานคร", district="จตุจักร")
        lek_u = make_user(db, email="lek.tech@demo.homekeeper", name="ช่างเล็ก ประปาดี", role=UserRole.technician.value,
                         phone="0863334444", province="กรุงเทพมหานคร", district="ห้วยขวาง")
        db.flush()
        make_technician(db, chai_u, admin.id, lat=13.83, lng=100.56, radius=15, exp=8, rating=4.8, jobs_done=132,
                        bio="ช่างแอร์และช่างไฟฟ้า ประสบการณ์ 8 ปี", category_slugs=["air-conditioner", "electrician"])
        make_technician(db, lek_u, admin.id, lat=13.77, lng=100.57, radius=12, exp=5, rating=4.6, jobs_done=87,
                        bio="ช่างประปา งานเร็ว สะอาด", category_slugs=["plumber"])

        # ---- Properties + assets ----
        house = Property(owner_id=somchai.id, name="บ้านเดี่ยว รามอินทรา", property_type="house",
                         address="99/1 ซ.รามอินทรา 5", province="กรุงเทพมหานคร", district="จตุจักร",
                         latitude=13.83, longitude=100.56, year_built=2015, usable_area=180)
        db.add(house)
        db.flush()
        db.add_all([
            Asset(property_id=house.id, asset_category="เครื่องปรับอากาศ", name="แอร์ห้องนอน", brand="Daikin",
                  model="FTKM24", serial_number="DK-24-0091", purchase_date=date(2021, 4, 10),
                  warranty_end=date(2026, 4, 10), status="active",
                  maintenance_interval_days=180, next_maintenance_date=date.today() + timedelta(days=20)),
            Asset(property_id=house.id, asset_category="ปั๊มน้ำ", name="ปั๊มน้ำอัตโนมัติ", brand="Mitsubishi",
                  model="WP-205", serial_number="MB-205-7781", purchase_date=date(2020, 1, 5),
                  warranty_end=date(2025, 1, 5), status="active"),
            Asset(property_id=house.id, asset_category="เครื่องทำน้ำอุ่น", name="เครื่องทำน้ำอุ่น", brand="Stiebel",
                  model="IS27", status="active"),
        ])
        car = Property(owner_id=somchai.id, name="Toyota Yaris", property_type="car",
                       province="กรุงเทพมหานคร", district="จตุจักร")
        db.add(car)

        condo = Property(owner_id=nida.id, name="คอนโด ลุมพินี", property_type="condo",
                         address="เดอะลุมพินี ห้อง 18/302", province="กรุงเทพมหานคร", district="ห้วยขวาง",
                         floor="18", unit_number="302", latitude=13.77, longitude=100.57)
        db.add(condo)
        db.flush()
        aircon2 = Asset(property_id=condo.id, asset_category="เครื่องปรับอากาศ", name="แอร์ห้องนั่งเล่น",
                        brand="Mitsubishi", model="MSY-GT13", status="active")
        db.add(aircon2)
        db.flush()

        aircon1 = db.query(Asset).filter(Asset.property_id == house.id).first()

        # ---- Jobs across statuses ----
        # 1) New request waiting for admin dispatch.
        make_job(db, customer=nida, category_slug="plumber", title="ก๊อกน้ำในครัวรั่ว",
                 problem="น้ำหยดตลอดเวลา ปิดไม่สนิท", urgency=Urgency.today.value,
                 status=JobStatus.requested.value, property_id=condo.id)

        # 2) Assigned, technician accepted, on the way.
        make_job(db, customer=nida, category_slug="air-conditioner", title="แอร์ไม่เย็น",
                 problem="เปิดแล้วมีลมแต่ไม่เย็น", urgency=Urgency.scheduled.value,
                 status=JobStatus.traveling.value, property_id=condo.id, asset_id=aircon2.id,
                 technician_id=chai_u.id)

        # 3) In progress with an approved quotation.
        job3 = make_job(db, customer=somchai, category_slug="air-conditioner", title="ล้างแอร์ + เติมน้ำยา",
                        problem="ล้างใหญ่ประจำปีและเติมน้ำยา", urgency=Urgency.scheduled.value,
                        status=JobStatus.inspecting.value, property_id=house.id, asset_id=aircon1.id,
                        technician_id=chai_u.id)
        q3 = Quotation(job_id=job3.id, technician_id=chai_u.id, version=1, labor_cost=800, travel_cost=100,
                       inspection_fee=0, other_charges=0, discount=0, platform_fee=0, vat=0, total=1250,
                       notes="ล้างแอร์ + เติมน้ำยา R32", status=QuotationStatus.approved.value,
                       valid_until=now() + timedelta(days=7), responded_at=now())
        db.add(q3)
        db.flush()
        db.add(Part(quotation_id=q3.id, job_id=job3.id, part_name="น้ำยาแอร์ R32", brand="Daikin",
                    quantity=1, unit_price=350, authenticity=PartAuthenticity.genuine.value, warranty_period_days=30))
        change_status(db, job3, JobStatus.approved.value, actor_id=somchai.id, force=True)
        change_status(db, job3, JobStatus.in_progress.value, actor_id=chai_u.id, force=True)
        db.add(JobMedia(job_id=job3.id, uploaded_by=chai_u.id, kind=MediaKind.before.value,
                        url="https://picsum.photos/seed/aircon-before/400", caption="ก่อนล้าง"))

        # 4) Fully completed → Home Health Record + Warranty auto-generated, then a review.
        job4 = make_job(db, customer=somchai, category_slug="electrician", title="เปลี่ยนเบรกเกอร์ตู้ไฟ",
                        problem="เบรกเกอร์ตัดบ่อย ต้องเปลี่ยนตัวใหม่", urgency=Urgency.today.value,
                        status=JobStatus.inspecting.value, property_id=house.id, technician_id=chai_u.id)
        q4 = Quotation(job_id=job4.id, technician_id=chai_u.id, version=1, labor_cost=600, travel_cost=100,
                       inspection_fee=0, other_charges=0, discount=0, platform_fee=0, vat=0, total=1150,
                       notes="เปลี่ยนเบรกเกอร์ 2 ตัว ตรวจระบบไฟ", status=QuotationStatus.approved.value,
                       valid_until=now() + timedelta(days=7), responded_at=now())
        db.add(q4)
        db.flush()
        db.add(Part(quotation_id=q4.id, job_id=job4.id, part_name="เบรกเกอร์ 2P 32A", brand="Schneider",
                    quantity=2, unit_price=225, authenticity=PartAuthenticity.genuine.value, warranty_period_days=365))
        db.add(JobMedia(job_id=job4.id, uploaded_by=chai_u.id, kind=MediaKind.before.value,
                        url="https://picsum.photos/seed/panel-before/400", caption="ตู้ไฟก่อนซ่อม"))
        db.add(JobMedia(job_id=job4.id, uploaded_by=chai_u.id, kind=MediaKind.after.value,
                        url="https://picsum.photos/seed/panel-after/400", caption="ตู้ไฟหลังซ่อม"))
        # Flush media before completion: the session is autoflush=False, so the
        # Home Health Record generation would otherwise not see these rows.
        db.flush()
        change_status(db, job4, JobStatus.approved.value, actor_id=somchai.id, force=True)
        change_status(db, job4, JobStatus.in_progress.value, actor_id=chai_u.id, force=True)
        # This transition triggers the Home Health Record + Warranty generation.
        change_status(db, job4, JobStatus.completed.value, actor_id=chai_u.id, force=True)
        db.add(Review(job_id=job4.id, customer_id=somchai.id, technician_id=chai_u.id,
                      rating_quality=5, rating_punctuality=5, rating_politeness=5, rating_cleanliness=4,
                      rating_value=5, rating_communication=5, overall_rating=4.83,
                      comment="ช่างสุภาพมาก งานเรียบร้อย เก็บกวาดสะอาด แนะนำเลยครับ"))

        db.commit()
        print("[demo] demo data created successfully")
        print("       password for ALL demo accounts: " + DEMO_PASSWORD)
        print("       customers : somchai@demo.homekeeper , nida@demo.homekeeper")
        print("       technicians: chai.tech@demo.homekeeper , lek.tech@demo.homekeeper")
        print("       admin     : use SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD")
    finally:
        db.close()


if __name__ == "__main__":
    main()
