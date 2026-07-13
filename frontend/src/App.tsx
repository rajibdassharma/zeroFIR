import { Navigate, Route, Routes } from 'react-router';
import { RequireAuth } from './components/RequireAuth';
import { ComplaintsListPage } from './pages/ComplaintsListPage';
import { LoginPage } from './pages/LoginPage';
import { MaskingApplicationPage } from './pages/MaskingApplicationPage';

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
        path="/complaints/:id"
        element={
          <RequireAuth>
            <MaskingApplicationPage />
          </RequireAuth>
        }
      />
      {/* Phase 1b: /complaints/:id/fir-entry (editable 15-section form) */}
      {/* Phase 1c: /dashboards, /reports */}
    </Routes>
  );
}
