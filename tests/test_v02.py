"""RentWise v0.2 regression tests. Synthetic records only."""
import asyncio
from datetime import date
import tempfile
from pathlib import Path

import httpx
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from app import main


def test_rent_month_corrections_and_audit():
    async def scenario():
        with tempfile.TemporaryDirectory() as directory:
            main.engine = create_engine("sqlite:///" + str(Path(directory) / "rentwise-test.sqlite3"), connect_args={"check_same_thread": False}, poolclass=NullPool)
            main.Base.metadata.create_all(main.engine)
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://local") as owner:
                res = await owner.post("/api/register", json={"name":"Demo Owner","email":"demo@example.test","password":"test-password-234"})
                assert res.status_code == 200, res.text
                prop = (await owner.post("/api/properties", json={"name":"Demo Flat","location":"Example City","units":1})).json()["id"]
                tenant = (await owner.post("/api/tenants", json={"name":"Demo Tenant","email":"","phone":""})).json()["id"]
                month = date.today().strftime("%Y-%m")
                next_year = date.today().year + (date.today().month == 12)
                next_month = (date.today().month % 12) + 1
                future = f"{next_year:04d}-{next_month:02d}"
                lease_payload = {"property_id":prop,"tenant_id":tenant,"monthly_rent":"15000.00","start_date":date.today().replace(day=1).isoformat()}
                lease_result = await owner.post("/api/leases",json=lease_payload)
                assert lease_result.status_code == 201, lease_result.text
                lease = lease_result.json()["id"]
                overlap = await owner.post("/api/leases", json=lease_payload)
                assert overlap.status_code == 409, overlap.text
                payment_payload = {"lease_id":lease,"amount":"5000.00","paid_on":date.today().isoformat(),"method":"cash","note":"Advance for next month","billing_month":future}
                pay_result = await owner.post("/api/payments",json=payment_payload)
                assert pay_result.status_code == 201, pay_result.text
                payment = pay_result.json()["id"]
                stats=(await owner.get("/api/stats")).json()
                assert stats["received"]=="5000.00", stats
                assert stats["allocated"]=="0.00", stats
                assert stats["outstanding"]=="15000.00", stats
                next_bill=(await owner.get("/api/invoices",params={"month":future})).json()
                assert next_bill["allocated"]=="5000.00", next_bill
                assert next_bill["outstanding"]=="10000.00", next_bill

                payment_payload.update({"billing_month":month,"note":"Current month partial payment"})
                corrected=await owner.put(f"/api/payments/{payment}",json=payment_payload)
                assert corrected.status_code==200, corrected.text
                stats=(await owner.get("/api/stats")).json()
                assert stats["allocated"]=="5000.00" and stats["outstanding"]=="10000.00", stats
                # Changing an old lease should not silently move a billed payment outside its term.
                change={**lease_payload,"start_date":f"{next_year:04d}-{next_month:02d}-01"}
                assert (await owner.put(f"/api/leases/{lease}",json=change)).status_code==422

                # Users cannot edit or void another landlord's payment.
                async with httpx.AsyncClient(transport=transport,base_url="http://local") as second:
                    assert (await second.post("/api/register",json={"name":"Second Owner","email":"second@example.test","password":"test-password-789"})).status_code==200
                    assert (await second.put(f"/api/payments/{payment}",json=payment_payload)).status_code==404
                    assert (await second.post(f"/api/payments/{payment}/void",json={"reason":"Wrong amount"})).status_code==404
                    assert (await second.delete(f"/api/properties/{prop}")).status_code==404

                assert (await owner.delete(f"/api/properties/{prop}")).status_code==409
                assert (await owner.post(f"/api/payments/{payment}/void",json={"reason":"Sample correction"})).status_code==200
                assert (await owner.post(f"/api/payments/{payment}/void",json={"reason":"Again"})).status_code==409
                stats=(await owner.get("/api/stats")).json()
                assert stats["received"]=="0.00" and stats["outstanding"]=="15000.00", stats
                payments=(await owner.get("/api/payments")).json()
                assert payments[0]["voided"] is True
                actions=[e["action"] for e in (await owner.get("/api/audit")).json()]
                assert "voided" in actions and "corrected" in actions and "created" in actions, actions
                assert (await owner.put(f"/api/payments/{payment}",json=payment_payload)).status_code==409
    asyncio.run(scenario())


def test_edit_delete_and_legacy_migration():
    async def scenario():
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/"rentwise-test.sqlite3")
            main.engine=create_engine("sqlite:///"+path,connect_args={"check_same_thread": False}, poolclass=NullPool)
            main.Base.metadata.create_all(main.engine)
            transport=httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport,base_url="http://local") as user:
                assert (await user.post("/api/register",json={"name":"Test Person","email":"person@example.test","password":"pass-test-12345"})).status_code==200
                p=(await user.post("/api/properties",json={"name":"Old label","location":"Example Town","units":1})).json()["id"]
                t=(await user.post("/api/tenants",json={"name":"Old tenant name","email":"","phone":""})).json()["id"]
                assert (await user.put(f"/api/properties/{p}",json={"name":"Corrected label","location":"Example Town","units":1})).status_code==200
                assert (await user.put(f"/api/tenants/{t}",json={"name":"Corrected tenant name","email":"","phone":""})).status_code==200
                assert (await user.get("/api/properties")).json()[0]["name"]=="Corrected label"
                assert (await user.get("/api/tenants")).json()[0]["name"]=="Corrected tenant name"
                assert (await user.delete(f"/api/tenants/{t}")).status_code==200
                assert (await user.delete(f"/api/properties/{p}")).status_code==200
                assert (await user.get("/api/properties")).json()==[]
                assert (await user.get("/api/tenants")).json()==[]
                assert len((await user.get("/api/audit")).json())>=6
    asyncio.run(scenario())
