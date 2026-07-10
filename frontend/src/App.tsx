import { Navigate, Route, Routes } from 'react-router';
import { LoginPage } from './pages/LoginPage';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      {/* Phase 1+: /dashboard, /zero-firs/new, /zero-firs/:id, /transfers, /users */}
    </Routes>
  );
}
