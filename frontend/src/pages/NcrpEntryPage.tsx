/** NCRP Entry — Call-Centre create + edit screen.
 *
 *  Two modes (URL param is the acknowledgement_no):
 *    - CREATE: `/complaints/new`          → POST /api/v1/complaints
 *    - EDIT:   `/complaints/:ackNo/ncrp`  → PATCH /api/v1/complaints/{ack_no}
 *
 *  Layout mirrors CyberFraud's data-entry screens — vertical left-side
 *  navigation grouped into two sections:
 *
 *    NCRP Fields                       Additional Fields for FIR
 *      · Complainant                     · Acts & Sections
 *      · Address                         · Time of Occurrence
 *      · Incident                        · Place of Incident
 *      · Suspects                        · Additional Info for FIR
 *      · Transactions
 *      · e-FIR Answers
 *
 *  On save we do TWO writes in sequence:
 *    1) create/edit the NCRP row (returns acknowledgement_no)
 *    2) PATCH the FIR-additional fields onto police_it_v2_data via
 *       `/api/v1/complaints/{ack_no}/v2-draft`
 *
 *  Both succeed → toast "Complaint saved" → back to inbox. If PS
 *  resolution failed (rare — dropdown normally guarantees it), a
 *  warning toast asks the operator to fix the PS and re-save.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { toast } from 'sonner';
import { AlertCircle, CheckCircle2, Save, Send } from 'lucide-react';
import { AppShell } from '../components/AppShell';
import {
  AddBtn, BoolRadio, NumField, RemBtn, Section, SelectField,
  TextAreaField, TextField,
} from '../components/form';
import { createComplaint, editComplaint } from '../lib/api/complaints';
import { getComplaint, getFirMasterDropdowns, saveV2Draft, submitComplaint } from '../lib/api/masking';
import { listPoliceStations } from '../lib/api/master';
import type {
  FirAct, FirEntry, FirMasterDropdowns,
  NcrpAddressPayload, NcrpComplainantPayload, NcrpComplaintPushRequest,
  NcrpEfirAnswerPayload, NcrpSuspectAccountPayload, NcrpTransactionPayload,
  PoliceStation,
} from '../types';

// ── Panel + tab metadata ────────────────────────────────────────
//
// Layout mirrors the NCRP portal itself (Screens 1–2 of the deck):
// two top-level tabs per side. The left sidebar picks which SIDE
// (NCRP vs Additional Fields for FIR), and the horizontal tab bar
// at the top of the content picks which SUB-TAB within that side.

type PanelKey = 'ncrp' | 'fir';

type NcrpTabKey = 'complainant_incident' | 'transactions_details';
type FirTabKey = 'acts' | 'time' | 'place' | 'fir_additional';
type TabKey = NcrpTabKey | FirTabKey;

interface TabDef<K extends TabKey> { key: K; label: string }

const NCRP_TABS: TabDef<NcrpTabKey>[] = [
  { key: 'complainant_incident', label: 'Complainant & Incident Details' },
  { key: 'transactions_details', label: "Transaction's Details" },
];

const FIR_TABS: TabDef<FirTabKey>[] = [
  { key: 'acts',           label: 'Acts & Sections' },
  { key: 'time',           label: 'Time of Occurrence' },
  { key: 'place',          label: 'Place of Incident' },
  { key: 'fir_additional', label: 'Additional Info for FIR' },
];

// ── Static option sets ──────────────────────────────────────────

const EFIR_QUESTIONS: { code: string; text: string }[] = [
  { code: 'amount_10_lakh_or_above',        text: 'Is the total fraud amount ₹10 lakh or above?' },
  { code: 'residing_in_state',              text: 'Is the complainant residing in Karnataka?' },
  { code: 'occurred_in_state_jurisdiction', text: 'Did the offence occur within Karnataka jurisdiction?' },
  { code: 'bns_318_4_cheated_delivered',    text: 'BNS 318(4) — was property delivered by way of cheating?' },
  { code: 'bns_319_pretending_someone_else',text: 'BNS 319 — did the offender pretend to be someone else?' },
  { code: 'bns_308_taken_through_threats',  text: 'BNS 308 — was property taken through threats?' },
  { code: 'bns_340_fake_document_electronic',text: 'BNS 340 — was a fake document or electronic record used?' },
];

const CATEGORY_OPTIONS = [
  '', 'Online Financial Fraud', 'Social Media Related Crime',
  'Cryptocurrency Fraud', 'Hacking / Data Breach',
  'Online Cyber Trafficking', 'Cyber Bullying / Stalking / Sextortion',
  'Other Cyber Crime',
];
const GENDER_OPTIONS = ['', 'M', 'F', 'Other', 'Prefer not to say'];
const RELATION_OPTIONS = ['', 'Father', 'Mother', 'Spouse', 'Son', 'Daughter', 'Guardian', 'Other'];
const TXN_TYPE_OPTIONS = ['', 'UPI', 'IMPS', 'NEFT', 'RTGS', 'Card', 'Net Banking', 'AEPS', 'ATM', 'Wallet', 'Cheque', 'Cash', 'Crypto', 'Other'];

// ── Small utilities ─────────────────────────────────────────────

const nz = (s: string): string | null => (s.trim() === '' ? null : s);
const toLocalDT = (iso: string | null): string => (iso === null ? '' : iso.slice(0, 16));
const fromLocalDT = (s: string): string | null => (s === '' ? null : `${s}:00`);

const emptyComplainant = (): NcrpComplainantPayload => ({
  name: '', gender: null, dob: null, mobile: '',
  email: null, relation_type: null, relation_name: null,
});
const emptyAddress = (): NcrpAddressPayload => ({
  house_no: null, street: null, colony: null, city: null,
  tehsil: null, country: 'India', state: 'Karnataka',
  district: null, police_station: null, pincode: null,
});
const emptyTxn = (): NcrpTransactionPayload => ({
  sub_category: null, bank_wallet: null, account_id: null,
  transaction_id: null, transaction_date: null, approx_time: null,
  amount: null, reference_no: null, other: null,
});
const emptySuspectAcct = (): NcrpSuspectAccountPayload => ({
  bank_wallet: null, account_id: null, ifsc_code: null,
  account_holder_name: null, amount_credited: null,
  credited_on: null, remarks: null,
});
const emptyAct = (): FirAct => ({
  act_code: null, act_name: null, sections: null,
  offence_type: null, gravity: null,
});
const defaultEfir = (): NcrpEfirAnswerPayload[] =>
  EFIR_QUESTIONS.map((q) => ({
    question_code: q.code, question_text: q.text, answer: false,
  }));

const emptyForm = (): NcrpComplaintPushRequest => ({
  acknowledgement_no: '',
  category: null,
  call_start_at: null,
  complainant: emptyComplainant(),
  address: emptyAddress(),
  incident_place: null,
  additional_information: null,
  has_suspect_account_details: false,
  suspect_mobiles: [],
  transactions: [],
  suspect_accounts: [],
  efir_answers: defaultEfir(),
});

/** FIR-draft form state — a subset of FirEntry covering ONLY the
 *  fields the CC operator captures at intake (sections 3, 4, 5, and
 *  section-6 extras). Sections 1 (PS Details) and 2 (FIR Summary)
 *  are police-side and stay on FirEntryPage. */
