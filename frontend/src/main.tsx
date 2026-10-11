import { StrictMode, useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ArrowRight, CheckCircle2, CircleDollarSign, Clock3, ExternalLink, HeartHandshake, Play, ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import './styles.css'
import './viewport.css'

const API = 'http://localhost:8000/api'
type Ticket = { id:number; type:string; requester:string; subject:string; status:string; created_at:string }
type AgentSummary = { agent:string; said:string[]; tools_used:string[] }
type Events = { events: Record<string,unknown>[]; by_agent: AgentSummary[] }
type Report = { ticket_id:number; status:string; facts:string[]; findings:{agent:string; summary:string; facts:string[]; recommended_next_step:string}[]; customer_safe_response:string; human_approval_required:boolean }

const pretty = (name:string) => name.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())
const agentColors:Record<string,string> = { boss:'lavender', inventory:'mint', accounting:'lemon', facilities:'sky', customer_service:'peach' }

function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selected, setSelected] = useState(101)
  const [events, setEvents] = useState<Events>({events:[], by_agent:[]})
  const [report, setReport] = useState<Report|null>(null)
  const [balance, setBalance] = useState<number|null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [approval, setApproval] = useState({kind:'purchase', ref_id:'', amount:'', account:'checking', approved_by:''})
  const load = useCallback(async () => {
    try {
      const [ticketRes, eventRes, cashRes] = await Promise.all([fetch(`${API}/tickets`), fetch(`${API}/events?limit=80`), fetch(`${API}/cash`)]);
      if (!ticketRes.ok || !eventRes.ok || !cashRes.ok) throw new Error('The desk API did not respond.')
      setTickets(await ticketRes.json()); setEvents(await eventRes.json()); setBalance((await cashRes.json()).balance)
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not reach the backend.') }
  }, [])
  useEffect(() => { load() }, [load])
  useEffect(() => { if (!running) return; const id = window.setInterval(load, 1800); return () => window.clearInterval(id) }, [running, load])
  const ticket = tickets.find(item => item.id === selected)
  const selectedAgents = useMemo(() => events.by_agent.filter(agent => agent.agent !== 'unknown'), [events])
  const run = async () => {
    setRunning(true); setReport(null); setError('')
    try {
      const res = await fetch(`${API}/tickets/${selected}/run`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({objective:'Review this ticket using the planned workflow and prepare a safe recommendation.'})})
      if (!res.ok) throw new Error(await res.text())
      setReport(await res.json()); await load()
    } catch (e) { setError(e instanceof Error ? e.message : 'The team run failed.') } finally { setRunning(false); await load() }
  }
  const approve = async (event:FormEvent) => {
    event.preventDefault(); setError('')
    try { const res = await fetch(`${API}/approve`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...approval, ref_id:approval.ref_id ? Number(approval.ref_id) : null, amount:Number(approval.amount)})}); if (!res.ok) throw new Error(await res.text()); setApproval({...approval, amount:'', ref_id:''}); await load() }
    catch (e) { setError(e instanceof Error ? e.message : 'Approval failed.') }
  }
  return <div className="shell">
    <header className="topbar"><div className="brand"><span className="brand-mark"><Sparkles size={17}/></span><span>Campus <b>Customs</b></span></div><div className="live"><span className="live-dot"/> Desk online <span className="divider"/> <span className="muted">Today · 31 Aug 2026</span></div></header>
    <main>
      <section className="hero"><div><p className="kicker">Operations, with a human in the loop</p><h1>Good decisions<br/><em>feel coordinated.</em></h1><p className="subhead">A calm little command center for the Campus Customs team.</p></div><div className="hero-note"><HeartHandshake size={20}/><span>Agents prepare.<br/><b>People approve.</b></span></div></section>
      {error && <div className="error"><Activity size={17}/>{error}</div>}
      <section className="metrics"><div className="metric"><span className="metric-icon mint-bg"><CircleDollarSign size={19}/></span><div><span>Checking balance</span><strong>{balance === null ? '—' : `$${balance.toLocaleString('en-US',{minimumFractionDigits:2})}`}</strong></div></div><div className="metric"><span className="metric-icon lavender-bg"><Clock3 size={19}/></span><div><span>Open tickets</span><strong>{tickets.filter(t=>t.status==='open').length}<small> / {tickets.length || 3} total</small></strong></div></div><div className="metric"><span className="metric-icon peach-bg"><ShieldCheck size={19}/></span><div><span>Human approval</span><strong>Always on</strong></div></div></section>
      <div className="workspace"><aside className="ticket-list"><div className="section-head"><div><p className="kicker">The desk</p><h2>Tickets</h2></div><span className="count-pill">{tickets.length || 3}</span></div>{tickets.map(item => <button className={`ticket-card ${selected===item.id?'selected':''}`} key={item.id} onClick={()=>{setSelected(item.id);setReport(null)}}><div className="ticket-line"><span className={`ticket-number ${item.id===101?'pink':item.id===102?'blue':'yellow'}`}>{item.id}</span><span className={`status ${item.status}`}>{item.status==='resolved'?<CheckCircle2 size={13}/>:<span className="status-dot"/>}{item.status}</span></div><strong>{item.subject}</strong><span>{item.requester}</span><ArrowRight className="arrow" size={16}/></button>)}</aside>
        <section className="detail"><div className="detail-head"><div><p className="kicker">Selected ticket</p><h2>{ticket?.subject || 'Choose a ticket'}</h2><p className="detail-meta">#{selected} · {ticket?.requester || '—'} · {ticket?.type?.replace('_',' ') || '—'}</p></div><button className="run-button" onClick={run} disabled={running || !ticket}>{running ? <><span className="spinner"/> Team is thinking</> : <><Play size={16} fill="currentColor"/> Run agent team</>}</button></div>
          <div className="run-state">{running ? <><span className="pulse"/> Live run · refreshing every 1.8 seconds</> : report ? <><CheckCircle2 size={15}/> Run finished · ticket marked resolved</> : <><Clock3 size={15}/> Ready when you are</>}</div>
          <div className="agent-grid">{['boss','inventory','accounting','facilities','customer_service'].map(name => { const item=selectedAgents.find(a=>a.agent===name); return <article className={`agent-card ${agentColors[name]}`} key={name}><div className="agent-top"><span className="avatar"><UserRound size={17}/></span><div><strong>{pretty(name)}</strong><span>{item ? 'Active in this run' : 'Waiting for a task'}</span></div><span className="agent-check">{item?<CheckCircle2 size={17}/>:<span className="hollow"/>}</span></div><p>{item?.said[item.said.length - 1] || 'Their notes will appear here as the team works.'}</p>{item?.tools_used.length ? <div className="tool-list">{item.tools_used.map(tool=><span key={tool}>{tool}</span>)}</div> : null}</article> })}</div>
          {report && <div className="summary"><div className="summary-title"><Sparkles size={18}/><div><p className="kicker">Team summary</p><h3>What happened on ticket #{report.ticket_id}</h3></div></div><div className="finding-grid">{report.findings.map(f=><div className="finding" key={f.agent}><b>{pretty(f.agent)}</b><p>{f.summary}</p><span>{f.recommended_next_step}</span></div>)}</div><div className="safe-response"><b>Customer-safe draft</b><p>{report.customer_safe_response}</p></div></div>}
          <div className="approval"><div><p className="kicker">Human approval</p><h3>Make a payment or purchase</h3><p>Agents can prepare the decision. Only a person can move cash.</p></div><form onSubmit={approve}><div className="form-row"><label>Kind<select value={approval.kind} onChange={e=>setApproval({...approval,kind:e.target.value})}><option value="purchase">Purchase</option><option value="rent">Rent payment</option><option value="invoice">Invoice payment</option></select></label><label>Amount<input required type="number" min="0.01" step="0.01" value={approval.amount} onChange={e=>setApproval({...approval,amount:e.target.value})} placeholder="0.00"/></label></div><div className="form-row"><label>Reference ID<input type="number" value={approval.ref_id} onChange={e=>setApproval({...approval,ref_id:e.target.value})} placeholder="Optional"/></label><label>Approved by<input required value={approval.approved_by} onChange={e=>setApproval({...approval,approved_by:e.target.value})} placeholder="Your name"/></label></div><button className="approve-button" type="submit"><ShieldCheck size={16}/> Approve & record</button></form></div>
        </section></div>
      <footer><span><Sparkles size={14}/> Grounded in Campus Customs records</span><a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API docs <ExternalLink size={13}/></a></footer>
    </main>
  </div>
}
createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
