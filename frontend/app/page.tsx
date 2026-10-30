"use client";

import { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, AlertTriangle, ArrowLeft, ArrowRight, Bot, CheckCircle2, ChevronRight, ClipboardCheck, FileText, Globe2, Leaf, LockKeyhole, MapPinned, Mic, Phone, Search, Settings, ShieldCheck, Sprout, UserPlus, Users, Waves } from "lucide-react";
import { Claim, FarmerRecord, FieldRecord, getAnalysis, getClaims, getFarmers, getFields, getSummary, Registration, registerFarm, SatelliteAnalysis, simulateVoice, Status, Summary } from "../lib/api";

type Screen = "Overview" | "Farm Explorer" | "Register Farm" | "Satellite Intelligence" | "Claims" | "AI Verification Calls" | "Verification Reports" | "Settings";
type DataState = { summary: Summary; fields: FieldRecord[]; claims: Claim[]; farmers: FarmerRecord[]; source: "live" | "preview" };

const nav: { name: Screen; icon: typeof Activity }[] = [
  { name: "Overview", icon: Activity }, { name: "Farm Explorer", icon: Globe2 }, { name: "Register Farm", icon: UserPlus }, { name: "Satellite Intelligence", icon: Waves },
  { name: "Claims", icon: ClipboardCheck }, { name: "AI Verification Calls", icon: Mic }, { name: "Verification Reports", icon: FileText }, { name: "Settings", icon: Settings },
];
const colors: Record<string, string> = { WITHIN_TOLERANCE: "#68e1a5", REVIEW_REQUIRED: "#f5bf60", INSUFFICIENT_EVIDENCE: "#ff8f85", PENDING: "#86a9e8", HUMAN_REVIEW: "#86a9e8" };

function StatusBadge({ status }: { status: Status }) { return <span className={`status ${status}`}>{status.replaceAll("_", " ")}</span>; }
function fmt(date: string) { return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" }).format(new Date(date)); }

type SessionUser = { name: string; phone: string; createdAt: string };

export default function AgriVerifyApp() {
  const [session, setSession] = useState<SessionUser | null>(null);
  const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("agriverify-demo-session");
      if (stored) setSession(JSON.parse(stored) as SessionUser);
    } catch { /* A blocked local-storage context simply presents the sign-in screen. */ }
    setSessionReady(true);
  }, []);

  function signIn(user: SessionUser) {
    window.localStorage.setItem("agriverify-demo-session", JSON.stringify(user));
    setSession(user);
  }

  function signOut() {
    window.localStorage.removeItem("agriverify-demo-session");
    setSession(null);
  }

  if (!sessionReady) return <main className="auth-page"><div className="auth-loading">Loading AgriVerify…</div></main>;
  if (!session) return <PhoneAuth onAuthenticated={signIn} />;
  return <Dashboard onSignOut={signOut} />;
}