type FirIntakeForm = Partial<FirEntry>;

const emptyFirForm = (): FirIntakeForm => ({
  crime_classification_major: null,
  crime_classification_minor: null,
  offences_involve_aadhaar: null,
  acts: [],

  incident_from_at: null,
  incident_to_at: null,
  info_received_at_ps_at: null,
  mode_of_complaint: 'NCRP',   // caller-came-through-NCRP is the norm
  fir_case_type: null,
  shd_reference: null,
  reasons_for_delay: null,
  complainant_saw_occurrence: null,

  poi_house_no: null, poi_street: null, poi_colony: null,
  poi_beat_name: null, poi_village: null, poi_city: null,
  poi_tehsil: null, poi_district: null, poi_state: null,
  poi_country: 'India', poi_police_station: null, poi_pincode: null,
  poi_distance_from_ps: null, poi_direction_from_ps: null,
  poi_mla_constituency: null, poi_mp_constituency: null,
  poi_is_forest: null, poi_is_sea: null, poi_location_nature: null,
  poi_latitude: null, poi_longitude: null,
  poi_other_juris_state: null, poi_other_juris_district: null,
  poi_other_juris_ps: null,

  comp_relation_to_victim: null,
  comp_role: null,
  comp_middle_name: null,
  comp_nationality: null,
  comp_occupation: null,
  comp_religion: null,
  comp_caste: null,
  comp_father_name: null,
  comp_mother_name: null,
  comp_uid_type: null,
  comp_uid_number: null,
  comp_aadhaar_ref_no: null,
  comp_alt_mobile: null,
});

// ── Component ────────────────────────────────────────────────────

