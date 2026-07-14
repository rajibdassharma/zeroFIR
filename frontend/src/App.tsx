import { Navigate, Route, Routes } from 'react-router';
import { RequireAuth } from './components/RequireAuth';
import { ComplaintsListPage } from './pages/ComplaintsListPage';
import { FirEntryPage } from './pages/FirEntryPage';
import { LoginPage } from './pages/LoginPage';
import { MaskingApplicationPage } from './pages/MaskingApplicationPage';
import { NcrpEntryPage } from './pages/NcrpEntryPage';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/complaints" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/complaints"
        element={
          <RequireAuth>
            <ComplaintsListPage />
          </RequireAuth>
        }
      />
      <Route
        path="/complaints/new"
        element={
          <RequireAuth>
            <NcrpEntryPage />
          </RequireAuth>
        }
      />
      <Route
        path="/complaints/:ackNo/ncrp"
        element={
          <RequireAuth>
            <NcrpEntryPage />
          </RequireAuth>
        }
      />
      <Route
        path="/complaints/:ackNo"
        element={
          <RequireAuth>
            <MaskingApplicationPage />
          </RequireAuth>
        }
      />
      <Route
        path="/complaints/:ackNo/fir-entry"
        element={
          <RequireAuth>
            <FirEntryPage />
          </RequireAuth>
        }
      />
      {/* Phase 1c: /dashboards, /reports */}
    </Routes>
  );
}
