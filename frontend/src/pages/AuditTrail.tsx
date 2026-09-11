import React, { useState, useEffect } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { getAlerts, getAlertDetail } from '../api/client';
import { History, Search, Download } from 'lucide-react';
import { AuditTimeline } from '../components/alerts/AuditTimeline';

export const AuditTrail: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Since we don't have a global /api/audit endpoint yet, 
    // we'll fetch all alerts, grab their details, and merge their audit logs
    const fetchAllAuditLogs = async () => {
      try {
        setLoading(true);
        const alertsData = await getAlerts();
        
        // Take the top 10 most recent alerts to avoid overwhelming the mock API
        const recentAlerts = alertsData.slice(0, 10);
        
        let allLogs: any[] = [];
        
        for (const alert of recentAlerts) {
          try {
            const detail = await getAlertDetail(alert.alert_id);
            if (detail && detail.audit_logs) {
              allLogs = [...allLogs, ...detail.audit_logs];
            }
          } catch (e) {
            console.error("Failed to fetch detail for alert", alert.alert_id);
          }
        }
        
        setLogs(allLogs);
      } catch (err) {
        console.error("Failed to fetch audit logs", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAllAuditLogs();
  }, []);

  return (
    <MainLayout>
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">System Audit Trail</h2>
          <p className="text-slate-500 text-sm mt-1">Immutable record of investigator actions and system events</p>
        </div>
        
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Search investigator or action..." 
              className="pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50">
            <Download size={16} />
            Export CSV
          </button>
        </div>
      </div>

      <div className="h-[calc(100vh-180px)]">
        {loading ? (
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm h-full flex flex-col items-center justify-center text-slate-500">
            <History className="animate-spin mb-4" size={32} />
            <p>Aggregating global audit records...</p>
          </div>
        ) : (
          <AuditTimeline logs={logs} />
        )}
      </div>
    </MainLayout>
  );
};
