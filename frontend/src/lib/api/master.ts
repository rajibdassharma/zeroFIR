import type { District, PoliceStation, UserOption } from '../../types';
import { apiFetch } from './client';

export function listDistricts() {
  return apiFetch<District[]>('/api/v1/districts/public');
}

export function listPoliceStations(districtId: number) {
  return apiFetch<PoliceStation[]>(
    `/api/v1/districts/${districtId}/police-stations/public`,
  );
}

export function listUsersForPS(psId: number) {
  return apiFetch<UserOption[]>(`/api/v1/police-stations/${psId}/users/public`);
}

export function listSuperAdmins() {
  return apiFetch<UserOption[]>('/api/v1/users/super-admins/public');
}
