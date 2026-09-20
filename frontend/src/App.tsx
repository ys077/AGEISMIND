import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from './store/appDataStore';
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
      <p className="text-slate-500 text-sm mt-1">Aggregated Predictive Risk</p>
    </div>
    <div className="h-[calc(100vh-180px)]">
      <RiskHeatmap mode="global" />
    </div>
  </MainLayout>
);

function App() {
  const { preloadApp, isPreloading, preloadError } = useAppStore();

  useEffect(() => {
    preloadApp();
  }, [preloadApp]);

  if (isPreloading) {
    return (
      <div className="flex h-screen bg-slate-50 items-center justify-center">
        <div className="text-slate-500 flex flex-col items-center">
          <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mb-4"></div>
          <p className="font-semibold">Initializing AgeisMind Intelligence Platform...</p>
        </div>
      </div>
    );
  }

  if (preloadError) {
    return (
      <div className="flex h-screen bg-slate-50 items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow border border-red-200 text-center">
          <h2 className="text-lg font-bold text-slate-900 mb-2">Initialization Failed</h2>
          <p className="text-slate-600">{preloadError}</p>
          <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700">Retry</button>
        </div>
      </div>
    );
  }

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
