"""Integration smoke tests; create only fictitious local data."""
import asyncio
import os
from pathlib import Path
import tempfile

import httpx


def test_owner_scoping_and_rent_ledger():
    with tempfile.TemporaryDirectory() as folder:
        os.environ["RENTWISE_DATABASE_URL"] = "sqlite:///" + str(Path(folder) / "rentwise-test.sqlite3")
        from app.main import app
        async def scenario():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport,base_url="http://testserver") as a:
                reg=await a.post('/api/register',json={'name':'Owner One','email':'owner1@example.test','password':'test-password-123'})
                assert reg.status_code==200,reg.text
                prop=await a.post('/api/properties',json={'name':'Mock Property','location':'Demo City','units':2})
                assert prop.status_code==201
                tenant=await a.post('/api/tenants',json={'name':'Example Tenant','email':'test@example.test','phone':''})
                assert tenant.status_code==201
                from datetime import date
                lease=await a.post('/api/leases',json={'property_id':prop.json()['id'],'tenant_id':tenant.json()['id'],'monthly_rent':'12000.00','start_date':date.today().replace(day=1).isoformat()})
                assert lease.status_code==201,lease.text
                pay=await a.post('/api/payments',json={'lease_id':lease.json()['id'],'amount':'3000.00','paid_on':date.today().isoformat(),'method':'upi','note':'Demo payment only','billing_month':date.today().strftime('%Y-%m')})
                assert pay.status_code==201,pay.text
                stats=(await a.get('/api/stats')).json()
                assert stats['expected']=='12000.00' and stats['received']=='3000.00' and stats['outstanding']=='9000.00',stats
            async with httpx.AsyncClient(transport=transport,base_url="http://testserver") as b:
                reg2=await b.post('/api/register',json={'name':'Owner Two','email':'owner2@example.test','password':'another-test-password'})
                assert reg2.status_code==200
                assert (await b.get('/api/properties')).json()==[]
                assert (await b.get('/api/payments')).json()==[]
                forbidden=await b.post('/api/leases',json={'property_id':prop.json()['id'],'tenant_id':tenant.json()['id'],'monthly_rent':'900.00','start_date':date.today().isoformat()})
                assert forbidden.status_code==404
            async with httpx.AsyncClient(transport=transport,base_url="http://testserver") as anon:
                assert (await anon.get('/api/properties')).status_code==401
        asyncio.run(scenario())
