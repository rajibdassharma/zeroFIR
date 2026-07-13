/** Shared TypeScript types — mirror the backend Pydantic schemas.
 *  When a schema field is added/removed on the backend, update the
 *  matching type here so the API-client + component code stays typed. */

// ── Master data ───────────────────────────────────────────────
export interface District {
  id: number;
  name: string;
}

export interface PoliceStation {
  id: number;
  name: string;
  district_id: number;
}

export interface UserOption {
  username: string;
  role: string;
}

// ── Masking Application (inbox row) ───────────────────────────
export interface MaskedApplicationListItem {
  id: string;
  complaint_id: string;
  acknowledgement_no: string;
  complainant_name: string;
  complainant_mobile: string;
  category: string | null;
  total_fraud_amount: string | null; // Decimal is serialised as string
  ps_id: number;
  ps_name: string | null;
  status: string;
  received_at: string; // ISO datetime
}

// ── NCRP data (read-only view) ────────────────────────────────
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

export interface NcrpEfirAnswer {
  id: string;
  question_code: string;
  question_text: string;
  answer: boolean;
}

export interface NcrpComplaintView {
  id: string;
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

  incident_occurred_at: string | null;
  additional_information: string | null;

  suspect_mobiles: string[];
  transactions: NcrpTransaction[];
  efir_answers: NcrpEfirAnswer[];
  received_at: string;
}

// ── Masking Application (full detail) ─────────────────────────
export interface MaskedApplicationDetail {
  id: string;
  ps_id: number;
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

  complaint: NcrpComplaintView;
}

// ── Session ───────────────────────────────────────────────────
export interface SessionUser {
  user_id: number;
  role: string;
  full_name: string | null;
}
