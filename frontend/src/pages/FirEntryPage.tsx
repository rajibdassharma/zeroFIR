/** FIR Entry — V2 sections 1-6 (Phase 1b.1).
 *
 *  Layout mirrors CyberFraud's CaseEntryPage: numbered pill tabs at
 *  top, one section per tab in white cards, Prev/Save-Draft/Next
 *  buttons at bottom. Save-draft PATCHes only the delta of fields the
 *  user has touched via the backend's `exclude_unset` handling.
 *
 *  Sections 7-11+14 (accused/victims/property/action/signature/other)
 *  land in Phase 1b.2 and 1b.3.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { toast } from 'sonner';
import { ChevronLeft, ChevronRight, Save } from 'lucide-react';
import { AppShell } from '../components/AppShell';
import {
  AddBtn, BoolRadio, NumField, RemBtn, Section, SelectField,
  TextAreaField, TextField,
} from '../components/form';
import { getComplaint, getFirMasterDropdowns, saveV2Draft } from '../lib/api/masking';
import { listPoliceStations } from '../lib/api/master';
import type {
  ComplaintDetail, FirAct, FirEntry, FirMasterDropdowns, PoliceStation,
} from '../types';

const TABS = [
  'PS Details',
  'FIR Summary',
  'Acts & Sections',
  'Time of Occurrence',
  'Place of Incident',
  'Complainant',
];

/** Empty FIR entry — every field null-ish. The form treats null-ish
 *  as "unset" and never sends unset keys on save-draft. */
function emptyEntry(): FirEntry {
  return {
    ps_details_district: null,
    ps_details_sub_division: null,
    ps_details_ps_name: null,
    ps_details_entry_date: null,
    ps_details_last_fir_no: null,
    ps_details_last_fir_time: null,
    ps_details_gsc_no: null,
    zero_fir_no: null,

    fir_summary: null,

    crime_classification_major: null,
    crime_classification_minor: null,
    offences_involve_aadhaar: null,
    acts: [],

    incident_from_at: null,
    incident_to_at: null,
    info_received_at_ps_at: null,
    mode_of_complaint: null,
    fir_case_type: null,
    shd_reference: null,
    reasons_for_delay: null,
    complainant_saw_occurrence: null,

    poi_house_no: null,
    poi_street: null,
    poi_colony: null,
    poi_beat_name: null,
    poi_village: null,
    poi_city: null,
    poi_tehsil: null,
    poi_district: null,
    poi_state: null,
    poi_country: 'India',
    poi_police_station: null,
    poi_pincode: null,
    poi_distance_from_ps: null,
    poi_direction_from_ps: null,
    poi_mla_constituency: null,
    poi_mp_constituency: null,
    poi_is_forest: null,
    poi_is_sea: null,
    poi_location_nature: null,
    poi_latitude: null,
    poi_longitude: null,
    poi_other_juris_state: null,
    poi_other_juris_district: null,
    poi_other_juris_ps: null,

    comp_relation_to_victim: null,
    comp_role: null,
    comp_first_name: null,
    comp_middle_name: null,
    comp_last_name: null,
    comp_dob: null,
    comp_age: null,
    comp_gender: null,
    comp_nationality: null,
    comp_occupation: null,
    comp_religion: null,
    comp_caste: null,
    comp_father_name: null,
    comp_mother_name: null,
    comp_uid_type: null,
    comp_uid_number: null,
    comp_aadhaar_ref_no: null,
    comp_email: null,
    comp_mobile: null,
    comp_alt_mobile: null,
    comp_address_house_no: null,
    comp_address_street: null,
    comp_address_city: null,
    comp_address_state: null,
    comp_address_pincode: null,
    comp_address_country: 'India',
  };
}

const emptyAct = (): FirAct => ({
  act_code: null, act_name: null, sections: null,
  offence_type: null, gravity: null,
});

/** Turn a nullable string field into ('' → null) so blanks don't
 *  land as empty strings in the DB (which would defeat NULL checks
 *  later). */
const nz = (s: string): string | null => (s.trim() === '' ? null : s);