function Dashboard({ onSignOut }: { onSignOut: () => void }) {
  const [screen, setScreen] = useState<Screen>("Overview");
  const [state, setState] = useState<DataState | null>(null);
  const [selectedField, setSelectedField] = useState("TX-001");
  const [analysis, setAnalysis] = useState<SatelliteAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { void refresh(); }, []);
  useEffect(() => { if (state) void refreshAnalysis(selectedField); }, [selectedField, state]);
  // quiet: refresh after a save without swapping the page for the loading card, so the form keeps its result message
  async function refresh(quiet = false) {
    if (!quiet) setLoading(true);
    const [summary, fields, claims, farmers] = await Promise.all([getSummary(), getFields(), getClaims(), getFarmers()]);
    setState({ summary: summary.data, fields: fields.data, claims: claims.data, farmers: farmers.data, source: summary.source === "live" && fields.source === "live" && claims.source === "live" ? "live" : "preview" });
    setLoading(false);
  }
  async function refreshAnalysis(id: string) { setAnalysis(null); const response = await getAnalysis(id); setAnalysis(response.data); }
  const field = state?.fields.find((item) => item.id === selectedField) || state?.fields[0];
  if (loading || !state) return <main className="main"><div className="card" style={{maxWidth:480, margin:"14vh auto"}}><Leaf className="leaf"/><h1>Preparing AgriVerify</h1><p className="card-sub">Loading verification records and evidence provenance…</p></div></main>;

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><Leaf className="leaf" size={25}/> AgriVerify</div>
      <div className="nav-label">Verification workspace</div>
      <nav className="nav">{nav.map(({name, icon: Icon}) => <button key={name} className={screen === name ? "active" : ""} onClick={() => setScreen(name)}><Icon size={16}/>{name}</button>)}</nav>
      <div className="sidebar-foot"><b>AgriVerify Intelligence Engine</b><br/>Human decision support only.<br/>Satellite estimates are probabilistic.</div>
    </aside>
    <main className="main">
      <header className="topbar"><div><div className="eyebrow">Insurance verification workspace</div><h1>{screen}</h1></div><div className="online"><span className="dot"/>{state.source === "live" ? "LOCAL API CONNECTED" : "STATIC PREVIEW — API OFFLINE"}</div></header>
      {state.source === "preview" && <div className="notice"><AlertTriangle size={15}/><span><b>Preview dataset.</b> This hosted/static view shows explicitly synthetic demo records. Start the local API to access live claim creation, verification, and PDF reports.</span></div>}
      {screen === "Overview" && <Overview data={state} setScreen={setScreen} />}
      {screen === "Farm Explorer" && field && <FarmExplorer fields={state.fields} claims={state.claims} field={field} onField={setSelectedField} onSatellite={() => setScreen("Satellite Intelligence")} />}
      {screen === "Register Farm" && <RegisterFarm farmers={state.farmers} onDone={() => refresh(true)} onOpenField={(id) => { setSelectedField(id); setScreen("Satellite Intelligence"); }} />}
      {screen === "Satellite Intelligence" && field && <SatellitePage field={field} fields={state.fields} claims={state.claims} analysis={analysis} onField={setSelectedField} />}
      {screen === "Claims" && <ClaimsPage claims={state.claims} fields={state.fields} onSatellite={(id) => {setSelectedField(id);setScreen("Satellite Intelligence");}} />}
      {screen === "AI Verification Calls" && <VoiceCalls initialField={selectedField} fields={state.fields} onCreated={() => refresh(true)} />}
      {screen === "Verification Reports" && <Reports claims={state.claims} />}
      {screen === "Settings" && <SettingsPage connected={state.source === "live"} onSignOut={onSignOut} />}
    </main>
  </div>;
}

