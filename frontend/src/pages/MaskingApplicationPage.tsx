import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { toast } from 'sonner';
import { AppShell } from '../components/AppShell';
import { getMaskedApplication } from '../lib/api/masking';
import type { MaskedApplicationDetail } from '../types';

/** Two-section screen:
 *   TOP    — read-only NCRP data (what API 1 delivered)
 *   BOTTOM — Masking Application status + FIR entry stub
 *
 *  Phase 1a shows the full read-only NCRP view. The FIR entry form
 *  (15 sections) lands in Phase 1b — a placeholder card sits there
 *  now so the layout is stable when it arrives.
 */
export function MaskingApplicationPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<MaskedApplicationDetail | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    if (!id) return;
    setBusy(true);
    getMaskedApplication(id)
      .then(setData)
      .catch((e) => toast.error(e.message))
      .finally(() => setBusy(false));
  }, [id]);

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

  const c = data.complaint;

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

        {/* ── SECTION 1: NCRP DATA (READ-ONLY) ────────────────── */}
        <section className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-bold border-b pb-2"
            style={{ color: 'var(--ksp-navy)' }}>
            NCRP Data (read-only)
          </h2>

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
            <p className="text-sm"><b>When:</b> {c.incident_occurred_at ?? '—'}</p>
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
            <Row label="Total fraud amount" value={data.total_fraud_amount} />
            <Row label="Above threshold" value={boolLabel(data.above_threshold)} />
            <Row label="Within Karnataka" value={boolLabel(data.within_karnataka_jurisdiction)} />
            <Row label="Zero FIR No." value={data.zero_fir_no} />
            <Row label="V2 FIR No." value={data.v2_fir_no} />
            <Row label="Picked up at" value={data.picked_up_at} />
          </div>

          <div className="mt-4 p-4 rounded-lg text-sm"
            style={{ background: '#fff7d6', border: '1px dashed var(--ksp-yellow)' }}>
            <b>FIR entry (15 sections)</b> — this editable form lands in
            Phase 1b. In this phase you can only review NCRP data.
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Row({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div>
      <div className="text-xs uppercase opacity-60">{label}</div>
      <div className="font-medium">{value ?? '—'}</div>
    </div>
  );
}

function boolLabel(v: boolean | null): string {
  if (v === null || v === undefined) return '—';
  return v ? 'Yes' : 'No';
}
