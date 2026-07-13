import type {
  MaskedApplicationDetail,
  MaskedApplicationListItem,
} from '../../types';
import { apiFetch } from './client';

export function listMaskedApplications(status?: string) {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  return apiFetch<MaskedApplicationListItem[]>(`/api/v1/masked-applications${qs}`);
}

export function getMaskedApplication(id: string) {
  return apiFetch<MaskedApplicationDetail>(`/api/v1/masked-applications/${id}`);
}