function PhoneAuth({ onAuthenticated }: { onAuthenticated: (user: SessionUser) => void }) {
  const [mode, setMode] = useState<"choose" | "signin" | "signup" | "verify">("choose");
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const creating = mode === "signup";

  function startVerification(event: React.FormEvent) {
    event.preventDefault();
    const digits = phone.replace(/\D/g, "");
    if (digits.length < 8 || digits.length > 15) { setError("Enter a valid phone number, including country code."); return; }
    if (mode === "signup" && name.trim().length < 2) { setError("Enter your name to create an account."); return; }
    setError(""); setCode(""); setMode("verify");
  }

  function verify(event: React.FormEvent) {
    event.preventDefault();
    if (code !== "246810") { setError("That demo code is not valid. Use 246810."); return; }
    onAuthenticated({ name: name.trim() || "AgriVerify reviewer", phone, createdAt: new Date().toISOString() });
  }

  const copy = mode === "choose" ? { eyebrow: "Crop intelligence for human review", title: "Verify the field.\nProtect the farmer.", text: "A secure workspace for evidence-led planting verification." } : mode === "verify" ? { eyebrow: "Phone verification", title: "One more\nsecure step.", text: "Confirm your phone number before opening the verification workspace." } : { eyebrow: creating ? "Create your workspace" : "Welcome back", title: creating ? "Build trust\nfrom the ground up." : "Continue your\nreview work.", text: "Use your phone number to access AgriVerify." };

  return <main className="auth-page">
    <section className="auth-art"><div className="auth-brand"><Leaf size={25}/> AgriVerify</div><div className="auth-copy"><div className="eyebrow">{copy.eyebrow}</div><h1>{copy.title.split("\n").map((line) => <span key={line}>{line}</span>)}</h1><p>{copy.text}</p></div><div className="auth-evidence"><span><ShieldCheck size={15}/> Evidence-first reviews</span><span><Waves size={15}/> Satellite Intelligence</span><span><Mic size={15}/> Farmer Voice Verification</span></div><div className="auth-orbit orbit-one"/><div className="auth-orbit orbit-two"/><div className="auth-field"/></section>
    <section className="auth-panel"><div className="auth-card">
      {mode !== "choose" && <button className="auth-back" onClick={() => { setMode("choose"); setError(""); }}><ArrowLeft size={15}/> Back</button>}
      {mode === "choose" && <><div className="auth-kicker">AgriVerify access</div><h2>Welcome to your verification workspace.</h2><p className="auth-muted">Choose how you’d like to continue.</p><button className="auth-primary" onClick={() => setMode("signin")}><Phone size={17}/> Sign in with phone <ArrowRight size={17}/></button><button className="auth-secondary" onClick={() => setMode("signup")}><UserPlus size={17}/> Create an account</button><p className="auth-footnote"><LockKeyhole size={13}/> Your number stays in this browser in demo mode.</p></>}
      {(mode === "signin" || mode === "signup") && <form onSubmit={startVerification}><div className="auth-kicker">{creating ? "New reviewer account" : "Phone sign in"}</div><h2>{creating ? "Create your AgriVerify account" : "Sign in to AgriVerify"}</h2><p className="auth-muted">{creating ? "Set up a local demo account using your phone number." : "Enter the phone number associated with your workspace."}</p>{creating && <label className="auth-label">Full name<input value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Priya Shah" autoComplete="name"/></label>}<label className="auth-label">Phone number<input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+1 555 123 4567" inputMode="tel" autoComplete="tel"/></label>{error && <p className="auth-error">{error}</p>}<button className="auth-primary" type="submit">Continue <ArrowRight size={17}/></button><p className="auth-switch">{creating ? "Already have an account?" : "New to AgriVerify?"} <button type="button" onClick={() => {setMode(creating ? "signin" : "signup"); setError("");}}>{creating ? "Sign in" : "Create one"}</button></p></form>}
      {mode === "verify" && <form onSubmit={verify}><div className="auth-kicker">Demo phone verification</div><h2>Enter the verification code</h2><p className="auth-muted">We would send a one-time code to <b>{phone}</b>. SMS delivery is not configured in this demo, so use the test code below.</p><div className="demo-code">Demo code: <b>246810</b></div><label className="auth-label">Six-digit code<input value={code} onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="000000" inputMode="numeric" autoComplete="one-time-code"/></label>{error && <p className="auth-error">{error}</p>}<button className="auth-primary" type="submit">Verify and enter workspace <ArrowRight size={17}/></button><p className="auth-footnote"><LockKeyhole size={13}/> For production, connect a verified SMS provider; no text is sent by this demo.</p></form>}
    </div></section>
  </main>;
}

function Overview({ data, setScreen }: { data: DataState; setScreen: (screen: Screen) => void }) {
  const s = data.summary;
  const metrics = [
    ["Registered farms", s.total_registered_farms, "synthetic demo farms", Sprout, "var(--green)"], ["Submitted claims", s.total_submitted_claims, "all verification records", ClipboardCheck, "#b3b9ff"],
    ["Within tolerance", s.claims_within_review_tolerance, "illustrative review policy", CheckCircle2, "var(--green)"], ["Needs investigation", s.claims_requiring_investigation, "human review recommended", AlertTriangle, "var(--amber)"],
  ] as const;
  const dist = Object.entries(s.status_distribution).filter(([, value]) => value > 0).map(([name, value]) => ({ name: name.replaceAll("_", " "), raw:name, value }));
  return <>
    <div className="grid metrics">{metrics.map(([label, value, trend, Icon, color]) => <section className="card metric" key={label}><Icon size={17} color={color}/><div className="value">{value}</div><div className="eyebrow" style={{marginTop:4}}>{label}</div><div className="trend"><strong>●</strong> {trend}</div></section>)}</div>
    <div className="grid dash-grid">
      <section className="card"><div className="card-title">Verification activity</div><div className="card-sub">NDVI-supported outcomes in the seeded demonstration set</div><div className="chart-wrap"><ResponsiveContainer><AreaChart data={[{month:"May 01",activity:0},{month:"May 08",activity:1},{month:"May 15",activity:1},{month:"May 22",activity:2},{month:"May 29",activity:3},{month:"Jun 05",activity:3}]}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#68e1a5" stopOpacity={.55}/><stop offset="100%" stopColor="#68e1a5" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false}/><XAxis dataKey="month" tickLine={false} axisLine={false}/><YAxis hide domain={[0,4]}/><Tooltip/><Area type="monotone" dataKey="activity" stroke="#68e1a5" fill="url(#fill)" strokeWidth={2}/></AreaChart></ResponsiveContainer></div></section>
      <section className="card"><div className="card-title">Claim status distribution</div><div className="card-sub">Rule outputs, not coverage decisions</div><div className="chart-wrap"><ResponsiveContainer><PieChart><Pie data={dist} dataKey="value" innerRadius="56%" outerRadius="80%" paddingAngle={4}>{dist.map((entry) => <Cell key={entry.raw} fill={colors[entry.raw]}/>)}</Pie><Tooltip/></PieChart></ResponsiveContainer></div><div style={{display:"flex",gap:9,flexWrap:"wrap",justifyContent:"center"}}>{dist.map(item=><span className="meta" key={item.raw}><i className="swatch" style={{background:colors[item.raw],display:"inline-block",marginRight:4}}/>{item.name}</span>)}</div></section>
    </div>
    <div className="grid dash-grid"><section className="card"><div className="card-title">Recent verification activity</div><div className="activity">{s.recent_claims.map((item) => <div className="activity-row" key={item.id}><i className="swatch" style={{background:colors[item.status]}}/><div><b>{item.field_id}</b><div className="meta">{item.id} · {fmt(item.submitted_at)}</div></div><StatusBadge status={item.status}/></div>)}</div></section><section className="card"><div className="card-title">Review queue</div><div className="card-sub">Claims that need a qualified human decision</div><div style={{fontSize:48,fontWeight:800,letterSpacing:"-.08em",marginTop:22,color:"var(--amber)"}}>{s.pending_human_reviews}</div><p className="card-sub" style={{lineHeight:1.5}}>Satellite evidence never approves, denies, or determines coverage.</p><button className="small-btn" onClick={() => setScreen("Claims")}>Open claims queue <ChevronRight size={13}/></button></section></div>
  </>;
}

function FarmExplorer({ fields, claims, field, onField, onSatellite }: { fields: FieldRecord[]; claims: Claim[]; field: FieldRecord; onField:(id:string)=>void; onSatellite:()=>void }) {
  const latest = claims.find((claim)=>claim.field_id===field.id);
  return <><div className="section-header"><div><div className="eyebrow">Geospatial field record</div><h2>Farm Explorer</h2></div><div className="filters"><div className="input"><Search size={14} style={{verticalAlign:"middle",marginRight:6}}/>Texas coordinate search</div></div></div><div className="explorer"><section className="card map"><div className="gridmap"/><div className="map-label"><MapPinned size={13} style={{verticalAlign:"middle",marginRight:5}}/>2D fallback — Cesium globe is enabled in local build configuration</div><div className="field-shape"/><div className="marker"/><div className="coord">{field.latitude.toFixed(4)}°, {field.longitude.toFixed(4)}° · WGS 84</div></section><section className="card"><div className="demo-tag">SYNTHETIC DEMO FIELD</div><h2 style={{fontSize:20,letterSpacing:"-.04em",margin:"13px 0 3px"}}>{field.id}</h2><div className="card-sub">{field.name}</div><div className="detail-grid"><div><div className="detail-key">Crop</div><div className="detail-value">{field.crop_type}</div></div><div><div className="detail-key">Field area</div><div className="detail-value">{field.area_hectares} ha</div></div><div><div className="detail-key">Latest claim</div><div className="detail-value">{latest?.id || "None"}</div></div><div><div className="detail-key">Verification</div>{latest && <StatusBadge status={latest.status}/>}</div></div><button className="primary-btn" onClick={onSatellite}>View Satellite Intelligence</button></section></div><section className="card" style={{marginTop:16}}><div className="card-title">Registered Texas fields</div><div className="field-list">{fields.map(item=><button key={item.id} className={`field-item ${item.id===field.id?"active":""}`} onClick={()=>onField(item.id)}><b>{item.id} · {item.name}</b><span>{item.crop_type} · {item.area_hectares} hectares · {item.latitude.toFixed(3)}°, {item.longitude.toFixed(3)}°</span></button>)}</div></section></>;
}

function SatellitePage({ field, fields, claims, analysis, onField }: { field: FieldRecord; fields: FieldRecord[]; claims: Claim[]; analysis: SatelliteAnalysis | null; onField: (id:string)=>void }) {
  const claim = claims.find((item)=>item.field_id===field.id); const chart = analysis?.observations.map(item=>({date:item.acquisition_date.slice(5),ndvi:item.ndvi,savi:item.additional_indices.savi,cloud:item.cloud_coverage})) || [];
  return <><div className="section-header"><div><div className="eyebrow">Satellite Intelligence</div><h2>{field.id} · {field.name}</h2></div><select className="input" value={field.id} onChange={(event)=>onField(event.target.value)}>{fields.map(item=><option key={item.id} value={item.id}>{item.id} · {item.name}</option>)}</select></div>{!analysis ? <section className="card"><div className="empty">Loading analysis and provenance…</div></section> : <><div className="notice"><AlertTriangle size={15}/><span><b>{analysis.is_demo_data ? "Synthetic demo series." : "Earth Engine analysis."}</b> {analysis.is_demo_data ? "Values are clearly generated for local demonstration and are not satellite-derived evidence." : "Processing uses cloud-screened Sentinel-2 surface reflectance."}</span></div><div className="sat-grid"><section className="card"><div className="card-title">Vegetation index history</div><div className="card-sub">NDVI is B8 (NIR) minus B4 (red), divided by their sum.</div><div className="chart-wrap"><ResponsiveContainer><AreaChart data={chart}><defs><linearGradient id="ndvi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#68e1a5" stopOpacity={.5}/><stop offset="1" stopColor="#68e1a5" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false}/><XAxis dataKey="date" tickLine={false} axisLine={false}/><YAxis domain={[0,.55]} tickLine={false} axisLine={false}/><Tooltip/><Area dataKey="ndvi" stroke="#68e1a5" fill="url(#ndvi)" strokeWidth={2}/><Area dataKey="savi" stroke="#9ba8ff" fill="transparent" strokeDasharray="4 4"/></AreaChart></ResponsiveContainer></div></section><section className="card"><div className="demo-tag">{analysis.evidence_quality}</div><div className="detail-grid"><div><div className="detail-key">Data source</div><div className="detail-value">{analysis.satellite_data_source}</div></div><div><div className="detail-key">Processing</div><div className="detail-value">{analysis.processing_status}</div></div><div><div className="detail-key">Reported date</div><div className="detail-value">{claim?.reported_planting_date || "—"}</div></div><div><div className="detail-key">Estimated window</div><div className="detail-value">{analysis.estimated_planting_window ? `${analysis.estimated_planting_window.start} → ${analysis.estimated_planting_window.end}` : "Insufficient evidence"}</div></div></div><div className="card-sub" style={{lineHeight:1.5}}>{analysis.limitations[0]}</div></section></div><section className="card" style={{marginTop:16}}><div className="card-title">Observation timeline</div><div className="timeline">{chart.map((item,index)=><div key={item.date}><div className={`time-dot ${claim && item.date===claim.reported_planting_date.slice(5)?"claim":""}`}/><div className="time-label">{item.date}<br/>NDVI {item.ndvi?.toFixed(2)}</div></div>)}</div></section></>}</>;
}

