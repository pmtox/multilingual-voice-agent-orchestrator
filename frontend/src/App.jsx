import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [leads, setLeads] = useState([]);
  const [callbacks, setCallbacks] = useState([]);
  const [events, setEvents] = useState([]);
  const [phone, setPhone] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const responses = await Promise.all([
        fetch(`${API}/api/leads`), fetch(`${API}/api/callbacks`),
        fetch(`${API}/api/whatsapp-events`),
      ]);
      if (responses.some((response) => !response.ok)) throw new Error("Dashboard API is unavailable");
      const [leadRows, callbackRows, eventRows] = await Promise.all(responses.map((response) => response.json()));
      setLeads(leadRows); setCallbacks(callbackRows); setEvents(eventRows);
      setStatus("");
    } catch (error) { setStatus(error.message); }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function startCall(event) {
    event.preventDefault();
    setLoading(true); setStatus("Requesting outbound call…");
    try {
      const response = await fetch(`${API}/api/call`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to: phone }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Call request failed");
      setStatus(`Call started${result.callId ? ` · ${result.callId}` : ""}`);
    } catch (error) { setStatus(error.message); }
    finally { setLoading(false); }
  }

  return <main className="shell">
    <header className="header">
      <div><div className="eyebrow">VOICE AUTOMATION · OPERATIONS</div><h1>Agent overview</h1></div>
      <span className="live"><i /> LIVE DASHBOARD</span>
    </header>
    <form className="callbox" onSubmit={startCall}>
      <div><h2>Launch outbound call</h2><p>Use an international phone number, including country code.</p></div>
      <div className="callform">
        <input aria-label="Lead phone number" required minLength="5" value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="+91 98765 43210" />
        <button disabled={loading}>{loading ? "Starting…" : "Start call ↗"}</button>
      </div>
      {status && <p className="status" role="status">{status}</p>}
    </form>
    <section className="stats">
      <Stat label="Qualified leads" value={leads.length} />
      <Stat label="Callbacks booked" value={callbacks.length} />
      <Stat label="WhatsApp actions" value={events.length} />
    </section>
    <section className="columns">
      <Panel title="Lead pipeline" count={leads.length}>
        {!leads.length ? <Empty text="Qualified leads appear here after a conversation." /> : leads.map((lead) =>
          <article className="item" key={lead.id}>
            <div className="itemtop"><strong>{lead.phone || "Unknown number"}</strong><Tier value={lead.tier} /></div>
            <p>{lead.summary || "No conversation summary recorded."}</p>
            <div className="details">{lead.products && <span>Products: {lead.products}</span>}{lead.budget && <span>Budget: {lead.budget}</span>}{lead.timeline && <span>Timeline: {lead.timeline}</span>}</div>
          </article>)}
      </Panel>
      <Panel title="Callback schedule" count={callbacks.length}>
        {!callbacks.length ? <Empty text="No callbacks scheduled." /> : callbacks.map((callback) =>
          <article className="item" key={callback.id}>
            <div className="itemtop"><strong>{callback.display}</strong><Tier value={callback.tier} /></div>
            <p>{callback.phone}{callback.note ? ` · ${callback.note}` : ""}</p>
            <small>Requested: “{callback.when_text}”</small>
          </article>)}
      </Panel>
    </section>
    <Panel title="WhatsApp activity" count={events.length}>
      {!events.length ? <Empty text="High-intent mid-call messages will appear here." /> : events.map((item) =>
        <article className="item" key={item.id}>
          <div className="itemtop"><strong>Mid-call · Hot lead</strong><small>{item.created_at}</small></div>
          <p>{item.context}</p>
        </article>)}
    </Panel>
    <footer>Multilingual voice-agent orchestration · FastAPI + React</footer>
  </main>;
}

function Stat({ label, value }) { return <div className="stat"><span>{label}</span><strong>{value}</strong></div>; }
function Panel({ title, count, children }) { return <section className="panel"><div className="panelhead"><h2>{title}</h2><span>{count}</span></div>{children}</section>; }
function Empty({ text }) { return <div className="empty">{text}</div>; }
function Tier({ value }) { const tier = (value || "unknown").toLowerCase(); return <span className={`tier ${tier}`}>{tier}</span>; }
