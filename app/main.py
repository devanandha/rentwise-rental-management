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


app = FastAPI(title="RentWise", version="0.1.0", description="Rental management prototype; payment recording only.")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("RENTWISE_SESSION_SECRET", secrets.token_urlsafe(48)), same_site="lax", https_only=os.environ.get("RENTWISE_HTTPS_ONLY", "0") == "1")
Base.metadata.create_all(engine)


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
            result.append({"id": lease.id, "property": prop.name, "tenant": tenant.name, "monthly_rent": currency(lease.monthly_rent), "start_date": lease.start_date.isoformat(), "end_date": lease.end_date.isoformat() if lease.end_date else None})
        return result


@app.post("/api/leases", status_code=201)
def create_lease(request: Request, data: NewLease):
    if data.end_date is not None and data.end_date < data.start_date:
        raise HTTPException(422, "End date must be after start date.")
    with Session(engine) as session:
        owner = current_user(request, session)
        get_owned(session, Property, data.property_id, owner.id)
        get_owned(session, Tenant, data.tenant_id, owner.id)
        lease = Lease(owner_id=owner.id, property_id=data.property_id, tenant_id=data.tenant_id, monthly_rent=data.monthly_rent, start_date=data.start_date, end_date=data.end_date)
        session.add(lease)
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
            out.append({"id": p.id, "tenant": tenant.name, "amount": currency(p.amount), "paid_on": p.paid_on.isoformat(), "method": p.method, "note": p.note})
        return out


@app.post("/api/payments", status_code=201)
def create_payment(request: Request, data: NewPayment):
    with Session(engine) as session:
        owner = current_user(request, session)
        get_owned(session, Lease, data.lease_id, owner.id)
        item = Payment(owner_id=owner.id, lease_id=data.lease_id, amount=data.amount, paid_on=data.paid_on, method=data.method, note=data.note.strip())
        session.add(item)
        session.commit()
        return {"id": item.id}


@app.get("/api/stats")
def stats(request: Request):
    """Simple monthly ledger summary, not an accounting statement.

    Assumes full rent for a lease active at any point this month; no proration,
    credits, deposits, tax, adjustments, or late fees.
    """
    with Session(engine) as session:
        owner = current_user(request, session)
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        all_leases = list(session.scalars(select(Lease).where(Lease.owner_id == owner.id)))
        active = [lease for lease in all_leases if lease.start_date <= month_end and (lease.end_date is None or lease.end_date >= month_start)]
        expected = sum((lease.monthly_rent for lease in active), Decimal("0"))
        received = session.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.owner_id == owner.id, Payment.paid_on >= month_start, Payment.paid_on <= month_end))
        received = Decimal(str(received))
        pcount = session.scalar(select(func.count(Property.id)).where(Property.owner_id == owner.id))
        tcount = session.scalar(select(func.count(Tenant.id)).where(Tenant.owner_id == owner.id))
        return {"properties": pcount, "tenants": tcount, "active_leases": len(active), "expected": currency(expected), "received": currency(received), "outstanding": currency(max(expected-received, Decimal("0"))), "month": today.strftime("%B %Y"), "assumptions": "Full monthly rent for every lease active during the month; recorded payments are grouped by payment date. Not an accounting statement."}