function ClaimsPage({ claims, fields, onSatellite }: { claims: Claim[]; fields: FieldRecord[]; onSatellite: (fieldId: string)=>void }) { const [filter,setFilter]=useState("ALL");const [query,setQuery]=useState("");const list=useMemo(()=>claims.filter(c=>(filter==="ALL"||c.status===filter)&&(`${c.id} ${c.field_id} ${c.farmer_id}`.toLowerCase().includes(query.toLowerCase()))),[claims,filter,query]);return <><div className="section-header"><div><div className="eyebrow">Claim management</div><h2>Verification queue</h2></div><div className="filters"><input className="input" placeholder="Search field or claim" value={query} onChange={e=>setQuery(e.target.value)}/><select className="input" value={filter} onChange={e=>setFilter(e.target.value)}><option>ALL</option><option>WITHIN_TOLERANCE</option><option>REVIEW_REQUIRED</option><option>INSUFFICIENT_EVIDENCE</option></select></div></div><section className="card"><table className="table"><thead><tr><th>Claim</th><th>Farm</th><th>Reported planting</th><th>Status</th><th>Action</th></tr></thead><tbody>{list.map(claim=><tr key={claim.id}><td><b>{claim.id}</b><div className="meta">{claim.farmer_id}</div></td><td>{claim.field_id}<div className="meta">{fields.find(f=>f.id===claim.field_id)?.name}</div></td><td>{claim.reported_planting_date}</td><td><StatusBadge status={claim.status}/></td><td><button className="linkish" onClick={()=>onSatellite(claim.field_id)}>Inspect evidence →</button></td></tr>)}</tbody></table>{list.length===0&&<div className="empty">No claims match this filter.</div>}</section></>}

