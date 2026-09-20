import React, { useState, useEffect } from 'react';
import { getAlertSummary, getAlerts, getAlertDetail } from '../api/client';
import { AlertList } from '../components/alerts/AlertList';
import { AlertDetailsPane } from '../components/alerts/AlertDetailsPane';
import { AuditTimeline } from '../components/alerts/AuditTimeline';
import { ShieldAlert, Clock, CheckSquare, BellRing, Filter, Search, RefreshCw } from 'lucide-react';
import { MainLayout } from '../components/layout/MainLayout';
import { useAppStore } from '../store/appDataStore';

export const AlertsPage: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [selectedAlertDetail, setSelectedAlertDetail] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const { alertsList } = useAppStore();

  const loadAlertsData = async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) setRefreshing(true);
      
      const [sum, al] = await Promise.all([
        getAlertSummary(),
        getAlerts()
      ]);

      setSummary(sum);
      
      const sorted = (al || []).sort((a: any, b: any) => (b.probability || 0) - (a.probability || 0));
      setAlerts(sorted);

      // Auto-select first alert if none selected or current is invalid
      if (sorted.length > 0 && (!selectedAlertId || !sorted.some((a: any) => a.alert_id === selectedAlertId))) {
        setSelectedAlertId(sorted[0].alert_id);
      }
    } catch (err) {
      console.error("Failed to load alerts data", err);
    } finally {
      setLoading(false);
      if (isManualRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAlertsData();
  }, []);

  useEffect(() => {
    if (selectedAlertId) {
      getAlertDetail(selectedAlertId)
        .then(setSelectedAlertDetail)
        .catch(console.error);
    } else {
      setSelectedAlertDetail(null);
    }
  }, [selectedAlertId]);

  const handleAlertUpdated = () => {
    loadAlertsData();
    if (selectedAlertId) {
      getAlertDetail(selectedAlertId)
        .then(setSelectedAlertDetail)
        .catch(console.error);
    }
  };

  // Filtered alerts
  const filteredAlerts = alerts.filter((alert) => {
    const matchesPriority = priorityFilter === 'ALL' || alert.priority === priorityFilter;
    const matchesStatus = statusFilter === 'ALL' || alert.status === statusFilter;
    const q = searchQuery.toLowerCase();
    const matchesSearch = !q || 
      (alert.complaint_id && alert.complaint_id.toLowerCase().includes(q)) ||
      (alert.district && alert.district.toLowerCase().includes(q));
    return matchesPriority && matchesStatus && matchesSearch;
  });

  return (
    <MainLayout>
      {/* Header & Controls */}
      <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-red-100 text-red-700 rounded-lg">
              <BellRing size={20} />
            </span>
            <h2 className="text-2xl font-bold text-slate-900">Alerts & Threat Dispatch Center</h2>
          </div>
          <p className="text-slate-500 text-sm mt-1">
            Real-time probabilistic cash withdrawal alerts requiring immediate investigator triage and interdiction
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadAlertsData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={15} className={refreshing ? 'animate-spin text-blue-600' : ''} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Feed'}</span>
          </button>
        </div>
      </div>

      {/* Tactical KPI Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm flex flex-col">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
            <BellRing size={14} className="text-blue-500" /> Active Alert Queue
          </span>
          <span className="text-3xl font-bold text-slate-900">{summary ? summary.total_alerts : '--'}</span>
          <span className="text-[11px] text-slate-400 mt-1">Total pending investigation alerts</span>
        </div>
        
        <div className="bg-red-50 rounded-lg border border-red-200 p-4 shadow-sm flex flex-col">
          <span className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-2 flex items-center gap-2">
            <ShieldAlert size={14} /> Critical Threats
          </span>
          <span className="text-3xl font-bold text-red-700">{summary ? summary.high_priority : '--'}</span>
          <span className="text-[11px] text-red-600 font-medium mt-1">High probability (&gt;70%) cash-outs</span>
        </div>

        <div className="bg-amber-50 rounded-lg border border-amber-200 p-4 shadow-sm flex flex-col">
          <span className="text-xs font-semibold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-2">
            <Clock size={14} className="text-amber-600" /> Pending Review
          </span>
          <span className="text-3xl font-bold text-amber-900">
            {summary ? ((summary.in_review_alerts || summary.in_review || 0) + (summary.new_alerts || summary.new || 0)) : '--'}
          </span>
          <span className="text-[11px] text-amber-700 font-medium mt-1">Awaiting bank/field dispatch</span>
        </div>

        <div className="bg-emerald-50 rounded-lg border border-emerald-200 p-4 shadow-sm flex flex-col">
          <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider mb-2 flex items-center gap-2">
            <CheckSquare size={14} className="text-emerald-600" /> Actions Recorded
          </span>
          <span className="text-3xl font-bold text-emerald-900">
            {summary ? (summary.action_taken_alerts || summary.action_taken || 0) : '--'}
          </span>
          <span className="text-[11px] text-emerald-700 font-medium mt-1">Investigator actions logged</span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-3 mb-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 mr-1">
            <Filter size={13} /> Filters:
          </span>

          {/* Priority Pill Select */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  priorityFilter === p
                    ? 'bg-white text-slate-900 shadow-sm font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {p === 'ALL' ? 'All Priorities' : p}
              </button>
            ))}
          </div>

          {/* Status Select */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium">
            {['ALL', 'NEW', 'IN_REVIEW', 'ACTION_TAKEN'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  statusFilter === st
                    ? 'bg-white text-slate-900 shadow-sm font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {st === 'ALL' ? 'All Statuses' : st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={15} />
          <input
            type="text"
            placeholder="Search complaint ID or district..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white"
          />
        </div>
      </div>

      {/* 3-Column Tactical Workstation Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-320px)] min-h-[600px]">
        {/* Left Column: Filtered Alert Queue */}
        <div className="lg:col-span-3 h-full">
          <AlertList 
            alerts={filteredAlerts} 
            selectedAlertId={selectedAlertId || undefined} 
            onSelectAlert={(id) => { setSelectedAlertId(id); }} 
            loading={loading}
          />
        </div>

        {/* Middle Column: Detailed Alert Dossier & Actions */}
        <div className="lg:col-span-6 h-full">
          <AlertDetailsPane 
            alertId={selectedAlertId} 
            onAlertUpdated={handleAlertUpdated} 
            onViewMap={() => { window.location.href = '/heatmap'; }}
          />
        </div>

        {/* Right Column: Alert Forensic Audit Timeline */}
        <div className="lg:col-span-3 h-full">
          <AuditTimeline logs={selectedAlertDetail?.audit_logs || []} />
        </div>
      </div>
    </MainLayout>
  );
};
