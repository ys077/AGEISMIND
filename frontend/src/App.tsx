import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { AlertsPage } from './pages/AlertsPage';
import { ComplaintsList } from './pages/ComplaintsList';
import { ComplaintDetails } from './pages/ComplaintDetails';
import { AuditTrail } from './pages/AuditTrail';
import { RiskHeatmap } from './components/RiskHeatmap';
import { MainLayout } from './components/layout/MainLayout';
import './index.css';

// A wrapper to render RiskHeatmap inside the MainLayout without selecting a specific complaint
const GlobalHeatmapPage = () => (
  <MainLayout>
    <div className="mb-6">
      <h2 className="text-2xl font-bold text-slate-900">Tamil Nadu Risk Radar</h2>
      <p className="text-slate-500 text-sm mt-1">Geographic intelligence and predictive threat modeling</p>
    </div>
    <div className="h-[calc(100vh-180px)]">
      <RiskHeatmap complaintId="ALL_COMPLAINTS" />
    </div>
  </MainLayout>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/complaints" element={<ComplaintsList />} />
        <Route path="/complaints/:complaintId" element={<ComplaintDetails />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/heatmap" element={<GlobalHeatmapPage />} />
        <Route path="/audit" element={<AuditTrail />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
