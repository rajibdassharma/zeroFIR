/** Internal complaint CRUD — Call-Centre only.
 *  Mirrors the same payload shape API 1 accepts; the backend
 *  differentiates by route (X-API-Key on the NCRP-side endpoint,
 *  JWT on these internal ones).
 */
import type { NcrpComplaintPushRequest, NcrpComplaintPushResponse } from '../../types';
import { apiFetch } from './client';

export function createComplaint(body: NcrpComplaintPushRequest) {
  return apiFetch<NcrpComplaintPushResponse>('/api/v1/complaints', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function editComplaint(
  ackNo: string,
  body: NcrpComplaintPushRequest,
) {
  return apiFetch<NcrpComplaintPushResponse>(
    `/api/v1/complaints/${encodeURIComponent(ackNo)}`,
    { method: 'PATCH', body: JSON.stringify(body) },
  );
}
