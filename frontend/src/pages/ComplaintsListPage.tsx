import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { toast } from 'sonner';
import { Plus } from 'lucide-react';
import { AppShell } from '../components/AppShell';
import { listComplaints } from '../lib/api/masking';
import type { ComplaintListItem } from '../types';

const STATUSES = [
  '', 'RECEIVED', 'IN_PROGRESS', 'SUBMITTED',
  'ROUTED_TO_E_LOST', 'ZERO_FIR_CREATED',
  'TRANSFERRED_TO_JURISDICTION_PS', 'TRANSFERRED_TO_CRIMAC',
  'REGISTERED_IN_V2', 'CLOSED_UNSIGNED', 'CANCELLED',
];

function fmtAmount(v: string | null): string {
  if (v === null) return '—';
  const n = Number(v);
  if (Number.isNaN(n)) return v;
  return n.toLocaleString('en-IN', { style: 'currency', currency: 'INR' });
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
}

export function ComplaintsListPage() {
  const [rows, setRows] = useState<ComplaintListItem[]>([]);
  const [status, setStatus] = useState<string>('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setBusy(true);
    listComplaints(status || undefined)
      .then(setRows)
      .catch((e) => toast.error(e.message))
      .finally(() => setBusy(false));
  }, [status]);

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <h1 className="text-2xl font-bold" style={{ color: 'var(--ksp-navy)' }}>
            Complaints Inbox
          </h1>
          <div className="flex items-center gap-3">
            <Link to="/complaints/new"
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-bold rounded-xl transition"
              style={{ background: 'var(--ksp-navy)', color: 'var(--ksp-yellow)', border: '2px solid rgba(0,0,0,0.25)' }}>
              <Plus className="w-4 h-4" /> New Complaint
            </Link>
            <label className="text-sm flex items-center gap-2">
              <span>Filter status:</span>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="px-3 py-1 rounded-lg text-sm bg-white"
                style={{ border: '2px solid var(--ksp-navy)' }}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s || 'All'}</option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead style={{ background: 'var(--ksp-navy)', color: '#fff' }}>
              <tr>
                <th className="px-3 py-2 text-left">Ack. No.</th>
                <th className="px-3 py-2 text-left">Complainant</th>
                <th className="px-3 py-2 text-left">Mobile</th>
                <th className="px-3 py-2 text-left">Category</th>
                <th className="px-3 py-2 text-right">Amount</th>
                <th className="px-3 py-2 text-left">PS</th>
                <th className="px-3 py-2 text-left">Status</th>
                <th className="px-3 py-2 text-left">Received</th>
              </tr>
            </thead>
            <tbody>
              {busy && (
                <tr><td colSpan={8} className="px-3 py-6 text-center italic">Loading…</td></tr>
              )}
              {!busy && rows.length === 0 && (
                <tr><td colSpan={8} className="px-3 py-6 text-center italic">No complaints yet.</td></tr>
              )}
              {!busy && rows.map((r) => (
                <tr key={r.acknowledgement_no} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2">
                    <Link to={`/complaints/${encodeURIComponent(r.acknowledgement_no)}`}
                      className="font-semibold underline"
                      style={{ color: 'var(--ksp-navy)' }}>
                      {r.acknowledgement_no}
                    </Link>
                  </td>
                  <td className="px-3 py-2">{r.complainant_name}</td>
                  <td className="px-3 py-2">{r.complainant_mobile}</td>
                  <td className="px-3 py-2">{r.category ?? '—'}</td>
                  <td className="px-3 py-2 text-right">{fmtAmount(r.total_fraud_amount)}</td>
                  <td className="px-3 py-2">{r.ps_name ?? '—'}</td>
                  <td className="px-3 py-2">
                    <span className="px-2 py-0.5 rounded-full text-xs font-semibold"
                      style={{ background: 'var(--ksp-yellow)', color: '#000' }}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">{fmtDate(r.received_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}
