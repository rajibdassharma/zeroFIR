/** Shared TypeScript types — mirror the backend Pydantic schemas.
 *  When a schema field is added/removed on the backend, update the
 *  matching type here so the API-client + component code stays typed.
 *
 *  Two outbound bundles per complaint:
 *    ncrp_data     → what goes back to NCRP (APIs 2/5)
 *    police_it_v2  → what goes to Police IT V2 to raise the FIR
 *  Both keyed on `acknowledgement_no`.
 */

// ── Master data ───────────────────────────────────────────────
export interface UserOption {
  username: string;
  role: string;
}

export interface PoliceStation {
  id: number;
  name: string;
}

// ── Inbox row ────────────────────────────────────────────────
export interface ComplaintListItem {
  acknowledgement_no: string;
  complainant_name: string;
  complainant_mobile: string;
  category: string | null;
  total_fraud_amount: string | null;
  ps_id: number | null;
  ps_name: string | null;
  status: string;
  received_at: string;
}

// ── NCRP-side child rows (read view) ─────────────────────────
export interface NcrpTransaction {
  id: string;
  sub_category: string | null;
  bank_wallet: string | null;
  account_id: string | null;
  transaction_id: string | null;
  transaction_date: string | null;
  approx_time: string | null;
  amount: string | null;
  reference_no: string | null;
  other: string | null;
}

export interface NcrpSuspectAccount {
  id: string;
  bank_wallet: string | null;
  account_id: string | null;
  ifsc_code: string | null;
  account_holder_name: string | null;
  amount_credited: string | null;
  credited_on: string | null;
  remarks: string | null;
}

export interface NcrpEfirAnswer {
  id: string;
  question_code: string;
  question_text: string;
  answer: boolean;
}

// ── NCRP-side full view (backend NcrpDataView) ───────────────
export interface NcrpDataView {
  acknowledgement_no: string;
  category: string | null;
  call_start_at: string | null;

  complainant_name: string;
  complainant_gender: string | null;
  complainant_dob: string | null;
  complainant_mobile: string;
  complainant_email: string | null;
  complainant_relation_type: string | null;
  complainant_relation_name: string | null;

  address_house_no: string | null;
  address_street: string | null;
  address_colony: string | null;
  address_city: string | null;
  address_tehsil: string | null;
  address_country: string | null;
  address_state: string | null;
  address_district: string | null;
  address_ps_name: string | null;
  address_pincode: string | null;

  incident_place: string | null;
  additional_information: string | null;

  has_suspect_account_details: boolean;
  suspect_mobiles: string[];
  transactions: NcrpTransaction[];
  suspect_accounts: NcrpSuspectAccount[];
  efir_answers: NcrpEfirAnswer[];
  received_at: string;
}

// ── Police IT V2 outbound (FIR entry sections 1-6) ──────────
export interface FirAct {
  id?: string;
  act_code: string | null;
  act_name: string | null;
  sections: string | null;
  offence_type: string | null;
  gravity: string | null;
}

export interface FirEntry {
  // Section 1
  ps_details_district: string | null;
  ps_details_sub_division: string | null;
  ps_details_ps_name: string | null;
  ps_details_entry_date: string | null;
  ps_details_last_fir_no: string | null;
  ps_details_last_fir_time: string | null;
  ps_details_gsc_no: string | null;
  zero_fir_no: string | null;

  // Section 2
  fir_summary: string | null;

  // Section 3
  crime_classification_major: string | null;
  crime_classification_minor: string | null;
  offences_involve_aadhaar: boolean | null;
  acts: FirAct[];

  // Section 4
  incident_from_at: string | null;
  incident_to_at: string | null;
  info_received_at_ps_at: string | null;
  mode_of_complaint: string | null;
  fir_case_type: string | null;
  shd_reference: string | null;
  reasons_for_delay: string | null;
  complainant_saw_occurrence: boolean | null;

  // Section 5
  poi_house_no: string | null;
  poi_street: string | null;
  poi_colony: string | null;
  poi_beat_name: string | null;
  poi_village: string | null;
  poi_city: string | null;
  poi_tehsil: string | null;
  poi_district: string | null;
  poi_state: string | null;
  poi_country: string | null;
  poi_police_station: string | null;
  poi_pincode: string | null;
  poi_distance_from_ps: string | null;
  poi_direction_from_ps: string | null;
  poi_mla_constituency: string | null;
  poi_mp_constituency: string | null;
  poi_is_forest: boolean | null;
  poi_is_sea: boolean | null;
  poi_location_nature: string | null;
  poi_latitude: string | null;
  poi_longitude: string | null;
  poi_other_juris_state: string | null;
  poi_other_juris_district: string | null;
  poi_other_juris_ps: string | null;