function VoiceCalls({ initialField, fields, onCreated }: { initialField: string; fields: FieldRecord[]; onCreated: () => Promise<void> }) { const [farm,setFarm]=useState(initialField);const crop=fields.find(item=>item.id===farm)?.crop_type||"Cotton";const [date,setDate]=useState("2025-05-25");const [language,setLanguage]=useState("en");const [result,setResult]=useState("");const [busy,setBusy]=useState(false);async function submit(){setBusy(true);setResult("");try{const output=await simulateVoice({farm_id:farm,crop_type:crop,planting_date:date,language});setResult(`Simulation completed. Claim ${output.claim_id} is ${output.verification.status.replaceAll("_"," ")}.`);await onCreated();}catch(error){setResult(error instanceof Error?error.message:"Simulation failed.");}finally{setBusy(false)}}return <><div className="section-header"><div><div className="eyebrow">Conversational Voice AI</div><h2>AI Verification Calls</h2></div><span className="demo-tag">TEXT SIMULATOR</span></div><div className="notice"><Bot size={15}/><span>The simulator follows the same backend business operations as a phone call. It is not a live call. Configure Bolna credentials and its agent separately for live voice verification.</span></div><div className="call-sim"><section className="card"><div className="card-title">AgriVerify AI Assistant</div><div className="card-sub">Create a test intake with a confirmed date.</div><div className="form-stack"><label>Farm ID<select className="input" value={farm} onChange={e=>setFarm(e.target.value)}>{fields.map(item=><option key={item.id} value={item.id}>{item.id} · {item.name}</option>)}</select></label><label>Crop<input className="input" value={crop} disabled/></label><label>Confirmed planting date<input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)}/></label><label>Language preference<select className="input" value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="hi">Hindi (requires live-agent validation)</option><option value="mr">Marathi (requires live-agent validation)</option></select></label><button className="primary-btn" disabled={busy} onClick={submit}>{busy?"Verifying…":"Run intake simulation"}</button></div>{result&&<div className="result">{result}</div>}</section><section className="card"><div className="card-title">Example conversation</div><div className="transcript"><div className="utterance assistant">Hello, welcome to AgriVerify. I can help record crop planting information for review. Could you tell me your farm ID?</div><div className="utterance farmer">{farm}. Cotton.</div><div className="utterance assistant">Thank you. What date did you plant the cotton? I’ll confirm the date before submitting.</div><div className="utterance farmer">{date}</div><div className="utterance assistant">I will use available observations to estimate a planting window. This supports human review and does not determine coverage.</div></div></section></div></>}