/** Convert a "YYYY-MM-DDTHH:mm" datetime-local string ↔ ISO for API. */
const fromLocalDT = (s: string): string | null =>
  s === '' ? null : `${s}:00`;
const toLocalDT = (iso: string | null): string =>
  iso === null ? '' : iso.slice(0, 16);

export function FirEntryPage() {
  const { ackNo } = useParams<{ ackNo: string }>();
  const navigate = useNavigate();

  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [detail, setDetail] = useState<ComplaintDetail | null>(null);
  const [f, setF] = useState<FirEntry>(emptyEntry());
  const [master, setMaster] = useState<FirMasterDropdowns | null>(null);
  const [pses, setPSes] = useState<PoliceStation[]>([]);

  useEffect(() => {
    if (!ackNo) return;
    setLoading(true);
    Promise.all([getComplaint(ackNo), getFirMasterDropdowns(), listPoliceStations()])
      .then(([d, m, ps]) => {
        setDetail(d);
        setMaster(m);
        setPSes(ps);
        setF({ ...emptyEntry(), ...d.police_it_v2 });
      })
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  }, [ackNo]);

  const setField = <K extends keyof FirEntry>(k: K, v: FirEntry[K]) =>
    setF((prev) => ({ ...prev, [k]: v }));

  const handleSaveDraft = async () => {
    if (!ackNo) return;
    setSaving(true);
    try {
      const updated = await saveV2Draft(ackNo, f);
      setDetail(updated);
      setF({ ...emptyEntry(), ...updated.police_it_v2 });
      toast.success('Draft saved');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!ackNo) return;
    // TODO Phase 1b.3: this calls a dedicated /submit route that runs
    // the threshold + jurisdiction auto-decisions, transitions status
    // to ZERO_FIR_CREATED / ROUTED_TO_E_LOST etc., and fires API 2.
    // Today it just persists the entry (same PATCH as Save Draft) and
    // returns to the complaint detail.
    setSaving(true);
    try {
      await saveV2Draft(ackNo, f);
      toast.success('FIR entry submitted (auto-decisions land in Phase 1b.3)');
      navigate(`/complaints/${encodeURIComponent(ackNo)}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Submit failed');
    } finally {
      setSaving(false);
    }
  };

  // Options for SelectFields (compact, memoized so re-renders don't
  // rebuild the arrays).
  const opts = useMemo(() => {
    if (!master) {
      return {
        acts: [], mode: [], case_type: [], offence: [], gravity: [],
        direction: [], uid: [], relation: [], role: [], states: [],
        major_head: [], minor_head: [], religion: [], caste: [], ps: [],
      };
    }
    const dashOpt = { value: '', label: '— Select —' };
    return {
      acts: [dashOpt, ...master.acts.map((a) => ({ value: a.code, label: a.name }))],
      mode: [dashOpt, ...master.mode_of_complaint.map((s) => ({ value: s, label: s }))],
      case_type: [dashOpt, ...master.fir_case_type.map((s) => ({ value: s, label: s }))],
      offence: [dashOpt, ...master.offence_type.map((s) => ({ value: s, label: s }))],
      gravity: [dashOpt, ...master.gravity.map((s) => ({ value: s, label: s }))],
      direction: [dashOpt, ...master.direction.map((s) => ({ value: s, label: s }))],
      uid: [dashOpt, ...master.uid_type.map((s) => ({ value: s, label: s }))],
      relation: [dashOpt, ...master.relation_to_victim.map((s) => ({ value: s, label: s }))],
      role: [dashOpt, ...master.complainant_role.map((s) => ({
        value: s, label: s.replace(/_/g, ' '),
      }))],
      states: [dashOpt, ...master.indian_states.map((s) => ({ value: s, label: s }))],
      major_head: [dashOpt, ...master.crime_major_head.map((s) => ({ value: s, label: s }))],
      minor_head: [dashOpt, ...master.crime_minor_head.map((s) => ({ value: s, label: s }))],
      religion: [dashOpt, ...master.religion.map((s) => ({ value: s, label: s }))],
      caste: [dashOpt, ...master.caste.map((s) => ({ value: s, label: s }))],
      ps: [dashOpt, ...pses.map((p) => ({ value: p.name, label: p.name }))],
    };
  }, [master, pses]);

  if (loading || !detail) {
    return <AppShell><div className="text-center py-10 italic">Loading…</div></AppShell>;
  }

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        {/* Context strip — NCRP ack + status */}
        <div className="rounded-2xl p-4 mb-4" style={{ background: 'var(--ksp-navy)', color: '#fff' }}>
          <div className="flex flex-wrap items-baseline gap-3 justify-between">
            <div>
              <Link to={`/complaints/${encodeURIComponent(detail.acknowledgement_no)}`}
                className="text-xs underline opacity-80">← Back to Masking Application</Link>
              <h1 className="text-lg font-bold" style={{ color: 'var(--ksp-yellow)' }}>
                FIR Entry
              </h1>
              <p className="text-xs mt-1">
                Ack. <b>{detail.ncrp_data.acknowledgement_no}</b> ·
                Complainant: {detail.ncrp_data.complainant_name} ·
                PS: {detail.ps_name ?? '—'}
              </p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold"
              style={{ background: 'var(--ksp-yellow)', color: '#000' }}>
              {detail.status}
            </span>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex flex-wrap gap-2 mb-4">
          {TABS.map((label, i) => (
            <button key={label} type="button" onClick={() => setTab(i)}
              className="px-4 py-2 text-sm font-semibold rounded-xl transition"
              style={{
                background: tab === i ? 'var(--ksp-navy)' : 'var(--ksp-yellow)',
                color: tab === i ? 'var(--ksp-yellow)' : '#000',
                border: '2px solid rgba(0,0,0,0.2)',
              }}>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold"
                  style={{
                    background: tab === i ? 'var(--ksp-yellow)' : 'var(--ksp-navy)',
                    color: tab === i ? 'var(--ksp-navy)' : 'var(--ksp-yellow)',
                  }}>
                  {i + 1}
                </span>
                {label}
              </span>
            </button>
          ))}
        </div>

        <div className="space-y-5">
          {/* ═════ TAB 1 — PS Details ═════ */}
          {tab === 0 && (
            <Section title="Police Station Details">
              <TextField label="District" value={f.ps_details_district ?? ''}
                onChange={(v) => setField('ps_details_district', nz(v))} />
              <TextField label="Sub-Division" value={f.ps_details_sub_division ?? ''}
                onChange={(v) => setField('ps_details_sub_division', nz(v))} />
              <TextField label="Police Station" value={f.ps_details_ps_name ?? ''}
                onChange={(v) => setField('ps_details_ps_name', nz(v))} />
              <TextField label="Entry Date" type="date" value={f.ps_details_entry_date ?? ''}
                onChange={(v) => setField('ps_details_entry_date', nz(v))} />
              <TextField label="Last FIR No" value={f.ps_details_last_fir_no ?? ''}
                onChange={(v) => setField('ps_details_last_fir_no', nz(v))}
                placeholder="e.g. 199/2026" />
              <TextField label="Last FIR Date-Time" type="datetime-local"
                value={toLocalDT(f.ps_details_last_fir_time)}
                onChange={(v) => setField('ps_details_last_fir_time', fromLocalDT(v))} />
              <TextField label="Zero FIR No" value={f.zero_fir_no ?? ''}
                onChange={(v) => setField('zero_fir_no', nz(v))}
                placeholder="e.g. 0/2026" />
              <TextField label="GSC No" value={f.ps_details_gsc_no ?? ''}
                onChange={(v) => setField('ps_details_gsc_no', nz(v))} />
            </Section>
          )}

          {/* ═════ TAB 2 — FIR Summary ═════ */}
          {tab === 1 && (
            <Section title="FIR Summary (English / Kannada)">
              <TextAreaField label="Summary (≥ 300 chars)"
                value={f.fir_summary ?? ''}
                onChange={(v) => setField('fir_summary', nz(v))}
                rows={12} maxLength={20000} />
            </Section>
          )}

          {/* ═════ TAB 3 — Acts & Sections ═════ */}
          {tab === 2 && (
            <div className="space-y-5">
              <Section title="Crime Classification">
                <SelectField label="Major Head" value={f.crime_classification_major ?? ''}
                  onChange={(v) => setField('crime_classification_major', nz(v))}
                  options={opts.major_head} />
                <SelectField label="Minor Head" value={f.crime_classification_minor ?? ''}
                  onChange={(v) => setField('crime_classification_minor', nz(v))}
                  options={opts.minor_head} />

                <BoolRadio label="Involves Aadhaar?" value={f.offences_involve_aadhaar}
                  onChange={(v) => setField('offences_involve_aadhaar', v)} />
              </Section>

              {f.acts.map((a, i) => (
                <div key={i} className="rounded-2xl p-5 space-y-3"
                  style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)',
                           boxShadow: '0 6px 16px rgba(0,0,0,0.08)' }}>
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold uppercase tracking-wide"
                      style={{ color: 'var(--ksp-red)' }}>Act #{i + 1}</h3>
                    <RemBtn onClick={() => setField('acts', f.acts.filter((_, j) => j !== i))} />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <SelectField label="Act" value={a.act_code ?? ''}
                      onChange={(v) => {
                        const acts = [...f.acts];
                        const label = master?.acts.find((m) => m.code === v)?.name ?? null;
                        acts[i] = { ...acts[i], act_code: nz(v), act_name: label };
                        setField('acts', acts);
                      }}
                      options={opts.acts} />
                    <TextField label="Sections (comma-separated)" value={a.sections ?? ''}
                      onChange={(v) => {
                        const acts = [...f.acts];
                        acts[i] = { ...acts[i], sections: nz(v) };
                        setField('acts', acts);
                      }}
                      placeholder="e.g. 318(4), 319, 340" />
                    <SelectField label="Offence Type" value={a.offence_type ?? ''}
                      onChange={(v) => {
                        const acts = [...f.acts];
                        acts[i] = { ...acts[i], offence_type: nz(v) };
                        setField('acts', acts);
                      }}
                      options={opts.offence} />
                    <SelectField label="Gravity" value={a.gravity ?? ''}
                      onChange={(v) => {
                        const acts = [...f.acts];
                        acts[i] = { ...acts[i], gravity: nz(v) };
                        setField('acts', acts);
                      }}
                      options={opts.gravity} />
                  </div>
                </div>
              ))}
              <AddBtn label="Add Act" onClick={() => setField('acts', [...f.acts, emptyAct()])} />
            </div>
          )}

          {/* ═════ TAB 4 — Time of Occurrence ═════ */}
          {tab === 3 && (
            <Section title="Time of Occurrence">
              <TextField label="Incident From (date-time)" type="datetime-local"
                value={toLocalDT(f.incident_from_at)}
                onChange={(v) => setField('incident_from_at', fromLocalDT(v))} />
              <TextField label="Incident To (date-time)" type="datetime-local"
                value={toLocalDT(f.incident_to_at)}
                onChange={(v) => setField('incident_to_at', fromLocalDT(v))} />
              <TextField label="Info Received at PS (date-time)" type="datetime-local"
                value={toLocalDT(f.info_received_at_ps_at)}
                onChange={(v) => setField('info_received_at_ps_at', fromLocalDT(v))} />
              <SelectField label="Mode of Complaint" value={f.mode_of_complaint ?? ''}
                onChange={(v) => setField('mode_of_complaint', nz(v))}
                options={opts.mode} />
              <SelectField label="FIR Case Type" value={f.fir_case_type ?? ''}
                onChange={(v) => setField('fir_case_type', nz(v))}
                options={opts.case_type} />
              <TextField label="SHD Reference" value={f.shd_reference ?? ''}
                onChange={(v) => setField('shd_reference', nz(v))} />
              <BoolRadio label="Complainant saw occurrence?"
                value={f.complainant_saw_occurrence}
                onChange={(v) => setField('complainant_saw_occurrence', v)} />
              <TextAreaField label="Reasons for Delay (if any)"
                value={f.reasons_for_delay ?? ''}
                onChange={(v) => setField('reasons_for_delay', nz(v))}
                rows={3} />
            </Section>
          )}

          {/* ═════ TAB 5 — Place of Incident ═════ */}
          {tab === 4 && (
            <div className="space-y-5">
              <Section title="Address">
                <TextField label="House No" value={f.poi_house_no ?? ''}
                  onChange={(v) => setField('poi_house_no', nz(v))} />
                <TextField label="Street" value={f.poi_street ?? ''}
                  onChange={(v) => setField('poi_street', nz(v))} />
                <TextField label="Colony / Locality / Area" value={f.poi_colony ?? ''}
                  onChange={(v) => setField('poi_colony', nz(v))} />
                <TextField label="Beat Name" value={f.poi_beat_name ?? ''}
                  onChange={(v) => setField('poi_beat_name', nz(v))} />
                <TextField label="Village" value={f.poi_village ?? ''}
                  onChange={(v) => setField('poi_village', nz(v))} />
                <TextField label="City" value={f.poi_city ?? ''}
                  onChange={(v) => setField('poi_city', nz(v))} />
                <TextField label="Tehsil / Block / Mandal" value={f.poi_tehsil ?? ''}
                  onChange={(v) => setField('poi_tehsil', nz(v))} />
                <TextField label="District" value={f.poi_district ?? ''}
                  onChange={(v) => setField('poi_district', nz(v))} />
                <SelectField label="State" value={f.poi_state ?? ''}
                  onChange={(v) => setField('poi_state', nz(v))}
                  options={opts.states} />
                <TextField label="Country" value={f.poi_country ?? ''}
                  onChange={(v) => setField('poi_country', nz(v))} />
                <SelectField label="Police Station (of incident)"
                  value={f.poi_police_station ?? ''}
                  onChange={(v) => setField('poi_police_station', nz(v))}
                  options={opts.ps} />
                <TextField label="Pincode" value={f.poi_pincode ?? ''}
                  onChange={(v) => setField('poi_pincode', nz(v.replace(/\D/g, '')))}
                  maxLength={6} inputMode="numeric" />
              </Section>

              <Section title="Location Context">
                <TextField label="Distance from PS" value={f.poi_distance_from_ps ?? ''}
                  onChange={(v) => setField('poi_distance_from_ps', nz(v))}
                  placeholder="e.g. 12 km" />
                <SelectField label="Direction from PS" value={f.poi_direction_from_ps ?? ''}
                  onChange={(v) => setField('poi_direction_from_ps', nz(v))}
                  options={opts.direction} />
                <TextField label="MLA Constituency" value={f.poi_mla_constituency ?? ''}
                  onChange={(v) => setField('poi_mla_constituency', nz(v))} />
                <TextField label="MP Constituency" value={f.poi_mp_constituency ?? ''}
                  onChange={(v) => setField('poi_mp_constituency', nz(v))} />
                <BoolRadio label="Forest Area?" value={f.poi_is_forest}
                  onChange={(v) => setField('poi_is_forest', v)} />
                <BoolRadio label="Sea?" value={f.poi_is_sea}
                  onChange={(v) => setField('poi_is_sea', v)} />
                <SelectField label="Nature of Location" value={f.poi_location_nature ?? ''}
                  onChange={(v) => setField('poi_location_nature', nz(v))}
                  options={[
                    { value: '', label: '— Select —' },
                    { value: 'actual', label: 'Actual' },
                    { value: 'temporary', label: 'Temporary' },
                  ]} />
                <TextField label="Latitude" value={f.poi_latitude ?? ''}
                  onChange={(v) => setField('poi_latitude', nz(v))}
                  placeholder="12.9716" />
                <TextField label="Longitude" value={f.poi_longitude ?? ''}
                  onChange={(v) => setField('poi_longitude', nz(v))}
                  placeholder="77.5946" />
              </Section>

              <Section title="Other Jurisdiction (if applicable)">
                <TextField label="State" value={f.poi_other_juris_state ?? ''}
                  onChange={(v) => setField('poi_other_juris_state', nz(v))} />
                <TextField label="District" value={f.poi_other_juris_district ?? ''}
                  onChange={(v) => setField('poi_other_juris_district', nz(v))} />
                <TextField label="Police Station" value={f.poi_other_juris_ps ?? ''}
                  onChange={(v) => setField('poi_other_juris_ps', nz(v))} />
              </Section>
            </div>
          )}

          {/* ═════ TAB 6 — Complainant / Informant ═════ */}
          {tab === 5 && (
            <div className="space-y-5">
              <Section title="Role & Relation">
                <SelectField label="Relation to Victim" value={f.comp_relation_to_victim ?? ''}
                  onChange={(v) => setField('comp_relation_to_victim', nz(v))}
                  options={opts.relation} />
                <SelectField label="Role" value={f.comp_role ?? ''}
                  onChange={(v) => setField('comp_role', nz(v))}
                  options={opts.role} />
              </Section>

              <Section title="Identity" cols={6}>
                <TextField label="First Name" wrapperClassName="lg:col-span-2"
                  value={f.comp_first_name ?? ''}
                  onChange={(v) => setField('comp_first_name', nz(v))} />
                <TextField label="Middle Name" wrapperClassName="lg:col-span-2"
                  value={f.comp_middle_name ?? ''}
                  onChange={(v) => setField('comp_middle_name', nz(v))} />
                <TextField label="Last Name" wrapperClassName="lg:col-span-2"
                  value={f.comp_last_name ?? ''}
                  onChange={(v) => setField('comp_last_name', nz(v))} />

                <TextField label="DOB" type="date" wrapperClassName="lg:col-span-2"
                  value={f.comp_dob ?? ''}
                  onChange={(v) => setField('comp_dob', nz(v))} />
                <NumField label="Age" wrapperClassName="lg:col-span-1"
                  value={f.comp_age} onChange={(v) => setField('comp_age', v)} />
                <SelectField label="Gender" wrapperClassName="lg:col-span-1"
                  value={f.comp_gender ?? ''}
                  onChange={(v) => setField('comp_gender', nz(v))}
                  options={[
                    { value: '', label: '—' },
                    { value: 'Male', label: 'Male' },
                    { value: 'Female', label: 'Female' },
                    { value: 'Other', label: 'Other' },
                  ]} />
                <TextField label="Nationality" wrapperClassName="lg:col-span-2"
                  value={f.comp_nationality ?? ''}
                  onChange={(v) => setField('comp_nationality', nz(v))}
                  placeholder="Indian" />
                <TextField label="Occupation" wrapperClassName="lg:col-span-4"
                  value={f.comp_occupation ?? ''}
                  onChange={(v) => setField('comp_occupation', nz(v))} />
                <SelectField label="Religion" wrapperClassName="lg:col-span-3"
                  value={f.comp_religion ?? ''}
                  onChange={(v) => setField('comp_religion', nz(v))}
                  options={opts.religion} />
                <SelectField label="Caste" wrapperClassName="lg:col-span-3"
                  value={f.comp_caste ?? ''}
                  onChange={(v) => setField('comp_caste', nz(v))}
                  options={opts.caste} />
              </Section>

              <Section title="Parents">
                <TextField label="Father's Name" value={f.comp_father_name ?? ''}
                  onChange={(v) => setField('comp_father_name', nz(v))} />
                <TextField label="Mother's Name" value={f.comp_mother_name ?? ''}
                  onChange={(v) => setField('comp_mother_name', nz(v))} />
              </Section>

              <Section title="Identification">
                <TextField label="Aadhaar Reference No. *"
                  value={f.comp_aadhaar_ref_no ?? ''}
                  onChange={(v) => setField('comp_aadhaar_ref_no', nz(v.replace(/\D/g, '')))}
                  maxLength={12} inputMode="numeric"
                  placeholder="12-digit Aadhaar" />
                <SelectField label="Other UID Type" value={f.comp_uid_type ?? ''}
                  onChange={(v) => setField('comp_uid_type', nz(v))}
                  options={opts.uid} />
                <TextField label="Other UID Number" value={f.comp_uid_number ?? ''}
                  onChange={(v) => setField('comp_uid_number', nz(v))} />
              </Section>

              <Section title="Contact">
                <TextField label="Email" type="email" value={f.comp_email ?? ''}
                  onChange={(v) => setField('comp_email', nz(v))}
                  inputMode="email" />
                <TextField label="Mobile" value={f.comp_mobile ?? ''}
                  onChange={(v) => setField('comp_mobile', nz(v.replace(/\D/g, '')))}
                  maxLength={10} inputMode="tel" />
                <TextField label="Alternate Mobile" value={f.comp_alt_mobile ?? ''}
                  onChange={(v) => setField('comp_alt_mobile', nz(v.replace(/\D/g, '')))}
                  maxLength={10} inputMode="tel" />
              </Section>

              <Section title="Address" cols={6}>
                <TextField label="House No" wrapperClassName="lg:col-span-1"
                  value={f.comp_address_house_no ?? ''}
                  onChange={(v) => setField('comp_address_house_no', nz(v))} />
                <TextField label="Street" wrapperClassName="lg:col-span-3"
                  value={f.comp_address_street ?? ''}
                  onChange={(v) => setField('comp_address_street', nz(v))} />
                <TextField label="City" wrapperClassName="lg:col-span-2"
                  value={f.comp_address_city ?? ''}
                  onChange={(v) => setField('comp_address_city', nz(v))} />
                <SelectField label="State" wrapperClassName="lg:col-span-2"
                  value={f.comp_address_state ?? ''}
                  onChange={(v) => setField('comp_address_state', nz(v))}
                  options={opts.states} />
                <TextField label="Pincode" wrapperClassName="lg:col-span-2"
                  value={f.comp_address_pincode ?? ''}
                  onChange={(v) => setField('comp_address_pincode', nz(v.replace(/\D/g, '')))}
                  maxLength={6} inputMode="numeric" />
                <TextField label="Country" wrapperClassName="lg:col-span-2"
                  value={f.comp_address_country ?? 'India'}
                  onChange={(v) => setField('comp_address_country', nz(v))} />
              </Section>
            </div>
          )}
        </div>

        {/* Nav bar — Prev on the left; Save Draft + (Next OR Submit) on the right.
            Submit only shows on the last tab (Complainant). Full auto-decisions
            (threshold + jurisdiction) land in Phase 1b.3; today Submit persists
            the entry and returns the operator to the Masking Application page. */}
        <div className="flex items-center justify-between mt-6">
          <button type="button" onClick={() => setTab((t) => Math.max(0, t - 1))}
            disabled={tab === 0}
            className="flex items-center gap-1 px-4 py-2 text-sm font-semibold rounded-xl transition disabled:opacity-30"
            style={{ background: 'var(--ksp-yellow)', color: '#000', border: '2px solid rgba(0,0,0,0.25)' }}>
            <ChevronLeft className="w-4 h-4" /> Previous
          </button>

          <div className="flex items-center gap-3">
            <button type="button" onClick={handleSaveDraft} disabled={saving}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-xl transition disabled:opacity-50"
              style={{ background: '#fff', color: 'var(--ksp-navy)', border: '2px solid var(--ksp-navy)' }}>
              <Save className="w-4 h-4" /> {saving ? 'Saving…' : 'Save Draft'}
            </button>
            <button type="button" onClick={() => navigate(`/complaints/${encodeURIComponent(ackNo!)}`)}
              className="px-4 py-2 text-sm font-semibold rounded-xl"
              style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--ksp-navy)', border: '2px solid rgba(0,0,0,0.1)' }}>
              Exit
            </button>
            {tab < TABS.length - 1 ? (
              <button type="button" onClick={() => setTab((t) => Math.min(TABS.length - 1, t + 1))}
                className="flex items-center gap-1 px-5 py-2.5 font-semibold rounded-xl transition"
                style={{ background: 'var(--ksp-navy)', color: 'var(--ksp-yellow)', border: '2px solid rgba(0,0,0,0.25)' }}>
                Next <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button type="button" onClick={handleSubmit} disabled={saving}
                className="flex items-center gap-2 px-6 py-2.5 font-bold rounded-xl transition disabled:opacity-50"
                style={{ background: 'var(--ksp-yellow)', color: '#000', border: '2px solid rgba(0,0,0,0.25)' }}>
                <Save className="w-4 h-4" /> {saving ? 'Submitting…' : 'Submit FIR'}
              </button>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