  // Section 6 (extras beyond NCRP)
  comp_relation_to_victim: string | null;
  comp_role: string | null;
  comp_first_name: string | null;
  comp_middle_name: string | null;
  comp_last_name: string | null;
  comp_dob: string | null;
  comp_age: number | null;
  comp_gender: string | null;
  comp_nationality: string | null;
  comp_occupation: string | null;
  comp_religion: string | null;
  comp_caste: string | null;
  comp_father_name: string | null;
  comp_mother_name: string | null;
  comp_uid_type: string | null;
  comp_uid_number: string | null;
  comp_aadhaar_ref_no: string | null;
  comp_email: string | null;
  comp_mobile: string | null;
  comp_alt_mobile: string | null;
  comp_address_house_no: string | null;
  comp_address_street: string | null;
  comp_address_city: string | null;
  comp_address_state: string | null;
  comp_address_pincode: string | null;
  comp_address_country: string | null;
}

export interface FirMasterDropdowns {
  acts: { code: string; name: string }[];
  mode_of_complaint: string[];
  fir_case_type: string[];
  offence_type: string[];
  gravity: string[];
  direction: string[];
  uid_type: string[];
  relation_to_victim: string[];
  complainant_role: string[];
  indian_states: string[];
  incident_place: string[];
  crime_major_head: string[];
  crime_minor_head: string[];
  religion: string[];
  caste: string[];
}

// ── Complaint detail (composed) ──────────────────────────────
export interface ComplaintDetail {
  acknowledgement_no: string;
  ps_id: number | null;
  ps_name: string | null;
  picked_up_by: number | null;
  picked_up_at: string | null;

  status: string;

  total_fraud_amount: string | null;
  above_threshold: boolean | null;
  threshold_at_decision: string | null;
  within_karnataka_jurisdiction: boolean | null;

  zero_fir_no: string | null;
  v2_fir_no: string | null;
  fir_summary: string | null;

  efir_pushed_at: string | null;
  notice_lien_pulled_at: string | null;
  registered_pushed_at: string | null;

  created_at: string;
  updated_at: string;

  ncrp_data: NcrpDataView;
  police_it_v2: FirEntry;
}

// ── NCRP push payload (Call-Centre create/edit; mirrors API 1) ─
export interface NcrpTransactionPayload {
  sub_category: string | null;
  bank_wallet: string | null;
  account_id: string | null;
  transaction_id: string | null;
  transaction_date: string | null;
  approx_time: string | null;
  amount: string | null;
  reference_no: string | null;
  other: string | null;
}

export interface NcrpSuspectAccountPayload {
  bank_wallet: string | null;
  account_id: string | null;
  ifsc_code: string | null;
  account_holder_name: string | null;
  amount_credited: string | null;
  credited_on: string | null;
  remarks: string | null;
}

export interface NcrpEfirAnswerPayload {
  question_code: string;
  question_text: string;
  answer: boolean;
}

export interface NcrpAddressPayload {
  house_no: string | null;
  street: string | null;
  colony: string | null;
  city: string | null;
  tehsil: string | null;
  country: string | null;
  state: string | null;
  district: string | null;
  police_station: string | null;
  pincode: string | null;
}

export interface NcrpComplainantPayload {
  name: string;
  gender: string | null;
  dob: string | null;
  mobile: string;
  email: string | null;
  relation_type: string | null;
  relation_name: string | null;
}

export interface NcrpComplaintPushRequest {
  acknowledgement_no: string;
  category: string | null;
  call_start_at: string | null;
  complainant: NcrpComplainantPayload;
  address: NcrpAddressPayload;
  incident_place: string | null;
  additional_information: string | null;
  has_suspect_account_details: boolean;
  suspect_mobiles: string[];
  transactions: NcrpTransactionPayload[];
  suspect_accounts: NcrpSuspectAccountPayload[];
  efir_answers: NcrpEfirAnswerPayload[];
}

export interface NcrpComplaintPushResponse {
  ok: boolean;
  acknowledgement_no: string;
  ps_id: number | null;
  ps_matched: boolean;
  duplicate: boolean;
}

// ── Outbound audit event (Sent Messages) ─────────────────────
export interface OutboundEvent {
  id: string;
  direction: 'outbound' | 'inbound';
  target_system: 'NCRP' | 'POLICE_IT_V2' | 'CRIMAC' | 'E_LOST';
  event_type: string;                       // slug (see backend EVENT_TYPES)
  status: 'placeholder' | 'success' | 'failed';
  payload: unknown | null;
  response: unknown | null;
  notes: string | null;
  created_at: string;                       // ISO datetime
}

// ── Session ───────────────────────────────────────────────────
export interface SessionUser {
  user_id: number;
  role: string;
  full_name: string | null;
}