function RegisterFarm({ farmers, onDone, onOpenField }: { farmers: FarmerRecord[]; onDone: () => Promise<void>; onOpenField: (id: string) => void }) {
  const [farmerId, setFarmerId] = useState("");
  const [form, setForm] = useState({ name: "", phone: "", language: "en", crop: "Cotton", fieldName: "", lat: "", lon: "", area: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<Registration | null>(null);
  const set = (key: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm({ ...form, [key]: event.target.value });
  const existing = farmers.find((item) => item.id === farmerId);

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setError(""); setDone(null);
    const latitude = Number(form.lat), longitude = Number(form.lon), area = Number(form.area);
    if (!farmerId && (form.name.trim().length < 2 || !form.phone.trim())) return setError("Enter the farmer's name and phone number, or choose an existing farmer.");
    if (form.fieldName.trim().length < 2 || form.crop.trim().length < 2) return setError("Enter a field name and a crop.");
    if (!form.lat || !form.lon || !form.area || Number.isNaN(latitude + longitude + area)) return setError("Enter latitude, longitude and area as numbers.");
    if (Math.abs(latitude) > 85 || Math.abs(longitude) > 180) return setError("Latitude must be between -85 and 85, longitude between -180 and 180.");
    if (area <= 0 || area > 1000) return setError("Area must be above 0 and at most 1000 hectares.");
    setBusy(true);
    try {
      const result = await registerFarm({ ...(farmerId ? { farmer_id: farmerId } : { name: form.name.trim(), phone_number: form.phone.trim() }), preferred_language: existing?.preferred_language || form.language, crop_type: form.crop.trim(), field_name: form.fieldName.trim(), latitude, longitude, area_hectares: area });
      setDone(result);
      setFarmerId(result.farmer.id);
      setForm({ ...form, fieldName: "", lat: "", lon: "", area: "" });
      await onDone();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Registration failed."); }
    finally { setBusy(false); }
  }

  return <><div className="section-header"><div><div className="eyebrow">Enrollment</div><h2>New farmer or new field</h2></div></div>
    <div className="call-sim">
      <section className="card"><div className="card-title">Farmer and field</div><div className="card-sub">Creates the farmer (or adds a field to an existing one) and the field boundary.</div>
        <form className="form-stack" onSubmit={submit}>
          <label>Farmer<select className="input" value={farmerId} onChange={(event) => setFarmerId(event.target.value)}><option value="">New farmer</option>{farmers.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.id.slice(0, 8)}</option>)}</select></label>
          {!farmerId && <><label>Full name<input className="input" value={form.name} onChange={set("name")} placeholder="e.g. Asha Rao" autoComplete="off"/></label>
            <label>Phone number (with country code)<input className="input" value={form.phone} onChange={set("phone")} placeholder="+91 98765 43210" inputMode="tel" autoComplete="off"/></label>
            <label>Language<select className="input" value={form.language} onChange={set("language")}><option value="en">English</option><option value="hi">Hindi (requires live-agent validation)</option><option value="mr">Marathi (requires live-agent validation)</option></select></label></>}
          <label>Field name<input className="input" value={form.fieldName} onChange={set("fieldName")} placeholder="e.g. North plot" autoComplete="off"/></label>
          <label>Crop<input className="input" value={form.crop} onChange={set("crop")}/></label>
          <label>Latitude (centre of field)<input className="input" value={form.lat} onChange={set("lat")} placeholder="33.5779" inputMode="decimal"/></label>
          <label>Longitude (centre of field)<input className="input" value={form.lon} onChange={set("lon")} placeholder="-101.8552" inputMode="decimal"/></label>
          <label>Area (hectares)<input className="input" value={form.area} onChange={set("area")} placeholder="12.5" inputMode="decimal"/></label>
          {error && <div className="notice" role="alert"><AlertTriangle size={15}/><span>{error}</span></div>}
          <button className="primary-btn" type="submit" disabled={busy}>{busy ? "Registering…" : "Register farm"}</button>
        </form>
        {done && <div className="result" role="status"><b>Registered.</b> {done.farmer.name} · field <b>{done.field.id}</b> ({done.field.area_hectares} ha).<div style={{marginTop:8}}><button className="small-btn" onClick={() => onOpenField(done.field.id)}>View satellite data <ChevronRight size={13}/></button></div>{done.demo_mode && <div className="meta" style={{marginTop:8}}>Demo mode is on, so no satellite data is fetched for this field. Set AGRIVERIFY_DEMO_MODE=false to use real imagery.</div>}</div>}
      </section>
      <section className="card"><div className="card-title">How the boundary is made</div>
        <p className="card-sub" style={{lineHeight:1.6}}>The field boundary is an <b>approximate square</b> of the area you enter, centred on the point you give. Real plots are rarely square, so treat satellite results for this field as indicative until a surveyed or drawn boundary replaces it.</p>
        <div className="card-title" style={{marginTop:18}}>Finding coordinates</div>
        <p className="card-sub" style={{lineHeight:1.6}}>In Google Maps, right-click the middle of the field and click the coordinates shown at the top of the menu to copy them. The first number is latitude, the second longitude.</p>
        <div className="card-title" style={{marginTop:18}}>Phone number</div>
        <p className="card-sub" style={{lineHeight:1.6}}>The phone number identifies the farmer, so each number can be registered only once. To add a second field, choose the farmer from the list.</p>
      </section>
    </div></>;
}

function Reports({ claims }: { claims: Claim[] }) { return <><div className="section-header"><div><div className="eyebrow">Generated records</div><h2>Verification Reports</h2></div><span className="demo-tag">PDF AVAILABLE LOCALLY</span></div><section className="card"><div className="card-title">Report generation</div><p className="card-sub" style={{lineHeight:1.6,maxWidth:740}}>A local report includes evidence provenance, satellite-derived interval, rule outcome, limitations, and the required human-review disclaimer. Static hosting cannot proxy the local PDF endpoint.</p><table className="table"><thead><tr><th>Claim</th><th>Status</th><th>Report</th></tr></thead><tbody>{claims.map(claim=><tr key={claim.id}><td><b>{claim.id}</b><div className="meta">{claim.field_id}</div></td><td><StatusBadge status={claim.status}/></td><td><a className="linkish" href={`http://localhost:8000/api/v1/reports/${claim.id}/pdf`} target="_blank">Open local PDF ↗</a></td></tr>)}</tbody></table></section></>}

function SettingsPage({ connected, onSignOut }: { connected: boolean; onSignOut: () => void }) { return <><div className="section-header"><div><div className="eyebrow">Configuration and safeguards</div><h2>Settings</h2></div></div><section className="card"><div className="card-title">Integration status</div><div className="settings-list"><div className="setting"><div><h3>Offline demonstration dataset</h3><p>Three synthetic Texas cotton fields, claims, and NDVI series. Every generated observation carries demo provenance.</p></div><span className="value-badge">ENABLED</span></div><div className="setting"><div><h3>Conversational Voice AI</h3><p>Bolna adapter exists server-side. Set BOLNA_API_KEY and BOLNA_AGENT_ID for a live call; configure a public webhook in the agent’s Extractions tab.</p></div><span className="value-badge">{connected?"CHECK LOCAL ENV":"NOT CONNECTED"}</span></div><div className="setting"><div><h3>Satellite Intelligence</h3><p>Earth Engine is used only with an authorized service account and project. When unavailable, the application does not manufacture real satellite output.</p></div><span className="value-badge">CONFIGURATION REQUIRED</span></div><div className="setting"><div><h3>Access control</h3><p>Set API_KEY in the local environment to require X-API-Key for dashboard routes. The demo mode is intentionally not production security.</p></div><span className="value-badge">ENVIRONMENT CONTROLLED</span></div><div className="setting"><div><h3>Session</h3><p>Sign out to return to the phone-number access screen. This clears only the local demo session stored in this browser.</p></div><button className="small-btn" onClick={onSignOut}>Sign out</button></div></div></section></>}
