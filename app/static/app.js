"use strict";
let user = null;
let active = 'overview';
let selectedMonth = new Date().toISOString().slice(0,7);
let records = {properties:[], tenants:[], leases:[], payments:[]};
const root = document.getElementById('app');
const dialog = document.getElementById('dialog');
const money = n => '₹' + Number(n || 0).toLocaleString('en-IN', {minimumFractionDigits:2,maximumFractionDigits:2});
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const today = () => new Date().toISOString().slice(0,10);
const api = async (path, payload, method='POST') => {
  const options = {credentials:'same-origin'};
  if (method !== 'POST' || payload !== undefined) options.method=method;
  if (payload !== undefined) { options.headers={'Content-Type':'application/json'}; options.body=JSON.stringify(payload); }
  const r = await fetch('/api/' + path, options);
  let data = {};
  try { data = await r.json(); } catch(e) { /* no content */ }
  if (!r.ok) { throw new Error(typeof data.detail === 'string' ? data.detail : (Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join('; ') : 'Request failed.')); }
  return data;
};
function toast(message, error=false) { const el=document.getElementById('toast');el.textContent=message;el.className=error?'error':''; clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.textContent='',3800); }
const icon = (key)=>({overview:'◈',properties:'⌂',tenants:'♙',leases:'▤',payments:'↗',invoices:'▦',audit:'◷'}[key]);
async function initialize(){ try{user=await api('me'); await refresh();} catch(e){user=null; renderAuth();}}
function renderAuth(mode='login'){
  root.innerHTML=`<div class="auth-shell"><section class="auth-side"><div class="brand"><span class="brand-icon">R</span> rentwise<span style="color:#b1f2bf">.</span></div><div class="auth-head"><div class="eyebrow">A simpler way to manage rentals</div><h1>Less admin.<br>More clarity.</h1><p>Keep your properties, tenants, leases and rent records together in one thoughtfully designed workspace.</p></div><div class="stat-banner"><strong>Built to make the details feel simple.</strong><p style="margin:7px 0 0">Independent portfolio prototype · Synthetic data recommended · No real payments processed</p></div></section><section class="auth-main"><div class="auth-card"><span class="eyebrow">Welcome to RentWise</span><h2>${mode==='login'?'Sign in':'Create your account'}</h2><p>${mode==='login'?'Your rental portfolio, all in one place.':'Start with a private local account. Use fictional data for testing.'}</p><form id="authForm">${mode==='signup'?'<div class="field"><label for="authName">Full name</label><input id="authName" name="name" autocomplete="name" required minlength="2" placeholder="Your name"></div>':''}<div class="field"><label for="authEmail">Email address</label><input id="authEmail" name="email" type="email" autocomplete="email" required placeholder="you@example.com"></div><div class="field"><label for="authPassword">Password</label><input id="authPassword" name="password" type="password" autocomplete="${mode==='login'?'current-password':'new-password'}" required minlength="${mode==='login'?'1':'10'}" placeholder="${mode==='login'?'Enter password':'At least 10 characters'}"></div><button type="submit" class="button full" style="margin-top:12px">${mode==='login'?'Sign in →':'Create account →'}</button></form><div class="switch-auth">${mode==='login'?"Don't have an account?":"Already have an account?"}<button id="swapAuth" type="button">${mode==='login'?'Sign up':'Sign in'}</button></div><p class="developer-note">Prototype only · No payment gateway connected</p></div></section></div>`;
  document.getElementById('swapAuth').onclick=()=>renderAuth(mode==='login'?'signup':'login');
  document.getElementById('authForm').onsubmit=async e=>{e.preventDefault();const form=new FormData(e.target);try{user=await api(mode==='login'?'login':'register',Object.fromEntries(form));await refresh();toast('Welcome to RentWise.');}catch(err){toast(err.message,true);}};
}
async function refresh(){const [p,t,l,pay,stats,bills,events]=await Promise.all(['properties','tenants','leases','payments','stats','invoices?month='+encodeURIComponent(selectedMonth),'audit'].map(s=>api(s)));records={properties:p,tenants:t,leases:l,payments:pay};window.currentStats=stats;window.currentInvoices=bills;window.auditEvents=events;renderApp();}
function navButton(key,label){return `<button data-nav="${key}" class="${active===key?'active':''}"><span class="glyph">${icon(key)}</span> ${label}</button>`;}
function renderApp(){
 const stats=window.currentStats;
 const sectionNames={overview:'Overview',properties:'Properties',tenants:'Tenants',leases:'Leases',payments:'Payments',invoices:'Rent bills',audit:'Activity log'};
 root.innerHTML=`<div class="app-shell"><aside class="sidebar"><div class="brand"><span class="brand-icon">R</span> rentwise<span style="color:#b4efc5">.</span></div><nav class="nav" aria-label="Main navigation">${navButton('overview','Overview')}${navButton('properties','Properties')}${navButton('tenants','Tenants')}${navButton('leases','Leases')}${navButton('payments','Rent ledger')}${navButton('invoices','Rent bills')}${navButton('audit','Activity log')}</nav><div class="sidebar-bottom"><div class="small" style="opacity:.7">SIGNED IN AS</div><strong>${escapeHtml(user.name)}</strong><div class="small" style="margin-top:4px;word-break:break-all">${escapeHtml(user.email)}</div><button id="logout" type="button">↩ Sign out</button></div></aside><main class="workspace"><header class="topline"><div class="toplabel">RENTWISE / ${sectionNames[active].toUpperCase()}</div><div class="hello">Hello, ${escapeHtml(user.name.split(' ')[0])} 👋</div></header>${active==='overview'?renderDashboard():active==='invoices'?renderInvoices():active==='audit'?renderAudit():renderRecords()}<div class="developer-note">RentWise v0.2 · Local development prototype · Payments are recorded, not processed</div></main></div>`;
 document.querySelectorAll('[data-nav]').forEach(b=>b.onclick=()=>{active=b.dataset.nav;renderApp();});
 document.getElementById('logout').onclick=async()=>{await api('logout',{});user=null;active='overview';renderAuth();};
 document.querySelectorAll('[data-create]').forEach(b=>b.onclick=()=>openForm(b.dataset.create));
 document.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>{const [type,id]=b.dataset.edit.split(':');openForm(type,records[type].find(r=>r.id===Number(id)));});
 document.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>removeRecord(b.dataset.remove));
 document.querySelectorAll('[data-void]').forEach(b=>b.onclick=()=>voidRecord(Number(b.dataset.void)));
 const picker=document.getElementById('invoiceMonth');
 if(picker)picker.onchange=async()=>{selectedMonth=picker.value;try{await refresh();}catch(err){toast(err.message,true);}};

}
const headings={properties:['Your properties','Organise all your rental spaces in one view.','Add property'],tenants:['Your tenants','Manage your tenant directory with clarity.','Add tenant'],leases:['Lease agreements','Connect a tenant and property to a monthly rent.','Add lease'],payments:['Rent ledger','Track offline payments and recorded transactions.','Record payment']};
const addButton=type=>`<button class="button" data-create="${type}">+ ${headings[type][2]}</button>`;
function renderDashboard(){ const s=window.currentStats;const rows=records.payments.slice(0,5);
 return `<section class="main-heading"><div><span class="eyebrow">Portfolio snapshot · ${escapeHtml(s.month)}</span><h1>Good to have you here.</h1><p>Here is what is happening across your properties.</p></div><button class="button" data-create="properties">+ Add a property</button></section><section class="metrics"><article class="metric"><div class="meta">Total properties <span class="pictogram">⌂</span></div><strong>${s.properties}</strong><small>In your workspace</small></article><article class="metric"><div class="meta">Active leases <span class="pictogram">▤</span></div><strong>${s.active_leases}</strong><small>Active this month</small></article><article class="metric"><div class="meta">Rent received <span class="pictogram">↗</span></div><strong>${money(s.received)}</strong><small>Recorded this month</small></article><article class="metric"><div class="meta">Rent-month balance <span class="pictogram">◷</span></div><strong>${money(s.outstanding)}</strong><small>Bills after allocated payments</small></article></section><section class="content-grid"><article class="panel"><div class="panel-title"><h2>Recent payments</h2><span>${s.month}</span></div>${rows.length?`<div class="table-scroll"><table><thead><tr><th>Tenant</th><th>Date</th><th>Amount</th><th>Method</th></tr></thead><tbody>${rows.map(r=>`<tr><td><strong>${escapeHtml(r.tenant)}</strong></td><td>${escapeHtml(r.paid_on)}</td><td>${money(r.amount)}</td><td><span class="pill">${escapeHtml(r.method)}</span></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty"><div>◷</div>No payment records yet.<br>Record one when a tenant pays offline.</div>'}</article><article class="panel"><div class="panel-title"><h2>Quick actions</h2></div><div class="quick-actions"><button data-create="properties" class="quick-action"><span class="quick-icon">⌂</span> Add a new property ↗</button><button data-create="tenants" class="quick-action"><span class="quick-icon">♙</span> Add a tenant ↗</button><button data-create="leases" class="quick-action"><span class="quick-icon">▤</span> Create a lease ↗</button><button data-create="payments" class="quick-action"><span class="quick-icon">↗</span> Record a rent payment ↗</button></div><div class="note"><strong>How this figure works</strong><br>${escapeHtml(s.assumptions)}<br><br><strong>Allocated to this rent month:</strong> ${money(s.allocated)}. <strong>Legacy payments awaiting allocation:</strong> ${money(s.unallocated)}. To assign old payments, open Rent ledger and click Edit.</div></article></section>`;
}
function renderRecords(){
 const [title,subtitle]=headings[active];
 const data=records[active];
 const colsByType={properties:['Property','Location','Units'],tenants:['Name','Email','Phone'],leases:['Property','Tenant','Monthly rent','Start','End'],payments:['Tenant','Amount','Payment date','Rent month','Method','Status']};
 const rows=data.map(r=>{
  if(active==='properties')return [r.name,r.location,r.units];
  if(active==='tenants')return [r.name,r.email||'—',r.phone||'—'];
  if(active==='leases')return [r.property,r.tenant,money(r.monthly_rent),r.start_date,r.end_date||'Ongoing'];
  return [r.tenant,money(r.amount),r.paid_on,r.billing_month||'Unallocated',r.method,r.voided?'Voided':'Recorded'];
 });
 return `<section class="main-heading"><div><span class="eyebrow">Your workspace</span><h1>${title}</h1><p>${subtitle}</p></div>${addButton(active)}</section><article class="panel list-panel"><div class="panel-title"><h2>All ${active}</h2><span>${data.length} record${data.length===1?'':'s'}</span></div>${data.length?`<div class="table-scroll"><table><thead><tr>${colsByType[active].map(c=>`<th>${escapeHtml(c)}</th>`).join('')}<th>Actions</th></tr></thead><tbody>${rows.map((r,i)=>`<tr>${r.map((value,j)=>`<td>${j===0?'<strong>':''}${escapeHtml(value)}${j===0?'</strong>':''}</td>`).join('')}<td class="action-cell">${active==='payments'?(data[i].voided?'<span class="muted">Voided</span>':`<button class="row-action" data-edit="${active}:${data[i].id}">Edit</button><button class="row-action danger" data-void="${data[i].id}">Void</button>`):`<button class="row-action" data-edit="${active}:${data[i].id}">Edit</button><button class="row-action danger" data-remove="${active}:${data[i].id}">Delete</button>`}</td></tr>`).join('')}</tbody></table></div>`:`<div class="empty"><div>✧</div>Nothing here yet.<br>Add your first record.</div>`}</article>${active==='payments'?'<div class="note">Older payments created in v0.1 are intentionally left unallocated. Choose Edit and assign their correct rent month before relying on billing balances. Voiding retains an audit record.</div>':''}`;
}

function renderInvoices(){
 const report=window.currentInvoices;
 return `<section class="main-heading"><div><span class="eyebrow">Monthly rental records</span><h1>Rent bills</h1><p>Review what is due and what was allocated to each rent month.</p></div><div class="field compact-month"><label for="invoiceMonth">Billing month</label><input id="invoiceMonth" type="month" value="${escapeHtml(selectedMonth)}"></div></section><section class="metrics"><article class="metric"><div class="meta">Rent due</div><strong>${money(report.expected)}</strong><small>Full monthly lease charges</small></article><article class="metric"><div class="meta">Rent allocated</div><strong>${money(report.allocated)}</strong><small>Against selected billing month</small></article><article class="metric"><div class="meta">Balance due</div><strong>${money(report.outstanding)}</strong><small>Does not include other months</small></article><article class="metric"><div class="meta">Unallocated records</div><strong>${money(report.unallocated)}</strong><small>Assign legacy records in Rent ledger</small></article></section><article class="panel list-panel"><div class="panel-title"><h2>${escapeHtml(report.month)} rent bills</h2><span>${report.invoices.length} record(s)</span></div>${report.invoices.length?`<div class="table-scroll"><table><thead><tr><th>Property</th><th>Tenant</th><th>Due</th><th>Allocated</th><th>Balance</th><th>Credit</th><th>Status</th></tr></thead><tbody>${report.invoices.map(i=>`<tr><td>${escapeHtml(i.property)}</td><td>${escapeHtml(i.tenant)}</td><td>${money(i.due)}</td><td>${money(i.paid)}</td><td>${money(i.balance)}</td><td>${money(i.credit)}</td><td>${escapeHtml(i.status)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">No lease charges for the selected month.</div>'}</article><div class="note">${escapeHtml(report.note)}</div>`;
}

function renderAudit(){
 const events=window.auditEvents;
 return `<section class="main-heading"><div><span class="eyebrow">Tracked record changes</span><h1>Activity log</h1><p>Latest 100 create, edit, delete, correction and void events.</p></div></section><article class="panel list-panel">${events.length?`<div class="table-scroll"><table><thead><tr><th>Recorded at (UTC)</th><th>Record type</th><th>Record ID</th><th>Action</th></tr></thead><tbody>${events.map(e=>`<tr><td>${escapeHtml(e.timestamp)}</td><td>${escapeHtml(e.entity)}</td><td>${e.entity_id}</td><td>${escapeHtml(e.action)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">No activity logged yet.</div>'}</article><div class="note">Local demonstration log; not a tamper-proof compliance audit trail. Changes remain in the local database.</div>`;
}
function input(label,name,type='text',placeholder='',extra=''){return `<div class="field"><label for="field-${name}">${label}</label><input id="field-${name}" name="${name}" type="${type}" placeholder="${placeholder}" ${extra} required></div>`;}
function selectInput(label,name,items){return `<div class="field"><label for="field-${name}">${label}</label><select id="field-${name}" name="${name}" required><option value="">Choose ${label.toLowerCase()}</option>${items.map(x=>`<option value="${x.id}">${escapeHtml(x.name)}</option>`).join('')}</select></div>`;}
function openForm(type,record=null){
 let form='';
 if(type==='properties')form=input('Property name','name','text','e.g. Riverfront Apartments','minlength="2"')+input('Location','location','text','e.g. Kochi, Kerala','minlength="2"')+input('Number of units','units','number','1','min="1" max="1000" value="1"');
 if(type==='tenants')form=input('Tenant name','name','text','e.g. Asha Kumar','minlength="2"')+`<div class="field"><label for="field-email">Email (optional)</label><input id="field-email" name="email" type="email" placeholder="tenant@example.com"></div><div class="field"><label for="field-phone">Phone (optional)</label><input id="field-phone" name="phone" type="tel" placeholder="Phone number"></div>`;
 if(type==='leases')form=selectInput('Property','property_id',records.properties)+selectInput('Tenant','tenant_id',records.tenants)+input('Monthly rent in INR','monthly_rent','number','15000','min="0.01" step="0.01"')+`<div class="two-fields">${input('Start date','start_date','date','','value="'+today()+'"')}<div class="field"><label for="field-end_date">End date (optional)</label><input id="field-end_date" name="end_date" type="date"></div></div>`;
 if(type==='payments')form=selectInput('Lease','lease_id',records.leases.map(x=>({...x,name:x.tenant+' · '+x.property})))+input('Amount in INR','amount','number','15000','min="0.01" step="0.01"')+`<div class="two-fields">${input('Payment date','paid_on','date','','value="'+today()+'"')}<div class="field"><label for="field-billing_month">Rent month (required)</label><input id="field-billing_month" name="billing_month" type="month" value="${new Date().toISOString().slice(0,7)}" required></div></div><div class="field"><label for="field-method">Method</label><select id="field-method" name="method"><option>bank transfer</option><option>upi</option><option>cash</option><option>other</option></select></div><div class="field"><label for="field-note">Note (optional)</label><input id="field-note" name="note" placeholder="e.g. November rent"></div>`;
 if((type==='leases'&&(!records.properties.length||!records.tenants.length))||(type==='payments'&&!records.leases.length)){toast(type==='leases'?'Add a property and tenant before creating a lease.':'Create a lease before recording a payment.',true);return;}
 dialog.hidden=false;
 dialog.innerHTML=`<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle"><div class="modal-heading"><div><span class="eyebrow">Rental workspace</span><h2 id="modalTitle">${record?'Edit '+type.slice(0,-1):headings[type][2]}</h2><p>Use fictional data. Changes are recorded in Activity log.</p></div><button id="closeModal" class="icon-button" aria-label="Close dialog">×</button></div><form id="recordForm">${form}<div class="modal-end"><button type="button" class="button secondary" id="cancelModal">Cancel</button><button class="button" type="submit">${record?'Save changes':'Save record'} →</button></div></form></div>`;
 document.getElementById('closeModal').onclick=closeModal;document.getElementById('cancelModal').onclick=closeModal;
 if(record){
  for(const [key,val] of Object.entries(record)){
   const control=document.getElementById('recordForm').elements.namedItem(key);
   if(control && val !== null && val !== undefined)control.value=val;
  }
 }
 document.getElementById('recordForm').onsubmit=async e=>{e.preventDefault();const payload=Object.fromEntries(new FormData(e.target));for(const k of ['units','property_id','tenant_id','lease_id'])if(k in payload)payload[k]=Number(payload[k]);for(const k of ['start_date','end_date'])if(payload[k]==='')payload[k]=null;try{await api(type+(record?'/'+record.id:''),payload,record?'PUT':'POST');closeModal();await refresh();toast(record?'Changes saved.':'Record saved.');}catch(err){toast(err.message,true);}};
}

async function removeRecord(key){
 const [type,id]=key.split(':');
 if(!window.confirm('Delete this '+type.slice(0,-1)+'? Linked records may prevent deletion.'))return;
 try{await api(type+'/'+id,undefined,'DELETE');await refresh();toast('Record deleted.');}catch(err){toast(err.message,true);}
}

async function voidRecord(id){
 const reason=window.prompt('Reason for voiding this payment? The original record remains in the history.');
 if(reason===null)return;
 if(reason.trim().length<3){toast('Enter a reason of at least 3 characters.',true);return;}
 if(!window.confirm('Void this payment? It will stop counting toward rent totals.'))return;
 try{await api('payments/'+id+'/void',{reason:reason.trim()});await refresh();toast('Payment voided with an activity record.');}catch(err){toast(err.message,true);}
}
function closeModal(){dialog.hidden=true;dialog.innerHTML='';}
dialog.addEventListener('click',e=>{if(e.target===dialog)closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!dialog.hidden)closeModal();});
initialize();
