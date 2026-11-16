"""RentWise: local-first rental-management portfolio prototype.

This project records offline rent payments; it does NOT process online payments.
Never use it with real tenant information before a security and privacy review.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from pathlib import Path
import os
import secrets
import calendar
import json
from sqlalchemy import text

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, ForeignKey, String, Numeric, Date, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
DB_URL = os.environ.get("RENTWISE_DATABASE_URL", f"sqlite:///{BASE_DIR / 'rentwise.sqlite3'}")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(250))


class Property(Base):
    __tablename__ = "properties"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    location: Mapped[str] = mapped_column(String(180))
    units: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")


class Lease(Base):
    __tablename__ = "leases"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"))
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"))
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    lease_id: Mapped[int] = mapped_column(ForeignKey("leases.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    paid_on: Mapped[date] = mapped_column(Date)
    method: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(String(250), default="")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    billing_month: Mapped[str | None] = mapped_column(String(7), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(nullable=True)
    void_reason: Mapped[str] = mapped_column(String(240), default="")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column()
    action: Mapped[str] = mapped_column(String(30))
    changes: Mapped[str] = mapped_column(String(2500), default="{}")
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class Registration(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=10, max_length=128)


class Login(BaseModel):
    email: str
    password: str


class NewProperty(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    location: str = Field(min_length=2, max_length=180)
    units: int = Field(ge=1, le=1000)


class NewTenant(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=40)


class NewLease(BaseModel):
    property_id: int
    tenant_id: int
    monthly_rent: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    start_date: date
    end_date: date | None = None


class NewPayment(BaseModel):
    lease_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    paid_on: date
    method: str = Field(pattern="^(cash|bank transfer|upi|other)$")
    note: str = Field(default="", max_length=250)
    billing_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class VoidRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=240)


app = FastAPI(title="RentWise", version="0.2.0", description="Rental management prototype; payment recording only.")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("RENTWISE_SESSION_SECRET", secrets.token_urlsafe(48)), same_site="lax", https_only=os.environ.get("RENTWISE_HTTPS_ONLY", "0") == "1")
Base.metadata.create_all(engine)
# Non-destructive local SQLite migration. Older payments remain UNALLOCATED until reviewed.
if DB_URL.startswith("sqlite"):
    with engine.begin() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(payments)").all()}
        if "billing_month" not in existing:
            conn.exec_driver_sql("ALTER TABLE payments ADD COLUMN billing_month VARCHAR(7)")
        if "voided_at" not in existing:
            conn.exec_driver_sql("ALTER TABLE payments ADD COLUMN voided_at DATETIME")
        if "void_reason" not in existing:
            conn.exec_driver_sql("ALTER TABLE payments ADD COLUMN void_reason VARCHAR(240) DEFAULT ''")


def audit(session: Session, owner_id: int, entity: str, entity_id: int, action: str, before=None, after=None):
    payload = json.dumps({"before": before, "after": after}, default=str, ensure_ascii=False)
    session.add(AuditEvent(owner_id=owner_id, entity=entity, entity_id=entity_id, action=action, changes=payload[:2500]))


def as_month(value: str) -> tuple[date, date]:
    try:
        year, month = map(int, value.split("-"))
        start = date(year, month, 1)
        return start, date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, AttributeError):
        raise HTTPException(422, "Billing month must be YYYY-MM.")


def overlaps(a_start: date, a_end: date | None, b_start: date, b_end: date | None) -> bool:
    return a_start <= (b_end or date.max) and b_start <= (a_end or date.max)


def validate_lease(session: Session, owner_id: int, data: NewLease, excluding_id: int | None = None):
    if data.end_date is not None and data.end_date < data.start_date:
        raise HTTPException(422, "End date must be on or after start date.")
    prop = get_owned(session, Property, data.property_id, owner_id)
    get_owned(session, Tenant, data.tenant_id, owner_id)
    if prop.units == 1:
        for existing in session.scalars(select(Lease).where(Lease.owner_id == owner_id, Lease.property_id == prop.id)):
            if existing.id != excluding_id and overlaps(existing.start_date, existing.end_date, data.start_date, data.end_date):
                raise HTTPException(409, "This single-unit property already has an overlapping lease.")
    # Multi-unit properties need unit-level occupancy to validate conflicts.


def validate_payment_month(lease: Lease, billing_month: str):
    month_start, month_end = as_month(billing_month)
    if lease.start_date > month_end or (lease.end_date and lease.end_date < month_start):
        raise HTTPException(422, "Billing month is outside this lease's term.")


def current_user(request: Request, session: Session) -> User:
    user_id = request.session.get("user_id")
    user = session.get(User, user_id) if isinstance(user_id, int) else None
    if user is None:
        raise HTTPException(401, "Please sign in to continue.")
    return user


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(24)
    dk = pbkdf2_hmac("sha256", password.encode(), salt, 360_000)
    return f"pbkdf2_sha256$360000${salt.hex()}${dk.hex()}"


def password_matches(password: str, encoded: str) -> bool:
    try:
        scheme, iters, salt_hex, expected = encoded.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        calculated = pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
        return compare_digest(calculated, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def currency(value: Decimal) -> str:
    return f"{value:.2f}"


def get_owned(session: Session, model, record_id: int, owner_id: int):
    result = session.scalar(select(model).where(model.id == record_id, model.owner_id == owner_id))
    if result is None:
        raise HTTPException(404, "Record not found.")
    return result


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")


@app.get("/app.css", include_in_schema=False)
def css():
    return FileResponse(BASE_DIR / "app" / "static" / "app.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def js():
    return FileResponse(BASE_DIR / "app" / "static" / "app.js", media_type="application/javascript")


@app.post("/api/register")
def register(request: Request, data: Registration):
    email = data.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(422, "Enter a valid email address.")
    with Session(engine) as session:
        if session.scalar(select(User).where(User.email == email)):
            raise HTTPException(409, "An account with that email already exists.")
        user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password))
        session.add(user)
        session.commit()
        session.refresh(user)
        request.session["user_id"] = user.id
        return {"id": user.id, "name": user.name, "email": user.email}


@app.post("/api/login")
def login(request: Request, data: Login):
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.email == data.email.strip().lower()))
        if not user or not password_matches(data.password, user.password_hash):
            raise HTTPException(401, "Incorrect email or password.")
        request.session.clear()
        request.session["user_id"] = user.id
        return {"id": user.id, "name": user.name, "email": user.email}


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.get("/api/me")
def me(request: Request):
    with Session(engine) as session:
        user = current_user(request, session)
        return {"id": user.id, "name": user.name, "email": user.email}


@app.get("/api/properties")
def properties(request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        return [{"id": p.id, "name": p.name, "location": p.location, "units": p.units} for p in session.scalars(select(Property).where(Property.owner_id == owner.id).order_by(Property.id.desc()))]


@app.post("/api/properties", status_code=201)
def create_property(request: Request, data: NewProperty):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = Property(owner_id=owner.id, name=data.name.strip(), location=data.location.strip(), units=data.units)
        session.add(item)
        session.flush()
        audit(session, owner.id, "property", item.id, "created", after={"name": item.name, "location": item.location, "units": item.units})
        session.commit()
        return {"id": item.id, "name": item.name}


@app.get("/api/tenants")
def tenants(request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        return [{"id": t.id, "name": t.name, "email": t.email, "phone": t.phone} for t in session.scalars(select(Tenant).where(Tenant.owner_id == owner.id).order_by(Tenant.id.desc()))]


@app.post("/api/tenants", status_code=201)
def create_tenant(request: Request, data: NewTenant):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = Tenant(owner_id=owner.id, name=data.name.strip(), email=data.email.strip(), phone=data.phone.strip())
        session.add(item)
        session.flush()
        audit(session, owner.id, "tenant", item.id, "created", after={"name": item.name, "email": item.email, "phone": item.phone})
        session.commit()
        return {"id": item.id, "name": item.name}


@app.get("/api/leases")
def leases(request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        result = []
        for lease in session.scalars(select(Lease).where(Lease.owner_id == owner.id).order_by(Lease.id.desc())):
            prop = session.get(Property, lease.property_id)
            tenant = session.get(Tenant, lease.tenant_id)
            result.append({"id": lease.id, "property_id": lease.property_id, "tenant_id": lease.tenant_id, "property": prop.name, "tenant": tenant.name, "monthly_rent": currency(lease.monthly_rent), "start_date": lease.start_date.isoformat(), "end_date": lease.end_date.isoformat() if lease.end_date else None})
        return result


@app.post("/api/leases", status_code=201)
def create_lease(request: Request, data: NewLease):
    with Session(engine) as session:
        owner = current_user(request, session)
        validate_lease(session, owner.id, data)
        lease = Lease(owner_id=owner.id, property_id=data.property_id, tenant_id=data.tenant_id, monthly_rent=data.monthly_rent, start_date=data.start_date, end_date=data.end_date)
        session.add(lease)
        session.flush()
        audit(session, owner.id, "lease", lease.id, "created", after=data.model_dump(mode="json"))
        session.commit()
        return {"id": lease.id}


@app.get("/api/payments")
def payments(request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        out = []
        for p in session.scalars(select(Payment).where(Payment.owner_id == owner.id).order_by(Payment.paid_on.desc(), Payment.id.desc())):
            lease = session.get(Lease, p.lease_id)
            tenant = session.get(Tenant, lease.tenant_id)
            out.append({"id": p.id, "lease_id": p.lease_id, "tenant": tenant.name, "amount": currency(p.amount), "paid_on": p.paid_on.isoformat(), "method": p.method, "note": p.note, "billing_month": p.billing_month, "voided": p.voided_at is not None, "void_reason": p.void_reason})
        return out


@app.post("/api/payments", status_code=201)
def create_payment(request: Request, data: NewPayment):
    with Session(engine) as session:
        owner = current_user(request, session)
        lease = get_owned(session, Lease, data.lease_id, owner.id)
        validate_payment_month(lease, data.billing_month)
        item = Payment(owner_id=owner.id, lease_id=data.lease_id, amount=data.amount, paid_on=data.paid_on, method=data.method, note=data.note.strip(), billing_month=data.billing_month)
        session.add(item)
        session.flush()
        audit(session, owner.id, "payment", item.id, "created", after=data.model_dump(mode="json"))
        session.commit()
        return {"id": item.id}



@app.put("/api/properties/{record_id}")
def edit_property(record_id: int, request: Request, data: NewProperty):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Property, record_id, owner.id)
        if data.units == 1:
            leases_for_property = list(session.scalars(select(Lease).where(Lease.owner_id == owner.id, Lease.property_id == item.id)))
            for i, first in enumerate(leases_for_property):
                for second in leases_for_property[i + 1:]:
                    if overlaps(first.start_date, first.end_date, second.start_date, second.end_date):
                        raise HTTPException(409, "Resolve overlapping leases before reducing this property to one unit.")
        before = {"name": item.name, "location": item.location, "units": item.units}
        item.name, item.location, item.units = data.name.strip(), data.location.strip(), data.units
        audit(session, owner.id, "property", item.id, "edited", before, data.model_dump())
        session.commit()
        return {"ok": True}


@app.delete("/api/properties/{record_id}")
def delete_property(record_id: int, request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Property, record_id, owner.id)
        if session.scalar(select(Lease.id).where(Lease.owner_id == owner.id, Lease.property_id == record_id).limit(1)):
            raise HTTPException(409, "Property has leases. Remove or reassign them before deleting.")
        audit(session, owner.id, "property", item.id, "deleted", before={"name": item.name, "location": item.location})
        session.delete(item)
        session.commit()
        return {"ok": True}


@app.put("/api/tenants/{record_id}")
def edit_tenant(record_id: int, request: Request, data: NewTenant):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Tenant, record_id, owner.id)
        before = {"name": item.name, "email": item.email, "phone": item.phone}
        item.name, item.email, item.phone = data.name.strip(), data.email.strip(), data.phone.strip()
        audit(session, owner.id, "tenant", item.id, "edited", before, {"name": item.name, "email": item.email, "phone": item.phone})
        session.commit()
        return {"ok": True}


@app.delete("/api/tenants/{record_id}")
def delete_tenant(record_id: int, request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Tenant, record_id, owner.id)
        if session.scalar(select(Lease.id).where(Lease.owner_id == owner.id, Lease.tenant_id == record_id).limit(1)):
            raise HTTPException(409, "Tenant has leases. Cannot delete without removing linked leases.")
        audit(session, owner.id, "tenant", item.id, "deleted", before={"name": item.name})
        session.delete(item)
        session.commit()
        return {"ok": True}


@app.put("/api/leases/{record_id}")
def edit_lease(record_id: int, request: Request, data: NewLease):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Lease, record_id, owner.id)
        validate_lease(session, owner.id, data, excluding_id=item.id)
        for payment in session.scalars(select(Payment).where(Payment.owner_id == owner.id, Payment.lease_id == record_id)):
            if payment.billing_month:
                shadow = Lease(start_date=data.start_date, end_date=data.end_date)
                validate_payment_month(shadow, payment.billing_month)
        before = {"property_id": item.property_id, "tenant_id": item.tenant_id, "monthly_rent": str(item.monthly_rent), "start_date": str(item.start_date), "end_date": str(item.end_date)}
        item.property_id, item.tenant_id, item.monthly_rent = data.property_id, data.tenant_id, data.monthly_rent
        item.start_date, item.end_date = data.start_date, data.end_date
        audit(session, owner.id, "lease", item.id, "edited", before, data.model_dump(mode="json"))
        session.commit()
        return {"ok": True}


@app.delete("/api/leases/{record_id}")
def delete_lease(record_id: int, request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Lease, record_id, owner.id)
        if session.scalar(select(Payment.id).where(Payment.owner_id == owner.id, Payment.lease_id == record_id).limit(1)):
            raise HTTPException(409, "Lease has payment records. Cannot delete; edit the lease instead.")
        audit(session, owner.id, "lease", item.id, "deleted", before={"property_id": item.property_id, "tenant_id": item.tenant_id, "monthly_rent": str(item.monthly_rent), "start_date": str(item.start_date), "end_date": str(item.end_date)})
        session.delete(item)
        session.commit()
        return {"ok": True}


@app.put("/api/payments/{record_id}")
def edit_payment(record_id: int, request: Request, data: NewPayment):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Payment, record_id, owner.id)
        if item.voided_at is not None:
            raise HTTPException(409, "Voided payments cannot be edited.")
        lease = get_owned(session, Lease, data.lease_id, owner.id)
        validate_payment_month(lease, data.billing_month)
        before = {"lease_id": item.lease_id, "amount": str(item.amount), "paid_on": str(item.paid_on), "method": item.method, "note": item.note, "billing_month": item.billing_month}
        item.lease_id, item.amount, item.paid_on = data.lease_id, data.amount, data.paid_on
        item.method, item.note, item.billing_month = data.method, data.note.strip(), data.billing_month
        audit(session, owner.id, "payment", item.id, "corrected", before, data.model_dump(mode="json"))
        session.commit()
        return {"ok": True}


@app.post("/api/payments/{record_id}/void")
def void_payment(record_id: int, request: Request, data: VoidRequest):
    with Session(engine) as session:
        owner = current_user(request, session)
        item = get_owned(session, Payment, record_id, owner.id)
        if item.voided_at is not None:
            raise HTTPException(409, "Payment was already voided.")
        item.voided_at = datetime.now(timezone.utc)
        item.void_reason = data.reason.strip()
        audit(session, owner.id, "payment", item.id, "voided", before={"amount": str(item.amount), "billing_month": item.billing_month}, after={"reason": item.void_reason})
        session.commit()
        return {"ok": True}


@app.get("/api/audit")
def audit_events(request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        rows = session.scalars(select(AuditEvent).where(AuditEvent.owner_id == owner.id).order_by(AuditEvent.id.desc()).limit(100))
        return [{"id": a.id, "entity": a.entity, "entity_id": a.entity_id, "action": a.action, "timestamp": a.timestamp.isoformat()} for a in rows]


def month_summary(session: Session, owner_id: int, month: str):
    month_start, month_end = as_month(month)
    leases_for_owner = list(session.scalars(select(Lease).where(Lease.owner_id == owner_id)))
    active = [lease for lease in leases_for_owner if lease.start_date <= month_end and (lease.end_date is None or lease.end_date >= month_start)]
    payments = list(session.scalars(select(Payment).where(Payment.owner_id == owner_id, Payment.voided_at.is_(None))))
    allocated = {}
    for payment in payments:
        if payment.billing_month == month:
            allocated[payment.lease_id] = allocated.get(payment.lease_id, Decimal("0")) + payment.amount
    invoices = []
    for lease in active:
        prop = session.get(Property, lease.property_id)
        tenant = session.get(Tenant, lease.tenant_id)
        paid = allocated.get(lease.id, Decimal("0"))
        balance = max(lease.monthly_rent - paid, Decimal("0"))
        invoices.append({
            "lease_id": lease.id, "property": prop.name, "tenant": tenant.name,
            "period": month, "due": currency(lease.monthly_rent),
            "paid": currency(paid), "balance": currency(balance),
            "credit": currency(max(paid - lease.monthly_rent, Decimal("0"))),
            "status": "paid" if balance == 0 else ("partial" if paid > 0 else "unpaid"),
        })
    expected = sum((lease.monthly_rent for lease in active), Decimal("0"))
    paid_for_month = sum((Decimal(i["paid"]) for i in invoices), Decimal("0"))
    cash_received = sum((p.amount for p in payments if month_start <= p.paid_on <= month_end), Decimal("0"))
    unallocated = sum((p.amount for p in payments if p.billing_month is None), Decimal("0"))
    outstanding = sum((Decimal(i["balance"]) for i in invoices), Decimal("0"))
    return {"invoices": invoices, "expected": currency(expected), "allocated": currency(paid_for_month), "received": currency(cash_received), "outstanding": currency(outstanding), "unallocated": currency(unallocated), "active_leases": len(active)}


@app.get("/api/invoices")
def invoices(request: Request, month: str | None = None):
    month = month or date.today().strftime("%Y-%m")
    with Session(engine) as session:
        owner = current_user(request, session)
        report = month_summary(session, owner.id, month)
        return {"month": month, **report, "note": "Computed monthly rent charges for active leases. Full-month rent, no proration, fees, adjustments or refunds. Not tax invoices."}


@app.get("/api/stats")
def stats(request: Request):
    with Session(engine) as session:
        owner = current_user(request, session)
        today = date.today()
        report = month_summary(session, owner.id, today.strftime("%Y-%m"))
        pcount = session.scalar(select(func.count(Property.id)).where(Property.owner_id == owner.id))
        tcount = session.scalar(select(func.count(Tenant.id)).where(Tenant.owner_id == owner.id))
        return {"properties": pcount, "tenants": tcount, **{k: v for k, v in report.items() if k != "invoices"}, "month": today.strftime("%B %Y"), "assumptions": "Charges are grouped by rent month and payments are allocated to a specific month; cash received uses payment date. Full rent is charged for each month touched by a lease (no proration). Legacy payments remain unallocated until corrected. This is a prototype, not formal accounting."}
