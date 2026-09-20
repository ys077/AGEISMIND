import { MainLayout } from '../components/layout/MainLayout';
import { RiskHeatmap } from '../components/RiskHeatmap';

export const GlobalHeatmapPage = () => (
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
