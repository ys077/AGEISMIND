import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAppStore } from './store/appDataStore';
import { Dashboard } from './pages/Dashboard';
import './index.css';

const AlertsPage = lazy(() =>
  import('./pages/AlertsPage').then((m) => ({ default: m.AlertsPage }))
);
const ComplaintsList = lazy(() =>
  import('./pages/ComplaintsList').then((m) => ({ default: m.ComplaintsList }))
);
const ComplaintDetails = lazy(() =>
  import('./pages/ComplaintDetails').then((m) => ({ default: m.ComplaintDetails }))
);
const AuditTrail = lazy(() =>
  import('./pages/AuditTrail').then((m) => ({ default: m.AuditTrail }))
);
const GlobalHeatmapPage = lazy(() =>
  import('./pages/GlobalHeatmapPage').then((m) => ({ default: m.GlobalHeatmapPage }))
);

const RouteFallback = () => (
  <div className="flex h-screen bg-slate-50">
    <div className="w-64 bg-slate-900" />
    <div className="flex-1 p-6 space-y-4">
      <div className="h-8 w-72 bg-slate-200 rounded animate-pulse" />
      <div className="h-40 bg-slate-200 rounded animate-pulse" />
    </div>
  </div>
);

function App() {
  const preloadApp = useAppStore(state => state.preloadApp);

  useEffect(() => {
    preloadApp();
  }, [preloadApp]);

  return (
    <Router>
      <Suspense fallback={<RouteFallback />}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/complaints" element={<ComplaintsList />} />
          <Route path="/complaints/:complaintId" element={<ComplaintDetails />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/heatmap" element={<GlobalHeatmapPage />} />
          <Route path="/audit" element={<AuditTrail />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;
