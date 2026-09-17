import React, { useState, useEffect } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { getAuditTrail, type AuditRecord } from '../api/client';
import { History, Search, Download } from 'lucide-react';
import { AuditTimeline } from '../components/alerts/AuditTimeline';

export const AuditTrail: React.FC = () => {
  const [logs, setLogs] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchAuditLogs = async () => {
      try {
        setLoading(true);
        const data = await getAuditTrail();
        setLogs(data || []);
      } catch (err) {
        console.error("Failed to fetch audit logs", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAuditLogs();
  }, []);

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (log.action_type && log.action_type.toLowerCase().includes(q)) ||
      (log.actor_id && log.actor_id.toLowerCase().includes(q)) ||
      (log.complaint_id && log.complaint_id.toLowerCase().includes(q)) ||
      (log.entity_id && log.entity_id.toLowerCase().includes(q))
    );
  });

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
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
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
          <AuditTimeline logs={filteredLogs} />
        )}
      </div>
    </MainLayout>
  );
};
