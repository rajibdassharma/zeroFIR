import type {
  ComplaintDetail,
  ComplaintListItem,
  FirEntry,
  FirMasterDropdowns,
} from '../../types';
import { apiFetch } from './client';

export function listComplaints(status?: string) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiFetch<ComplaintListItem[]>(`/api/v1/complaints${qs}`);
}

export function getComplaint(ackNo: string) {
  return apiFetch<ComplaintDetail>(
    `/api/v1/complaints/${encodeURIComponent(ackNo)}`,
  );
}

/** PATCH the Police-IT-V2 draft (Section 1-6 fields). Server uses
 *  Pydantic `exclude_unset` so only keys explicitly present in the
 *  body are updated. `acts` is a full replacement of the child rows. */
export function saveV2Draft(ackNo: string, entry: Partial<FirEntry>) {
  return apiFetch<ComplaintDetail>(
    `/api/v1/complaints/${encodeURIComponent(ackNo)}/v2-draft`,
    { method: 'PATCH', body: JSON.stringify(entry) },
  );
}

/** POST /submit — fires the two outbound placeholders (NCRP push +
 *  Police IT V2 push) and advances workflow status to SUBMITTED.
 *  Frontend calls this AFTER a full save so any pending edits are
 *  already persisted. Body is empty. */
export function submitComplaint(ackNo: string) {
  return apiFetch<ComplaintDetail>(
    `/api/v1/complaints/${encodeURIComponent(ackNo)}/submit`,
    { method: 'POST' },
  );
}

export function getFirMasterDropdowns() {
  return apiFetch<FirMasterDropdowns>('/api/v1/fir-master/dropdowns/public');
}