export function NcrpEntryPage() {
  const { ackNo } = useParams<{ ackNo: string }>();
  const navigate = useNavigate();
  const isEdit = !!ackNo;

  const [panel, setPanel] = useState<PanelKey>('ncrp');
  const [ncrpTab, setNcrpTab] = useState<NcrpTabKey>('complainant_incident');
  const [firTab, setFirTab] = useState<FirTabKey>('acts');
  const tab: TabKey = panel === 'ncrp' ? ncrpTab : firTab;
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [f, setF] = useState<NcrpComplaintPushRequest>(emptyForm());
  const [fir, setFir] = useState<FirIntakeForm>(emptyFirForm());
  const [master, setMaster] = useState<FirMasterDropdowns | null>(null);
  const [pses, setPSes] = useState<PoliceStation[]>([]);

  // Load master data + PS list on mount.
  useEffect(() => {
    getFirMasterDropdowns().then(setMaster).catch((e) => toast.error(e.message));
    listPoliceStations().then(setPSes).catch((e) => toast.error(e.message));
  }, []);

  // EDIT mode: hydrate from the existing complaint.
  useEffect(() => {
    if (!isEdit || !ackNo) return;
    setLoading(true);
    getComplaint(ackNo)
      .then((d) => {
        const c = d.ncrp_data;
        const answersByCode = new Map(
          c.efir_answers.map((a) => [a.question_code, a.answer]),
        );
        const efir = EFIR_QUESTIONS.map((q) => ({
          question_code: q.code, question_text: q.text,
          answer: answersByCode.get(q.code) ?? false,
        }));
        setF({
          acknowledgement_no: c.acknowledgement_no,
          category: c.category,
          call_start_at: c.call_start_at,
          complainant: {
            name: c.complainant_name,
            gender: c.complainant_gender,
            dob: c.complainant_dob,
            mobile: c.complainant_mobile,
            email: c.complainant_email,
            relation_type: c.complainant_relation_type,
            relation_name: c.complainant_relation_name,
          },
          address: {
            house_no: c.address_house_no, street: c.address_street,
            colony: c.address_colony, city: c.address_city,
            tehsil: c.address_tehsil, country: c.address_country,
            state: c.address_state, district: c.address_district,
            police_station: c.address_ps_name, pincode: c.address_pincode,
          },
          incident_place: c.incident_place,
          additional_information: c.additional_information,
          has_suspect_account_details: c.has_suspect_account_details,
          suspect_mobiles: c.suspect_mobiles,
          transactions: c.transactions.map((t) => ({
            sub_category: t.sub_category, bank_wallet: t.bank_wallet,
            account_id: t.account_id, transaction_id: t.transaction_id,
            transaction_date: t.transaction_date, approx_time: t.approx_time,
            amount: t.amount, reference_no: t.reference_no, other: t.other,
          })),
          suspect_accounts: c.suspect_accounts.map((sa) => ({
            bank_wallet: sa.bank_wallet, account_id: sa.account_id,
            ifsc_code: sa.ifsc_code, account_holder_name: sa.account_holder_name,
            amount_credited: sa.amount_credited, credited_on: sa.credited_on,
            remarks: sa.remarks,
          })),
          efir_answers: efir,
        });
        // Pull the FIR-additional fields off the same detail response.
        setFir({ ...emptyFirForm(), ...d.police_it_v2 });
      })
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  }, [ackNo, isEdit]);

  // Small setters.
  const setComp = <K extends keyof NcrpComplainantPayload>(k: K, v: NcrpComplainantPayload[K]) =>
    setF((prev) => ({ ...prev, complainant: { ...prev.complainant, [k]: v } }));
  const setAddr = <K extends keyof NcrpAddressPayload>(k: K, v: NcrpAddressPayload[K]) =>
    setF((prev) => ({ ...prev, address: { ...prev.address, [k]: v } }));
  const setFirField = <K extends keyof FirIntakeForm>(k: K, v: FirIntakeForm[K]) =>
    setFir((prev) => ({ ...prev, [k]: v }));

  // ── Save + Submit ────────────────────────────────────────────
  // Save Draft = persist 1930 + FIR fields, no outbound push,
  //              status stays IN_PROGRESS. Requires only the bare
  //              identifiers so a partial draft can be stored.
  // Submit     = persist + fire NCRP + Police IT V2 outbound
  //              placeholders + advance status to SUBMITTED. Requires
  //              every mandatory field across every tab.

  const jumpTo = (panel: PanelKey, tab: TabKey) => {
    setPanel(panel);
    if (panel === 'ncrp') setNcrpTab(tab as NcrpTabKey);
    else setFirTab(tab as FirTabKey);
  };

  /** Draft-time validation — just the bare identifiers so we can
   *  persist without wiping the placeholder MA row. */
  const validateDraft = (): boolean => {
    if (!f.acknowledgement_no.trim()) { toast.error('Acknowledgement No is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.complainant.name.trim())   { toast.error('Complainant name is required');   jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.complainant.mobile.trim()) { toast.error('Complainant mobile is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.address.police_station)    { toast.error('Police Station is required');     jumpTo('ncrp', 'complainant_incident'); return false; }
    return true;
  };

  /** Submit-time validation — every mandatory field across all six
   *  tabs. Jumps to the first offending tab and shows a specific
   *  toast so the operator knows exactly what's missing.
   *
   *  Kept in the same order as `_TAB_REQUIREMENTS` below so a change
   *  in one place stays consistent with the tab-completion badges. */
  const validateSubmit = (): boolean => {
    // ── 1930 Fields → Complainant & Incident Details ─────────────
    if (!f.acknowledgement_no.trim()) { toast.error('Acknowledgement No is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.complainant.name.trim())   { toast.error('Complainant Full Name is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.complainant.mobile.trim()) { toast.error('Complainant Mobile is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.complainant.dob)           { toast.error('Complainant Date of Birth is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.complainant.gender)        { toast.error('Complainant Gender is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.address.city)              { toast.error('Complainant Address — City/Village is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.address.state)             { toast.error('Complainant Address — State is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.address.district)          { toast.error('Complainant Address — District is required'); jumpTo('ncrp', 'complainant_incident'); return false; }
    if (!f.address.police_station)    { toast.error('Complainant Address — Police Station is required'); jumpTo('ncrp', 'complainant_incident'); return false; }

    // ── 1930 Fields → Transaction's Details ─────────────────────
    const hasValidTxn = f.transactions.some((t) => t.amount != null && Number(t.amount) > 0);
    if (!hasValidTxn) { toast.error('At least one transaction with a valid amount is required'); jumpTo('ncrp', 'transactions_details'); return false; }

    // ── Additional Fields for FIR → Time of Occurrence ──────────
    if (!fir.incident_from_at) { toast.error('Incident From date-time is required'); jumpTo('fir', 'time'); return false; }
    if (!fir.incident_to_at)   { toast.error('Incident To date-time is required'); jumpTo('fir', 'time'); return false; }

    // ── Additional Fields for FIR → Place of Incident ───────────
    if (!fir.poi_city)           { toast.error('Place of Incident — City is required'); jumpTo('fir', 'place'); return false; }
    if (!fir.poi_district)       { toast.error('Place of Incident — District is required'); jumpTo('fir', 'place'); return false; }
    if (!fir.poi_state)          { toast.error('Place of Incident — State is required'); jumpTo('fir', 'place'); return false; }
    if (!fir.poi_police_station) { toast.error('Place of Incident — Police Station is required'); jumpTo('fir', 'place'); return false; }

    // ── Additional Fields for FIR → Additional Info for FIR ─────
    if (!fir.comp_aadhaar_ref_no) { toast.error('Aadhaar Reference No is required'); jumpTo('fir', 'fir_additional'); return false; }

    return true;
  };

  /** Which tabs have all their submit-time required fields filled.
   *  Powers the check-mark badges on the sidebar + top-tab pills. */
  const tabStatus = useMemo(() => ({
    complainant_incident: !!(
      f.acknowledgement_no.trim() && f.complainant.name.trim() &&
      f.complainant.mobile.trim() && f.complainant.dob &&
      f.complainant.gender && f.address.city && f.address.state &&
      f.address.district && f.address.police_station
    ),
    transactions_details: f.transactions.some(
      (t) => t.amount != null && Number(t.amount) > 0,
    ),
    acts: true,   // no hard-required fields at intake time
    time: !!(fir.incident_from_at && fir.incident_to_at),
    place: !!(
      fir.poi_city && fir.poi_state && fir.poi_district && fir.poi_police_station
    ),
    fir_additional: !!fir.comp_aadhaar_ref_no,
  } as Record<TabKey, boolean>), [f, fir]);

  const ncrpComplete = tabStatus.complainant_incident && tabStatus.transactions_details;
  const firComplete = tabStatus.acts && tabStatus.time && tabStatus.place && tabStatus.fir_additional;
  const allComplete = ncrpComplete && firComplete;

  /** Chase writes together — POST/PATCH the 1930 fields then PATCH
   *  the V2 draft. Returns the ack_no + whether V2 got persisted. */
  const persistAll = async () => {
    const res = isEdit
      ? await editComplaint(ackNo!, f)
      : await createComplaint(f);
    if (res.ps_matched) {
      await saveV2Draft(res.acknowledgement_no, fir);
    }
    return res;
  };

  const handleSaveDraft = async () => {
    if (!validateDraft()) return;
    setSaving(true);
    try {
      const res = await persistAll();
      if (res.ps_matched) {
        toast.success(isEdit ? 'Draft updated' : 'Saved as draft');
      } else {
        toast.warning(
          'Draft saved but PS could not be resolved — FIR-additional fields were not persisted. Fix the PS and re-save.',
        );
      }
      navigate('/complaints');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateSubmit()) return;
    setSaving(true);
    try {
      const res = await persistAll();
      if (!res.ps_matched) {
        toast.error(
          'Cannot submit — Police Station could not be resolved. Fix the PS and try again.',
        );
        return;
      }
      // Fires NCRP + Police IT V2 placeholders on the backend.
      await submitComplaint(res.acknowledgement_no);
      toast.success('Complaint submitted — outbound placeholders fired for NCRP + Police IT V2.');
      navigate('/complaints');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Submit failed');
    } finally {
      setSaving(false);
    }
  };

  // ── Memoized option sets ─────────────────────────────────────
  const dashOpt = { value: '', label: '— Select —' };
  const genderOpts = useMemo(() =>
    GENDER_OPTIONS.map((g) => ({ value: g, label: g || '— Select —' })), []);
  const relationOpts = useMemo(() =>
    RELATION_OPTIONS.map((r) => ({ value: r, label: r || '— Select —' })), []);
  const categoryOpts = useMemo(() =>
    CATEGORY_OPTIONS.map((c) => ({ value: c, label: c || '— Select —' })), []);
  const txnTypeOpts = useMemo(() =>
    TXN_TYPE_OPTIONS.map((t) => ({ value: t, label: t || '— Select —' })), []);
  const psOpts = useMemo(() => [
    dashOpt, ...pses.map((p) => ({ value: p.name, label: p.name })),
  ], [pses]);
  const opts = useMemo(() => {
    if (!master) {
      return { acts: [], mode: [], case_type: [], offence: [], gravity: [], direction: [], uid: [], relation: [], role: [], states: [], incident_place: [], major_head: [], minor_head: [], religion: [], caste: [] };
    }
    return {
      acts: [dashOpt, ...master.acts.map((a) => ({ value: a.code, label: a.name }))],
      mode: [dashOpt, ...master.mode_of_complaint.map((s) => ({ value: s, label: s }))],
      case_type: [dashOpt, ...master.fir_case_type.map((s) => ({ value: s, label: s }))],
      offence: [dashOpt, ...master.offence_type.map((s) => ({ value: s, label: s }))],
      gravity: [dashOpt, ...master.gravity.map((s) => ({ value: s, label: s }))],
      direction: [dashOpt, ...master.direction.map((s) => ({ value: s, label: s }))],
      uid: [dashOpt, ...master.uid_type.map((s) => ({ value: s, label: s }))],
      relation: [dashOpt, ...master.relation_to_victim.map((s) => ({ value: s, label: s }))],
      role: [dashOpt, ...master.complainant_role.map((s) => ({ value: s, label: s.replace(/_/g, ' ') }))],
      states: [dashOpt, ...master.indian_states.map((s) => ({ value: s, label: s }))],
      incident_place: [dashOpt, ...master.incident_place.map((s) => ({ value: s, label: s }))],
      major_head: [dashOpt, ...master.crime_major_head.map((s) => ({ value: s, label: s }))],
      minor_head: [dashOpt, ...master.crime_minor_head.map((s) => ({ value: s, label: s }))],
      religion: [dashOpt, ...master.religion.map((s) => ({ value: s, label: s }))],
      caste: [dashOpt, ...master.caste.map((s) => ({ value: s, label: s }))],
    };
  }, [master]);

  if (loading) {
    return <AppShell><div className="text-center py-10 italic">Loading…</div></AppShell>;
  }

  // Little green ✓ / amber ! that tells the operator whether a tab
  // (or a whole panel) has captured every submit-time required field.
  const StatusDot = ({ complete }: { complete: boolean }) => (
    complete
      ? <CheckCircle2 className="w-4 h-4" style={{ color: '#0a6b28' }} />
      : <AlertCircle  className="w-4 h-4" style={{ color: '#b47500' }} />
  );

  // ── Left-sidebar panel link + top horizontal tab pill ────────
  const PanelLink = ({ p, label, complete }: {
    p: PanelKey; label: string; complete: boolean;
  }) => (
    <button type="button" onClick={() => setPanel(p)}
      className="flex items-center justify-between w-full text-left px-3 py-2.5 rounded-lg text-sm font-semibold transition"
      style={{
        background: panel === p ? 'var(--ksp-navy)' : 'transparent',
        color: panel === p ? 'var(--ksp-yellow)' : 'var(--ksp-navy)',
      }}>
      <span>{label}</span>
      <StatusDot complete={complete} />
    </button>
  );

  // Numbered-pill top tab in the CyberFraud style + completion dot.
  const TopTab = ({ i, label, active, complete, onClick }: {
    i: number; label: string; active: boolean; complete: boolean; onClick: () => void;
  }) => (
    <button type="button" onClick={onClick}
      className="px-4 py-2 text-sm font-semibold rounded-xl transition"
      style={{
        background: active ? 'var(--ksp-navy)' : 'var(--ksp-yellow)',
        color: active ? 'var(--ksp-yellow)' : '#000',
        border: '2px solid rgba(0,0,0,0.2)',
      }}>
      <span className="inline-flex items-center gap-1.5">
        <span className="w-5 h-5 rounded-full text-xs flex items-center justify-center font-bold"
          style={{
            background: active ? 'var(--ksp-yellow)' : 'var(--ksp-navy)',
            color: active ? 'var(--ksp-navy)' : 'var(--ksp-yellow)',
          }}>
          {i}
        </span>
        {label}
        <StatusDot complete={complete} />
      </span>
    </button>
  );

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        {/* Context strip */}
        <div className="rounded-2xl p-4 mb-4" style={{ background: 'var(--ksp-navy)', color: '#fff' }}>
          <div className="flex flex-wrap items-baseline gap-3 justify-between">
            <div>
              <Link to="/complaints" className="text-xs underline opacity-80">← Back to inbox</Link>
              <h1 className="text-lg font-bold" style={{ color: 'var(--ksp-yellow)' }}>
                {isEdit ? 'Edit NCRP Data' : 'New Complaint (Call-Centre Intake)'}
              </h1>
              <p className="text-xs mt-1">
                {isEdit
                  ? `Editing: ${f.acknowledgement_no}`
                  : 'Pick a section on the left; the tabs above the form show what belongs in that section.'}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-4">
          {/* ═════ Left sidebar ═════ */}
          <aside
            className="rounded-2xl p-3 h-fit sticky top-4 space-y-4"
            style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)', boxShadow: '0 6px 16px rgba(0,0,0,0.08)' }}
          >
            <div>
              <div className="text-xs uppercase font-bold mb-2 px-2 tracking-wide opacity-60">
                Sections
              </div>
              <div className="space-y-1">
                <PanelLink p="ncrp" label="1930 Fields" complete={ncrpComplete} />
                <PanelLink p="fir"  label="Additional Fields for FIR" complete={firComplete} />
              </div>
            </div>

            {/* Submit lives here (moved from bottom bar) so it's
                always visible without scrolling. Only enabled when
                every tab has captured its mandatory fields — on
                click we still run validateSubmit() as a defence-in-
                depth check + to surface the specific missing field. */}
            <div className="pt-3 border-t space-y-2" style={{ borderColor: 'rgba(0,0,0,0.08)' }}>
              <div className="text-xs px-2" style={{ color: allComplete ? '#0a6b28' : 'var(--ksp-red)' }}>
                {allComplete
                  ? 'All tabs complete — ready to submit.'
                  : 'Complete every tab (green ✓) before submitting.'}
              </div>
              <button type="button" onClick={handleSubmit} disabled={saving}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 font-bold rounded-xl transition disabled:opacity-50"
                style={{
                  background: allComplete ? 'var(--ksp-yellow)' : 'rgba(255,212,0,0.35)',
                  color: '#000',
                  border: '2px solid rgba(0,0,0,0.25)',
                }}>
                <Send className="w-4 h-4" />
                {saving ? 'Submitting…' : 'Submit Complaint'}
              </button>
            </div>
          </aside>

          {/* ═════ Main content ═════ */}
          <div className="space-y-4">
            {/* Horizontal top tab bar — mirrors the NCRP portal
                layout (two tabs on the NCRP side; four on the FIR side). */}
            <div className="flex flex-wrap gap-2">
              {panel === 'ncrp'
                ? NCRP_TABS.map((t, i) => (
                    <TopTab key={t.key} i={i + 1} label={t.label}
                      active={ncrpTab === t.key}
                      complete={tabStatus[t.key]}
                      onClick={() => setNcrpTab(t.key)} />
                  ))
                : FIR_TABS.map((t, i) => (
                    <TopTab key={t.key} i={i + 1} label={t.label}
                      active={firTab === t.key}
                      complete={tabStatus[t.key]}
                      onClick={() => setFirTab(t.key)} />
                  ))
              }
            </div>

            {tab === 'complainant_incident' && (
              <div className="space-y-5">
                {/* ── Screen 1 top strip on the NCRP portal — call
                     start date/time + acknowledgement + category. */}
                <Section title="Call Intake">
                  <TextField label="Acknowledgement No *" value={f.acknowledgement_no}
                    onChange={(v) => setF((p) => ({ ...p, acknowledgement_no: v }))}
                    placeholder="e.g. 30811260070042" />
                  <SelectField label="Category" value={f.category ?? ''}
                    onChange={(v) => setF((p) => ({ ...p, category: nz(v) }))}
                    options={categoryOpts} />
                  <TextField label="Call Started" type="datetime-local"
                    value={toLocalDT(f.call_start_at)}
                    onChange={(v) => setF((p) => ({ ...p, call_start_at: fromLocalDT(v) }))} />
                </Section>

                {/* ── Complainant / Victim Details block. */}
                <Section title="Complainant / Victim Details">
                  <TextField label="Full Name *" value={f.complainant.name}
                    onChange={(v) => setComp('name', v)} />
                  <SelectField label="Gender" value={f.complainant.gender ?? ''}
                    onChange={(v) => setComp('gender', nz(v))} options={genderOpts} />
                  <TextField label="Date of Birth" type="date"
                    value={f.complainant.dob ?? ''}
                    onChange={(v) => setComp('dob', nz(v))} />
                  <TextField label="Mobile *" value={f.complainant.mobile}
                    onChange={(v) => setComp('mobile', v.replace(/\D/g, ''))}
                    maxLength={10} inputMode="tel" />
                  <TextField label="Email" type="email" value={f.complainant.email ?? ''}
                    onChange={(v) => setComp('email', nz(v))} inputMode="email" />
                  <SelectField label="Father / Mother / Spouse"
                    value={f.complainant.relation_type ?? ''}
                    onChange={(v) => setComp('relation_type', nz(v))} options={relationOpts} />
                  <TextField label="Relation Name" value={f.complainant.relation_name ?? ''}
                    onChange={(v) => setComp('relation_name', nz(v))}
                    placeholder="e.g. father's name" />
                </Section>

                {/* ── Complainant / Victim Address block. */}
                <Section title="Complainant / Victim Address">
                  <TextField label="House No" value={f.address.house_no ?? ''}
                    onChange={(v) => setAddr('house_no', nz(v))} />
                  <TextField label="Street" value={f.address.street ?? ''}
                    onChange={(v) => setAddr('street', nz(v))} />
                  <TextField label="Colony / Area" value={f.address.colony ?? ''}
                    onChange={(v) => setAddr('colony', nz(v))} />
                  <TextField label="Vill / Town / City" value={f.address.city ?? ''}
                    onChange={(v) => setAddr('city', nz(v))} />
                  <TextField label="Tehsil / Taluk" value={f.address.tehsil ?? ''}
                    onChange={(v) => setAddr('tehsil', nz(v))} />
                  <TextField label="District" value={f.address.district ?? ''}
                    onChange={(v) => setAddr('district', nz(v))}
                    placeholder="e.g. Bengaluru City" />
                  <TextField label="State" value={f.address.state ?? ''}
                    onChange={(v) => setAddr('state', nz(v))} />
                  <TextField label="Country" value={f.address.country ?? ''}
                    onChange={(v) => setAddr('country', nz(v))} />
                  <SelectField label="Police Station *" value={f.address.police_station ?? ''}
                    onChange={(v) => setAddr('police_station', nz(v))}
                    options={psOpts} />
                  <TextField label="Pincode" value={f.address.pincode ?? ''}
                    onChange={(v) => setAddr('pincode', nz(v.replace(/\D/g, '')))}
                    maxLength={6} inputMode="numeric" />
                </Section>

                {/* ── Incident context (place dropdown + free text). */}
                <Section title="Incident">
                  <SelectField label="Where did the incident occur?"
                    value={f.incident_place ?? ''}
                    onChange={(v) => setF((p) => ({ ...p, incident_place: nz(v) }))}
                    options={opts.incident_place}
                    wrapperClassName="col-span-full" />
                  <TextAreaField label="Additional Information about the incident"
                    value={f.additional_information ?? ''}
                    onChange={(v) => setF((p) => ({ ...p, additional_information: nz(v) }))}
                    rows={6} maxLength={500} />
                </Section>

                {/* ── Suspect Mobile Nos (Add-button pattern). */}
                <Section title="Suspect Mobile Numbers">
                  {f.suspect_mobiles.length === 0 && (
                    <p className="col-span-full text-sm italic opacity-60">
                      No suspect mobiles yet. Click Add below.
                    </p>
                  )}
                  {f.suspect_mobiles.map((m, i) => (
                    <div key={i} className="flex items-end gap-2">
                      <div className="flex-1">
                        <TextField label={`Mobile #${i + 1}`} value={m}
                          onChange={(v) => {
                            const arr = [...f.suspect_mobiles];
                            arr[i] = v.replace(/\D/g, '');
                            setF((p) => ({ ...p, suspect_mobiles: arr }));
                          }}
                          maxLength={12} inputMode="tel" />
                      </div>
                      <RemBtn onClick={() =>
                        setF((p) => ({ ...p, suspect_mobiles: p.suspect_mobiles.filter((_, j) => j !== i) }))
                      } />
                    </div>
                  ))}
                </Section>
                <AddBtn label="Add Suspect Mobile"
                  onClick={() => setF((p) => ({ ...p, suspect_mobiles: [...p.suspect_mobiles, ''] }))} />
              </div>
            )}

            {tab === 'transactions_details' && (
              <div className="space-y-5">
                <Section title="Victim's Debited Transactions">
                  <p className="col-span-full text-xs italic opacity-70">
                    One row per transaction debited from the victim's account.
                  </p>
                </Section>

                {f.transactions.map((t, i) => (
                  <div key={i} className="rounded-2xl p-5 space-y-3"
                    style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)',
                             boxShadow: '0 6px 16px rgba(0,0,0,0.08)' }}>
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold uppercase tracking-wide"
                        style={{ color: 'var(--ksp-red)' }}>Transaction #{i + 1}</h3>
                      <RemBtn onClick={() =>
                        setF((p) => ({ ...p, transactions: p.transactions.filter((_, j) => j !== i) }))
                      } />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <SelectField label="Type" value={t.sub_category ?? ''}
                        onChange={(v) => {
                          const arr = [...f.transactions];
                          arr[i] = { ...arr[i], sub_category: nz(v) };
                          setF((p) => ({ ...p, transactions: arr }));
                        }}
                        options={txnTypeOpts} />
                      <TextField label="Bank / Wallet" value={t.bank_wallet ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], bank_wallet: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                      <TextField label="Account ID" value={t.account_id ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], account_id: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                      <TextField label="Transaction ID" value={t.transaction_id ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], transaction_id: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                      <TextField label="Date" type="date" value={t.transaction_date ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], transaction_date: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                      <TextField label="Approx Time" value={t.approx_time ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], approx_time: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }}
                        placeholder="e.g. 09:37 PM" />
                      <NumField label="Amount (₹)"
                        value={t.amount === null ? null : Number(t.amount)}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], amount: v === null ? null : String(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                      <TextField label="Reference No" value={t.reference_no ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], reference_no: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                      <TextField label="Other" value={t.other ?? ''}
                        onChange={(v) => { const arr = [...f.transactions]; arr[i] = { ...arr[i], other: nz(v) }; setF((p) => ({ ...p, transactions: arr })); }} />
                    </div>
                  </div>
                ))}
                <AddBtn label="Add Transaction"
                  onClick={() => setF((p) => ({ ...p, transactions: [...p.transactions, emptyTxn()] }))} />

                {/* Suspect Accounts */}
                <Section title="Do You have Suspect Account Details?">
                  <div className="col-span-full">
                    <BoolRadio label="Suspect account details available"
                      value={f.has_suspect_account_details}
                      onChange={(v) => setF((p) => ({
                        ...p,
                        has_suspect_account_details: v ?? false,
                        suspect_accounts: v === true ? p.suspect_accounts : [],
                      }))} />
                  </div>
                </Section>

                {f.has_suspect_account_details && (
                  <>
                    {f.suspect_accounts.map((sa, i) => (
                      <div key={i} className="rounded-2xl p-5 space-y-3"
                        style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)',
                                 boxShadow: '0 6px 16px rgba(0,0,0,0.08)' }}>
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-bold uppercase tracking-wide"
                            style={{ color: 'var(--ksp-red)' }}>Suspect Account #{i + 1}</h3>
                          <RemBtn onClick={() =>
                            setF((p) => ({ ...p, suspect_accounts: p.suspect_accounts.filter((_, j) => j !== i) }))
                          } />
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                          <TextField label="Bank / Wallet" value={sa.bank_wallet ?? ''}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], bank_wallet: nz(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }} />
                          <TextField label="Account / UPI Id" value={sa.account_id ?? ''}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], account_id: nz(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }} />
                          <TextField label="IFSC" value={sa.ifsc_code ?? ''}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], ifsc_code: nz(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }} />
                          <TextField label="Account Holder Name" value={sa.account_holder_name ?? ''}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], account_holder_name: nz(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }} />
                          <NumField label="Amount Credited (₹)"
                            value={sa.amount_credited === null ? null : Number(sa.amount_credited)}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], amount_credited: v === null ? null : String(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }} />
                          <TextField label="Credited On" type="date" value={sa.credited_on ?? ''}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], credited_on: nz(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }} />
                          <TextField label="Remarks" value={sa.remarks ?? ''}
                            onChange={(v) => { const arr = [...f.suspect_accounts]; arr[i] = { ...arr[i], remarks: nz(v) }; setF((p) => ({ ...p, suspect_accounts: arr })); }}
                            wrapperClassName="sm:col-span-2 lg:col-span-3" />
                        </div>
                      </div>
                    ))}
                    <AddBtn label="Add Suspect Account"
                      onClick={() => setF((p) => ({
                        ...p, suspect_accounts: [...p.suspect_accounts, emptySuspectAcct()],
                      }))} />
                  </>
                )}

                {/* ── e-FIR Questions — pops as a modal in the NCRP
                     portal (screens 3–9) but shown inline here so the
                     operator can tick all seven at once. */}
                <Section title="e-FIR Questionnaire (BNS 2023)">
                  <div className="col-span-full space-y-2">
                    {f.efir_answers.map((a, i) => (
                      <label key={a.question_code}
                        className="flex items-start gap-3 p-3 rounded-lg cursor-pointer"
                        style={{ background: '#fff', border: '1px solid rgba(11,44,74,0.15)' }}>
                        <input type="checkbox" checked={a.answer}
                          onChange={(e) => {
                            const arr = [...f.efir_answers];
                            arr[i] = { ...arr[i], answer: e.target.checked };
                            setF((p) => ({ ...p, efir_answers: arr }));
                          }}
                          className="mt-1" />
                        <div>
                          <div className="text-sm font-semibold" style={{ color: 'var(--ksp-navy)' }}>
                            {a.question_text}
                          </div>
                          <div className="text-xs opacity-50 mt-0.5">{a.question_code}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </Section>
              </div>
            )}

            {/* ═════ Additional Fields for FIR ═════ */}

            {tab === 'acts' && (
              <div className="space-y-5">
                <Section title="Crime Classification">
                  <SelectField label="Major Head" value={fir.crime_classification_major ?? ''}
                    onChange={(v) => setFirField('crime_classification_major', nz(v))}
                    options={opts.major_head} />
                  <SelectField label="Minor Head" value={fir.crime_classification_minor ?? ''}
                    onChange={(v) => setFirField('crime_classification_minor', nz(v))}
                    options={opts.minor_head} />
                  <BoolRadio label="Involves Aadhaar?" value={fir.offences_involve_aadhaar ?? null}
                    onChange={(v) => setFirField('offences_involve_aadhaar', v)} />
                </Section>

                {(fir.acts ?? []).map((a, i) => (
                  <div key={i} className="rounded-2xl p-5 space-y-3"
                    style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)',
                             boxShadow: '0 6px 16px rgba(0,0,0,0.08)' }}>
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-bold uppercase tracking-wide"
                        style={{ color: 'var(--ksp-red)' }}>Act #{i + 1}</h3>
                      <RemBtn onClick={() => setFirField('acts', (fir.acts ?? []).filter((_, j) => j !== i))} />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <SelectField label="Act" value={a.act_code ?? ''}
                        onChange={(v) => {
                          const acts = [...(fir.acts ?? [])];
                          const label = master?.acts.find((m) => m.code === v)?.name ?? null;
                          acts[i] = { ...acts[i], act_code: nz(v), act_name: label };
                          setFirField('acts', acts);
                        }}
                        options={opts.acts} />
                      <TextField label="Sections (comma-separated)" value={a.sections ?? ''}
                        onChange={(v) => {
                          const acts = [...(fir.acts ?? [])];
                          acts[i] = { ...acts[i], sections: nz(v) };
                          setFirField('acts', acts);
                        }}
                        placeholder="e.g. 318(4), 319, 340" />
                      <SelectField label="Offence Type" value={a.offence_type ?? ''}
                        onChange={(v) => {
                          const acts = [...(fir.acts ?? [])];
                          acts[i] = { ...acts[i], offence_type: nz(v) };
                          setFirField('acts', acts);
                        }}
                        options={opts.offence} />
                      <SelectField label="Gravity" value={a.gravity ?? ''}
                        onChange={(v) => {
                          const acts = [...(fir.acts ?? [])];
                          acts[i] = { ...acts[i], gravity: nz(v) };
                          setFirField('acts', acts);
                        }}
                        options={opts.gravity} />
                    </div>
                  </div>
                ))}
                <AddBtn label="Add Act" onClick={() =>
                  setFirField('acts', [...(fir.acts ?? []), emptyAct()])
                } />
              </div>
            )}

            {tab === 'time' && (
              <Section title="Time of Occurrence">
                <TextField label="Incident From (date-time)" type="datetime-local"
                  value={toLocalDT(fir.incident_from_at ?? null)}
                  onChange={(v) => setFirField('incident_from_at', fromLocalDT(v))} />
                <TextField label="Incident To (date-time)" type="datetime-local"
                  value={toLocalDT(fir.incident_to_at ?? null)}
                  onChange={(v) => setFirField('incident_to_at', fromLocalDT(v))} />
                <TextField label="Info Received at PS (date-time)" type="datetime-local"
                  value={toLocalDT(fir.info_received_at_ps_at ?? null)}
                  onChange={(v) => setFirField('info_received_at_ps_at', fromLocalDT(v))} />
                <SelectField label="Mode of Complaint" value={fir.mode_of_complaint ?? ''}
                  onChange={(v) => setFirField('mode_of_complaint', nz(v))}
                  options={opts.mode} />
                <SelectField label="FIR Case Type" value={fir.fir_case_type ?? ''}
                  onChange={(v) => setFirField('fir_case_type', nz(v))}
                  options={opts.case_type} />
                <TextField label="SHD Reference" value={fir.shd_reference ?? ''}
                  onChange={(v) => setFirField('shd_reference', nz(v))} />
                <BoolRadio label="Complainant saw occurrence?"
                  value={fir.complainant_saw_occurrence ?? null}
                  onChange={(v) => setFirField('complainant_saw_occurrence', v)} />
                <TextAreaField label="Reasons for Delay (if any)"
                  value={fir.reasons_for_delay ?? ''}
                  onChange={(v) => setFirField('reasons_for_delay', nz(v))} rows={3} />
              </Section>
            )}

            {tab === 'place' && (
              <div className="space-y-5">
                <Section title="Address (of Incident)">
                  <TextField label="House No" value={fir.poi_house_no ?? ''}
                    onChange={(v) => setFirField('poi_house_no', nz(v))} />
                  <TextField label="Street" value={fir.poi_street ?? ''}
                    onChange={(v) => setFirField('poi_street', nz(v))} />
                  <TextField label="Colony / Locality / Area" value={fir.poi_colony ?? ''}
                    onChange={(v) => setFirField('poi_colony', nz(v))} />
                  <TextField label="Beat Name" value={fir.poi_beat_name ?? ''}
                    onChange={(v) => setFirField('poi_beat_name', nz(v))} />
                  <TextField label="Village" value={fir.poi_village ?? ''}
                    onChange={(v) => setFirField('poi_village', nz(v))} />
                  <TextField label="City" value={fir.poi_city ?? ''}
                    onChange={(v) => setFirField('poi_city', nz(v))} />
                  <TextField label="Tehsil / Block / Mandal" value={fir.poi_tehsil ?? ''}
                    onChange={(v) => setFirField('poi_tehsil', nz(v))} />
                  <TextField label="District" value={fir.poi_district ?? ''}
                    onChange={(v) => setFirField('poi_district', nz(v))} />
                  <SelectField label="State" value={fir.poi_state ?? ''}
                    onChange={(v) => setFirField('poi_state', nz(v))}
                    options={opts.states} />
                  <TextField label="Country" value={fir.poi_country ?? ''}
                    onChange={(v) => setFirField('poi_country', nz(v))} />
                  <SelectField label="Police Station (of incident)"
                    value={fir.poi_police_station ?? ''}
                    onChange={(v) => setFirField('poi_police_station', nz(v))}
                    options={psOpts} />
                  <TextField label="Pincode" value={fir.poi_pincode ?? ''}
                    onChange={(v) => setFirField('poi_pincode', nz(v.replace(/\D/g, '')))}
                    maxLength={6} inputMode="numeric" />
                </Section>

                <Section title="Location Context">
                  <TextField label="Distance from PS" value={fir.poi_distance_from_ps ?? ''}
                    onChange={(v) => setFirField('poi_distance_from_ps', nz(v))}
                    placeholder="e.g. 12 km" />
                  <SelectField label="Direction from PS" value={fir.poi_direction_from_ps ?? ''}
                    onChange={(v) => setFirField('poi_direction_from_ps', nz(v))}
                    options={opts.direction} />
                  <TextField label="MLA Constituency" value={fir.poi_mla_constituency ?? ''}
                    onChange={(v) => setFirField('poi_mla_constituency', nz(v))} />
                  <TextField label="MP Constituency" value={fir.poi_mp_constituency ?? ''}
                    onChange={(v) => setFirField('poi_mp_constituency', nz(v))} />
                  <BoolRadio label="Forest Area?" value={fir.poi_is_forest ?? null}
                    onChange={(v) => setFirField('poi_is_forest', v)} />
                  <BoolRadio label="Sea?" value={fir.poi_is_sea ?? null}
                    onChange={(v) => setFirField('poi_is_sea', v)} />
                  <SelectField label="Nature of Location" value={fir.poi_location_nature ?? ''}
                    onChange={(v) => setFirField('poi_location_nature', nz(v))}
                    options={[
                      { value: '', label: '— Select —' },
                      { value: 'actual', label: 'Actual' },
                      { value: 'temporary', label: 'Temporary' },
                    ]} />
                  <TextField label="Latitude" value={fir.poi_latitude ?? ''}
                    onChange={(v) => setFirField('poi_latitude', nz(v))} placeholder="12.9716" />
                  <TextField label="Longitude" value={fir.poi_longitude ?? ''}
                    onChange={(v) => setFirField('poi_longitude', nz(v))} placeholder="77.5946" />
                </Section>

                <Section title="Other Jurisdiction (if applicable)">
                  <TextField label="State" value={fir.poi_other_juris_state ?? ''}
                    onChange={(v) => setFirField('poi_other_juris_state', nz(v))} />
                  <TextField label="District" value={fir.poi_other_juris_district ?? ''}
                    onChange={(v) => setFirField('poi_other_juris_district', nz(v))} />
                  <TextField label="Police Station" value={fir.poi_other_juris_ps ?? ''}
                    onChange={(v) => setFirField('poi_other_juris_ps', nz(v))} />
                </Section>
              </div>
            )}

            {tab === 'fir_additional' && (
              <div className="space-y-5">
                <Section title="Role & Relation">
                  <SelectField label="Relation to Victim" value={fir.comp_relation_to_victim ?? ''}
                    onChange={(v) => setFirField('comp_relation_to_victim', nz(v))}
                    options={opts.relation} />
                  <SelectField label="Role" value={fir.comp_role ?? ''}
                    onChange={(v) => setFirField('comp_role', nz(v))}
                    options={opts.role} />
                </Section>

                <Section title="Name & Personal">
                  <TextField label="Middle Name" value={fir.comp_middle_name ?? ''}
                    onChange={(v) => setFirField('comp_middle_name', nz(v))}
                    placeholder="NCRP only captures full name — split here if needed" />
                  <TextField label="Nationality" value={fir.comp_nationality ?? ''}
                    onChange={(v) => setFirField('comp_nationality', nz(v))}
                    placeholder="Indian" />
                  <TextField label="Occupation" value={fir.comp_occupation ?? ''}
                    onChange={(v) => setFirField('comp_occupation', nz(v))} />
                  <SelectField label="Religion" value={fir.comp_religion ?? ''}
                    onChange={(v) => setFirField('comp_religion', nz(v))}
                    options={opts.religion} />
                  <SelectField label="Caste" value={fir.comp_caste ?? ''}
                    onChange={(v) => setFirField('comp_caste', nz(v))}
                    options={opts.caste} />
                </Section>

                <Section title="Parents">
                  <TextField label="Father's Name" value={fir.comp_father_name ?? ''}
                    onChange={(v) => setFirField('comp_father_name', nz(v))} />
                  <TextField label="Mother's Name" value={fir.comp_mother_name ?? ''}
                    onChange={(v) => setFirField('comp_mother_name', nz(v))} />
                </Section>

                <Section title="Government ID">
                  <TextField label="Aadhaar Reference No. *"
                    value={fir.comp_aadhaar_ref_no ?? ''}
                    onChange={(v) => setFirField('comp_aadhaar_ref_no', nz(v.replace(/\D/g, '')))}
                    maxLength={12} inputMode="numeric"
                    placeholder="12-digit Aadhaar" />
                  <SelectField label="Other UID Type" value={fir.comp_uid_type ?? ''}
                    onChange={(v) => setFirField('comp_uid_type', nz(v))}
                    options={opts.uid} />
                  <TextField label="Other UID Number" value={fir.comp_uid_number ?? ''}
                    onChange={(v) => setFirField('comp_uid_number', nz(v))} />
                </Section>

                <Section title="Extra Contact">
                  <TextField label="Alternate Mobile" value={fir.comp_alt_mobile ?? ''}
                    onChange={(v) => setFirField('comp_alt_mobile', nz(v.replace(/\D/g, '')))}
                    maxLength={10} inputMode="tel" />
                </Section>
              </div>
            )}

            {/* ═════ Save bar ═════
                Only Save Draft + Cancel live here now. Submit
                Complaint moved to the left sidebar so it stays
                visible without scrolling and reads the tab-completion
                state at a glance. */}
            <div className="flex items-center justify-end gap-3 mt-6">
              <button type="button" onClick={() => navigate('/complaints')}
                className="px-4 py-2 text-sm font-semibold rounded-xl"
                style={{ background: 'rgba(0,0,0,0.05)', color: 'var(--ksp-navy)', border: '2px solid rgba(0,0,0,0.1)' }}>
                Cancel
              </button>
              <button type="button" onClick={handleSaveDraft} disabled={saving}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-xl transition disabled:opacity-50"
                style={{ background: '#fff', color: 'var(--ksp-navy)', border: '2px solid var(--ksp-navy)' }}>
                <Save className="w-4 h-4" />
                {saving ? 'Saving…' : 'Save Draft'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
