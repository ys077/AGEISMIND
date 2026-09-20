import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { useAppStore } from '../store/appDataStore';
import { 
  ShieldAlert, 
  IndianRupee, 
  FileText, 
  MapPin, 
  ArrowUpRight, 
  ChevronRight, 
  Clock, 
  Compass, 
  Layers, 
  PieChart, 
  CheckCircle2, 
  RefreshCw, 
  BellRing, 
  Activity, 
  Flame 
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { dashboardData: data, modelInfo, preloadApp } = useAppStore();
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await preloadApp(true); // Refreshes the cache
    setRefreshing(false);
  };

  React.useEffect(() => {
    preloadApp(false);
  }, []);

  const formatCurrency = (val: number) => {
    if (!val) return '₹0';
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    }
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} Lakh`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'ELEVATED':
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  if (!data) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-[70vh] gap-3 text-slate-500">
          <p className="text-sm font-medium">No dashboard data available.</p>
        </div>
      </MainLayout>
    );
  }

  const alertSummary = data?.alert_summary || {};
  const totalComplaints = data?.total_complaints || 0;
  const predictionCoverage = data?.prediction_coverage || 0;
  const totalFraud = data?.total_fraud_amount || 0;
  const avgFraud = data?.avg_fraud_amount || 0;
  const statusBreakdown = data?.status_breakdown || {};
  const underInvestigationCount = statusBreakdown['Under Investigation'] || 0;
  const resolvedCount = statusBreakdown['Resolved'] || 0;
  const modelVersion = modelInfo?.model_version || "unknown";

  return (
    <MainLayout>
      {/* Page Header */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-blue-100 text-blue-700 rounded-lg">
              <Compass size={20} />
            </span>
            <h2 className="text-2xl font-bold text-slate-900">Tamil Nadu Cyber Intelligence Command</h2>
          </div>
          <p className="text-slate-500 text-sm mt-1">
            Predictive Cash Withdrawal Intelligence
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Predictive Engine Active ({modelVersion})</span>
          </div>

          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={15} className={refreshing ? 'animate-spin text-blue-600' : ''} />
            <span>{refreshing ? 'Updating...' : 'Sync Data'}</span>
          </button>
        </div>
      </div>

      {/* Top Strategic KPI Banners */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Total Registered Complaints */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Prediction Coverage
            </span>
            <span className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <FileText size={18} />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{predictionCoverage.toLocaleString()}</span>
            <span className="text-sm font-semibold text-slate-500 flex items-center">
              / {totalComplaints.toLocaleString()} cases
            </span>
          </div>
          <div className="mt-3 flex items-center gap-3 text-xs text-slate-500 border-t border-slate-100 pt-2.5">
            <span className="flex items-center gap-1 font-medium text-amber-700">
              <Clock size={12} /> {underInvestigationCount} Active Cases
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 font-medium text-emerald-700">
              <CheckCircle2 size={12} /> {resolvedCount} Resolved
            </span>
          </div>
        </div>

        {/* Total Financial Exposure */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Financial Exposure
            </span>
            <span className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <IndianRupee size={18} />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{formatCurrency(totalFraud)}</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-2.5">
            <span>Avg Per Case: <strong className="text-slate-700">₹{Math.round(avgFraud).toLocaleString('en-IN')}</strong></span>
            <span className="text-[10px] text-slate-400">Total Siphoned</span>
          </div>
        </div>

        {/* Active Intercept Opportunities (Alerts) */}
        <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl border border-red-200 p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-red-700 uppercase tracking-wider flex items-center gap-1.5">
              <Flame size={14} className="text-red-600" /> Priorities
            </span>
            <button 
              onClick={() => navigate('/alerts')}
              className="p-1 text-red-600 hover:text-red-800 transition-colors flex items-center gap-0.5 text-xs font-bold"
            >
              Triage <ArrowUpRight size={14} />
            </button>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-red-700">
              {(alertSummary.high_priority || 0) + (alertSummary.critical_priority || 0)}
            </span>
            <span className="text-xs font-semibold text-red-600">High Priority candidates</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-red-800 border-t border-red-200/60 pt-2.5">
            <span>Queue: <strong>{alertSummary.total_alerts ?? 0} pending</strong></span>
          </div>
        </div>

        {/* Hotspot Vulnerability Index */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              High Risk Districts
            </span>
            <span className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <MapPin size={18} />
            </span>
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">
              {data?.districts_ranking?.filter((d: any) => d.risk_level === 'CRITICAL' || d.risk_level === 'HIGH').length || 0}
            </span>
            <span className="text-xs font-semibold text-amber-600">Active Clusters</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-2.5">
            <span>Primary: <strong className="text-slate-800">{data?.districts_ranking?.[0]?.city || 'N/A'}</strong></span>
            <button
              onClick={() => navigate('/heatmap')}
              className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-0.5"
            >
              Radar Map <ChevronRight size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Row 2: Visual Threat Analysis (Crime Categories & Top Hotspot Districts) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/* Crime Category & Financial Volume Distribution */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <PieChart size={18} className="text-blue-600" />
                  <span>Crime Category Typology & Financial Loss</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Proportionate financial exposure across major cybercrime classifications
                </p>
              </div>
              <span className="text-xs font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full">
                5 Major Sectors
              </span>
            </div>

            <div className="space-y-4">
              {(data?.categories_breakdown || []).map((cat: any, i: number) => {
                const colorPalette = [
                  { bg: 'bg-blue-500', bar: 'bg-blue-100', text: 'text-blue-700' },
                  { bg: 'bg-emerald-500', bar: 'bg-emerald-100', text: 'text-emerald-700' },
                  { bg: 'bg-indigo-500', bar: 'bg-indigo-100', text: 'text-indigo-700' },
                  { bg: 'bg-amber-500', bar: 'bg-amber-100', text: 'text-amber-700' },
                  { bg: 'bg-rose-500', bar: 'bg-rose-100', text: 'text-rose-700' },
                ];
                const theme = colorPalette[i % colorPalette.length];

                return (
                  <div key={cat.category} className="group">
                    <div className="flex justify-between items-center text-xs mb-1.5">
                      <span className="font-semibold text-slate-800 flex items-center gap-2">
                        <span className={`w-2.5 h-2.5 rounded-full ${theme.bg}`}></span>
                        {cat.category}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-500">{cat.count} cases</span>
                        <span className="font-bold text-slate-900">{formatCurrency(cat.amount)}</span>
                        <span className={`font-bold ${theme.text} w-10 text-right`}>{cat.percentage}%</span>
                      </div>
                    </div>
                    {/* Progress Track */}
                    <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${theme.bg} transition-all duration-500`} 
                        style={{ width: `${Math.min(100, Math.max(8, cat.percentage))}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Category Summary Footer */}
          <div className="mt-6 pt-4 border-t border-slate-100 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 rounded-lg bg-slate-50">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Top Threat</span>
              <strong className="text-slate-800 font-bold">{data?.categories_breakdown?.[0]?.category || 'N/A'}</strong>
            </div>
            <div className="p-2 rounded-lg bg-slate-50">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Top Modus Operandi</span>
              <strong className="text-slate-800 font-bold">{data?.fraud_types_breakdown?.[0]?.fraud_type || 'N/A'}</strong>
            </div>
            <div className="p-2 rounded-lg bg-slate-50">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Top Source Channel</span>
              <strong className="text-emerald-700 font-bold">{data?.channel_breakdown?.[0]?.channel || 'N/A'}</strong>
            </div>
          </div>
        </div>

        {/* Top Hotspot Districts Leaderboard */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <MapPin size={18} className="text-rose-600" />
                  <span>District Hotspot Vulnerability</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  High-density cash-out hubs identified by predictive spatial modeling
                </p>
              </div>
              <button
                onClick={() => navigate('/heatmap')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
              >
                Full Radar <ArrowUpRight size={13} />
              </button>
            </div>

            <div className="divide-y divide-slate-100">
              {(data?.districts_ranking || []).slice(0, 6).map((dist: any, idx: number) => (
                <div key={dist.city} className="py-2.5 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg transition-colors">
                  <div className="flex items-center gap-3">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      idx < 3 ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {idx + 1}
                    </span>
                    <div>
                      <h4 className="text-sm font-semibold text-slate-900 leading-tight">{dist.city}</h4>
                      <span className="text-[10px] font-medium text-slate-400">Code: {dist.district_id} • {dist.complaint_count} incidents</span>
                    </div>
                  </div>

                  <div className="text-right flex items-center gap-3">
                    <div>
                      <span className="text-xs font-bold text-slate-900 block">{formatCurrency(dist.total_fraud_amount)}</span>
                      <span className={`inline-block px-1.5 py-0.2 text-[9px] font-extrabold uppercase rounded border ${getRiskBadge(dist.risk_level)}`}>
                        {dist.risk_level}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100">
            <button
              onClick={() => navigate('/heatmap')}
              className="w-full py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1.5"
            >
              <Activity size={14} className="text-blue-600" />
              Launch Live Tamil Nadu Spatial Threat Heatmap
            </button>
          </div>
        </div>
      </div>

      {/* Row 3: Tactical Incident Stream & Typologies */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/* Recent High-Priority Complaints Feed */}
        <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <ShieldAlert size={18} className="text-amber-600" />
                <span>Recent High-Risk Incident Telemetry</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Recent cyber-financial cases undergoing predictive analysis
              </p>
            </div>
            <button
              onClick={() => navigate('/complaints')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              Registry View <ChevronRight size={14} />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-600 uppercase font-semibold">
                  <th className="py-2.5 px-3">Complaint ID</th>
                  <th className="py-2.5 px-3">Location</th>
                  <th className="py-2.5 px-3">Modus Operandi</th>
                  <th className="py-2.5 px-3 text-right">Loss Amount</th>
                  <th className="py-2.5 px-3">Intake Channel</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(data?.recent_complaints || []).map((item: any) => (
                  <tr 
                    key={item.complaint_id}
                    className="hover:bg-blue-50/40 cursor-pointer transition-colors"
                    onClick={() => navigate(`/complaints/${item.complaint_id}`)}
                  >
                    <td className="py-3 px-3 font-bold text-blue-600 font-mono">
                      #{item.complaint_id}
                    </td>
                    <td className="py-3 px-3 font-medium text-slate-800">
                      {item.victim_city} <span className="text-slate-400 text-[10px]">({item.district_id})</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-semibold text-slate-800">{item.fraud_type}</span>
                      <span className="block text-[10px] text-slate-400 truncate max-w-[140px]">{item.crime_category}</span>
                    </td>
                    <td className="py-3 px-3 text-right font-bold text-slate-900">
                      ₹{item.fraud_amount?.toLocaleString('en-IN') || '0'}
                    </td>
                    <td className="py-3 px-3 text-slate-600">
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-[10px] font-semibold">
                        {item.source_channel || 'Helpline 1930'}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        item.status === 'Resolved' 
                          ? 'bg-emerald-100 text-emerald-800' 
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {item.status || 'Active'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/complaints/${item.complaint_id}`);
                        }}
                        className="p-1 text-slate-400 hover:text-blue-600 transition-colors"
                      >
                        <ChevronRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Fraud Typologies Snapshot & Tactical Operations Hub */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          {/* Top Fraud Modus Operandi */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex-1">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-3">
              <Layers size={18} className="text-indigo-600" />
              <span>Prevalent Modus Operandi</span>
            </h3>
            
            <div className="space-y-2.5">
              {(data?.fraud_types_breakdown || []).slice(0, 5).map((ft: any) => (
                <div key={ft.fraud_type} className="flex items-center justify-between text-xs p-2 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors">
                  <div className="flex flex-col">
                    <span className="font-semibold text-slate-800">{ft.fraud_type}</span>
                    <span className="text-[10px] text-slate-500">{ft.count} incidents logged</span>
                  </div>
                  <span className="font-bold text-slate-900">{formatCurrency(ft.amount)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Operations Shortcuts */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-5 text-white shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold tracking-wider text-blue-400 uppercase">Investigator Tools</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              </div>
              <h4 className="text-sm font-bold mb-1">Prioritize Candidates</h4>
              <p className="text-xs text-slate-300 mb-4">
                Review model-ranked candidate locations for timely investigation.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => navigate('/alerts')}
                className="py-2.5 px-3 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-sm"
              >
                <BellRing size={14} /> Alert Triage ({alertSummary.total_alerts || 0})
              </button>

              <button
                onClick={() => navigate('/heatmap')}
                className="py-2.5 px-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-sm"
              >
                <Activity size={14} /> Risk Radar
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};
