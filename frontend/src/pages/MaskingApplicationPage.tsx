import { Fragment, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { toast } from 'sonner';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { AppShell } from '../components/AppShell';
import { getComplaint, getOutboundEvents } from '../lib/api/masking';
import type { ComplaintDetail, OutboundEvent } from '../types';

/** Detail view — the two outbound bundles side by side + workflow
 *  status + the Sent Messages audit. Keyed on `:ackNo`. */
export function MaskingApplicationPage() {
  const { ackNo } = useParams<{ ackNo: string }>();
  const [data, setData] = useState<ComplaintDetail | null>(null);
  const [events, setEvents] = useState<OutboundEvent[]>([]);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    if (!ackNo) return;
    setBusy(true);
    Promise.all([getComplaint(ackNo), getOutboundEvents(ackNo)])
      .then(([d, evs]) => { setData(d); setEvents(evs); })
      .catch((e) => toast.error(e.message))
      .finally(() => setBusy(false));
  }, [ackNo]);

  if (busy) {
    return <AppShell><div className="text-center py-10 italic">Loading…</div></AppShell>;
  }
  if (!data) {
    return (
      <AppShell>
        <div className="text-center py-10">
          <p>Complaint not found.</p>
          <Link to="/complaints" className="underline text-sm">← Back to inbox</Link>
        </div>
      </AppShell>
    );
  }

  const c = data.ncrp_data;
  const ackPath = encodeURIComponent(data.acknowledgement_no);

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link to="/complaints" className="text-xs underline">← Back to inbox</Link>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--ksp-navy)' }}>
              Masking Application
            </h1>
            <p className="text-xs">
              NCRP Ack. <b>{c.acknowledgement_no}</b> · PS: {data.ps_name ?? '—'}
            </p>
          </div>
          <span className="px-3 py-1 rounded-full text-xs font-bold"
            style={{ background: 'var(--ksp-yellow)', color: '#000' }}>
            {data.status}
          </span>
        </div>

        {/* ── Auto-decision outcome strip ─────────────────────── */}
        <DecisionStrip data={data} />

        {/* ── SECTION 1: NCRP DATA ────────────────────────────── */}
        <section className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b pb-2">
            <h2 className="text-lg font-bold" style={{ color: 'var(--ksp-navy)' }}>
              NCRP Data
            </h2>
            <Link to={`/complaints/${ackPath}/ncrp`}
              className="px-3 py-1.5 text-xs font-bold rounded-lg"
              style={{ background: 'var(--ksp-navy)', color: 'var(--ksp-yellow)', border: '2px solid rgba(0,0,0,0.25)' }}>
              Edit NCRP Data
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <Row label="Category" value={c.category} />
            <Row label="Call started" value={c.call_start_at} />
            <Row label="Complainant name" value={c.complainant_name} />
            <Row label="Mobile" value={c.complainant_mobile} />
            <Row label="Email" value={c.complainant_email} />
            <Row label="Gender" value={c.complainant_gender} />
            <Row label="DOB" value={c.complainant_dob} />
            <Row label={`${c.complainant_relation_type ?? 'Relation'}`}
              value={c.complainant_relation_name} />
          </div>

          <div>
            <h3 className="font-semibold text-sm mt-2 mb-1">Address</h3>
            <p className="text-sm">
              {[c.address_house_no, c.address_street, c.address_colony,
                c.address_city, c.address_tehsil, c.address_district,
                c.address_state, c.address_pincode, c.address_country]
                .filter(Boolean).join(', ') || '—'}
            </p>
            <p className="text-xs mt-1 italic">
              NCRP PS name: {c.address_ps_name ?? '—'}
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-sm mt-2 mb-1">Incident</h3>
            <p className="text-sm"><b>Where:</b> {c.incident_place ?? '—'}</p>
            <p className="text-sm whitespace-pre-wrap">
              <b>Additional info:</b> {c.additional_information ?? '—'}
            </p>
          </div>

          {c.suspect_mobiles.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mt-2 mb-1">Suspect mobiles</h3>
              <p className="text-sm">{c.suspect_mobiles.join(', ')}</p>
            </div>
          )}

          {c.transactions.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mt-2 mb-1">Transactions</h3>
              <table className="w-full text-xs">
                <thead style={{ background: '#eee' }}>
                  <tr>
                    <th className="px-2 py-1 text-left">Type</th>
                    <th className="px-2 py-1 text-left">Bank / Wallet</th>
                    <th className="px-2 py-1 text-left">Account</th>
                    <th className="px-2 py-1 text-left">Txn Id</th>
                    <th className="px-2 py-1 text-left">Date</th>
                    <th className="px-2 py-1 text-right">Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {c.transactions.map((t) => (
                    <tr key={t.id} className="border-t">
                      <td className="px-2 py-1">{t.sub_category ?? '—'}</td>
                      <td className="px-2 py-1">{t.bank_wallet ?? '—'}</td>
                      <td className="px-2 py-1">{t.account_id ?? '—'}</td>
                      <td className="px-2 py-1">{t.transaction_id ?? '—'}</td>
                      <td className="px-2 py-1">{t.transaction_date ?? '—'}</td>
                      <td className="px-2 py-1 text-right">{t.amount ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {c.has_suspect_account_details && (
            <div>
              <h3 className="font-semibold text-sm mt-2 mb-1">Suspect Accounts</h3>
              {c.suspect_accounts.length === 0 ? (
                <p className="text-sm italic opacity-60">
                  Caller confirmed they have suspect account details but none captured yet.
                </p>
              ) : (
                <table className="w-full text-xs">
                  <thead style={{ background: '#eee' }}>
                    <tr>
                      <th className="px-2 py-1 text-left">Bank / Wallet</th>
                      <th className="px-2 py-1 text-left">Account / UPI</th>
                      <th className="px-2 py-1 text-left">IFSC</th>
                      <th className="px-2 py-1 text-left">Holder</th>
                      <th className="px-2 py-1 text-right">Amount (₹)</th>
                      <th className="px-2 py-1 text-left">Credited</th>
                      <th className="px-2 py-1 text-left">Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {c.suspect_accounts.map((sa) => (
                      <tr key={sa.id} className="border-t">
                        <td className="px-2 py-1">{sa.bank_wallet ?? '—'}</td>
                        <td className="px-2 py-1">{sa.account_id ?? '—'}</td>
                        <td className="px-2 py-1">{sa.ifsc_code ?? '—'}</td>
                        <td className="px-2 py-1">{sa.account_holder_name ?? '—'}</td>
                        <td className="px-2 py-1 text-right">{sa.amount_credited ?? '—'}</td>
                        <td className="px-2 py-1">{sa.credited_on ?? '—'}</td>
                        <td className="px-2 py-1">{sa.remarks ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {c.efir_answers.length > 0 && (
            <div>
              <h3 className="font-semibold text-sm mt-2 mb-1">e-FIR questionnaire</h3>
              <ul className="text-sm list-disc list-inside">
                {c.efir_answers.map((a) => (
                  <li key={a.id}>
                    {a.question_text} — <b>{a.answer ? 'Yes' : 'No'}</b>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* ── SECTION 2: MASKING APPLICATION STATUS ─────────── */}
        <section className="bg-white rounded-2xl p-6 shadow-sm space-y-3">
          <h2 className="text-lg font-bold border-b pb-2"
            style={{ color: 'var(--ksp-navy)' }}>
            Masking Application
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <Row label="Total fraud amount" value={fmtAmount(data.total_fraud_amount)} />
            <Row label="Above threshold" value={boolLabel(data.above_threshold)} />
            <Row label="Within Karnataka" value={boolLabel(data.within_karnataka_jurisdiction)} />
            <Row label="Zero FIR No." value={data.zero_fir_no} />
            <Row label="V2 FIR No." value={data.v2_fir_no} />
            <Row label="Picked up at" value={data.picked_up_at} />
          </div>

          <div className="mt-4 flex items-center justify-between p-4 rounded-lg"
            style={{ background: '#fff7d6', border: '1px dashed var(--ksp-yellow)' }}>
            <div className="text-sm">
              <b>FIR entry</b> — sections 1-6 are live now (PS details,
              summary, acts, time, place, complainant). Sections 7-15
              land in Phase 1b.2 / 1b.3.
            </div>
            <Link to={`/complaints/${ackPath}/fir-entry`}
              className="px-4 py-2 text-sm font-bold rounded-xl"
              style={{ background: 'var(--ksp-navy)', color: 'var(--ksp-yellow)', border: '2px solid rgba(0,0,0,0.25)' }}>
              Open FIR Entry →
            </Link>
          </div>
        </section>

        {/* ── SECTION 3: SENT MESSAGES (outbound audit) ──────── */}
        <SentMessages events={events} />
      </div>
    </AppShell>
  );
}

// ── Small helpers ────────────────────────────────────────────

function Row({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div>
      <div className="text-xs uppercase opacity-60">{label}</div>
      <div className="font-medium">{value ?? '—'}</div>
    </div>
  );
}

function boolLabel(v: boolean | null | undefined): string {
  if (v === null || v === undefined) return '—';
  return v ? 'Yes' : 'No';
}

function fmtAmount(v: string | null): string {
  if (v === null) return '—';
  const n = Number(v);
  if (Number.isNaN(n)) return v;
  return n.toLocaleString('en-IN', { style: 'currency', currency: 'INR' });
}

function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
}

// ── Auto-decision outcome strip ──────────────────────────────

function DecisionStrip({ data }: { data: ComplaintDetail }) {
  // Nothing to show until Submit has run (all three flags null pre-submit).
  if (data.above_threshold === null && data.within_karnataka_jurisdiction === null) {
    return (
      <section className="rounded-2xl p-4 text-sm"
        style={{ background: '#eef2f7', border: '1px dashed rgba(11,44,74,0.2)' }}>
        <b>Auto-decisions</b> — will run when the operator clicks
        Submit Complaint. Threshold + jurisdiction outcome + routing
        target will appear here.
      </section>
    );
  }

  const chip = (label: string, ok: boolean | null, yesText: string, noText: string) => {
    if (ok === null) return null;
    const bg = ok ? '#dff5e6' : '#fde3e3';
    const fg = ok ? '#0a6b28' : '#8b1919';
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-semibold"
        style={{ background: bg, color: fg }}>
        {label}: {ok ? yesText : noText}
      </span>
    );
  };

  return (
    <section className="rounded-2xl p-4 space-y-2"
      style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)', boxShadow: '0 6px 16px rgba(0,0,0,0.08)' }}>
      <div className="text-xs uppercase font-bold tracking-wide"
        style={{ color: 'var(--ksp-red)' }}>
        Auto-decisions
      </div>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span><b>Total:</b> {fmtAmount(data.total_fraud_amount)}</span>
        <span className="opacity-40">·</span>
        {chip('Threshold', data.above_threshold, 'Above', 'Below')}
        {chip('KA jurisdiction', data.within_karnataka_jurisdiction, 'Yes', 'No')}
        <span className="opacity-40">·</span>
        <span><b>Routed to:</b> {routeLabel(data.status)}</span>
      </div>
    </section>
  );
}

function routeLabel(status: string): string {
  switch (status) {
    case 'ROUTED_TO_E_LOST':            return 'e-Lost Platform';
    case 'ZERO_FIR_CREATED':            return 'Zero FIR (KA CEN PS)';
    case 'TRANSFERRED_TO_JURISDICTION_PS': return 'Jurisdictional PS (KA)';
    case 'TRANSFERRED_TO_CRIMAC':       return 'CRIMAC Portal (non-KA)';
    case 'REGISTERED_IN_V2':            return 'Registered in Police IT V2';
    case 'CLOSED_UNSIGNED':             return 'Closed — unsigned in 3 days';
    default:                            return status;
  }
}

// ── Sent Messages (outbound audit) ───────────────────────────

const TARGET_STYLE: Record<OutboundEvent['target_system'], { bg: string; fg: string }> = {
  NCRP:         { bg: '#e3ecff', fg: '#1a3a8a' },
  POLICE_IT_V2: { bg: '#fff2d6', fg: '#8a5b00' },
  CRIMAC:       { bg: '#f5e0ff', fg: '#5a1e8a' },
  E_LOST:       { bg: '#eee', fg: '#444' },
};

const STATUS_STYLE: Record<OutboundEvent['status'], { bg: string; fg: string }> = {
  placeholder: { bg: '#fff7d6', fg: '#8a5b00' },
  success:     { bg: '#dff5e6', fg: '#0a6b28' },
  failed:      { bg: '#fde3e3', fg: '#8b1919' },
};

function SentMessages({ events }: { events: OutboundEvent[] }) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <section className="bg-white rounded-2xl p-6 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b pb-2">
        <h2 className="text-lg font-bold" style={{ color: 'var(--ksp-navy)' }}>
          Sent Messages
        </h2>
        <span className="text-xs opacity-60">
          {events.length} event{events.length === 1 ? '' : 's'}
        </span>
      </div>

      {events.length === 0 ? (
        <p className="text-sm italic opacity-60 py-2">
          No integration events yet. Click Submit Complaint on the NCRP
          entry page and this timeline will fill with each push / pull.
        </p>
      ) : (
        <table className="w-full text-xs">
          <thead style={{ background: '#f5f5f7' }}>
            <tr>
              <th className="px-2 py-1.5 text-left w-8"></th>
              <th className="px-2 py-1.5 text-left">When</th>
              <th className="px-2 py-1.5 text-left">Target</th>
              <th className="px-2 py-1.5 text-left">Event</th>
              <th className="px-2 py-1.5 text-left">Dir</th>
              <th className="px-2 py-1.5 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => {
              const isOpen = expandedId === ev.id;
              const tgt = TARGET_STYLE[ev.target_system] ?? TARGET_STYLE.E_LOST;
              const st = STATUS_STYLE[ev.status] ?? STATUS_STYLE.placeholder;
              return (
                <Fragment key={ev.id}>
                  <tr className="border-t hover:bg-slate-50 cursor-pointer"
                    onClick={() => setExpandedId(isOpen ? null : ev.id)}>
                    <td className="px-2 py-2">
                      {isOpen ? <ChevronDown className="w-3.5 h-3.5" />
                              : <ChevronRight className="w-3.5 h-3.5" />}
                    </td>
                    <td className="px-2 py-2 whitespace-nowrap">{fmtDateTime(ev.created_at)}</td>
                    <td className="px-2 py-2">
                      <span className="px-2 py-0.5 rounded-full font-semibold"
                        style={{ background: tgt.bg, color: tgt.fg }}>
                        {ev.target_system}
                      </span>
                    </td>
                    <td className="px-2 py-2 font-mono">{ev.event_type}</td>
                    <td className="px-2 py-2 uppercase opacity-70">{ev.direction}</td>
                    <td className="px-2 py-2">
                      <span className="px-2 py-0.5 rounded-full font-semibold"
                        style={{ background: st.bg, color: st.fg }}>
                        {ev.status}
                      </span>
                    </td>
                  </tr>
                  {isOpen && (
                    <tr style={{ background: '#fafbfd' }}>
                      <td></td>
                      <td colSpan={5} className="px-3 py-3 space-y-3">
                        {ev.notes && (
                          <div>
                            <div className="text-xs font-bold opacity-60 mb-0.5">Notes</div>
                            <div className="text-sm">{ev.notes}</div>
                          </div>
                        )}
                        {ev.payload && (
                          <div>
                            <div className="text-xs font-bold opacity-60 mb-0.5">
                              Payload (what we {ev.direction === 'outbound' ? 'would send' : 'would request'})
                            </div>
                            <pre className="text-xs p-2 rounded overflow-x-auto"
                              style={{ background: '#0b2c4a', color: '#c8dcf5' }}>
                              {JSON.stringify(ev.payload, null, 2)}
                            </pre>
                          </div>
                        )}
                        {ev.response && (
                          <div>
                            <div className="text-xs font-bold opacity-60 mb-0.5">Response</div>
                            <pre className="text-xs p-2 rounded overflow-x-auto"
                              style={{ background: '#0a3316', color: '#c8f5d5' }}>
                              {JSON.stringify(ev.response, null, 2)}
                            </pre>
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
