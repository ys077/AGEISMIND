import React from 'react';
import { History, CheckCircle, MessageSquare, PlusCircle, ShieldAlert } from 'lucide-react';

export const AuditTimeline: React.FC<{ logs: any[] }> = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 text-sm text-slate-500 text-center flex flex-col items-center justify-center h-full">
        <History className="text-slate-300 mb-2" size={24} />
        <p className="font-semibold text-slate-700">No audit records found.</p>
        <p className="text-xs text-slate-400 mt-1">Actions taken by investigators or automated system alerts will appear here.</p>
      </div>
    );
  }

  // Sort logs by timestamp descending safely
  const sortedLogs = [...logs].sort((a, b) => {
    const timeA = new Date(a.timestamp || a.created_at || 0).getTime();
    const timeB = new Date(b.timestamp || b.created_at || 0).getTime();
    return timeB - timeA;
  });

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col h-full">
      <div className="bg-slate-50 border-b border-slate-200 p-4 sticky top-0 z-10 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Audit Timeline</h3>
          <p className="text-xs text-slate-500">System & Operator Activity Log ({sortedLogs.length} events)</p>
        </div>
      </div>

      <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
        <div className="relative border-l-2 border-slate-200 ml-3 space-y-6 pb-4">
          {sortedLogs.map((log, index) => {
            const rawTime = log.timestamp || log.created_at;
            const timeStr = rawTime ? new Date(rawTime).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'N/A';
            const rawAction = log.action_type || log.action || 'ACTIVITY_LOGGED';
            const actionText = rawAction.replace(/_/g, ' ').toLowerCase();
            const logId = log.audit_id || log.log_id || log.id || `audit_${index}`;
            const actor = log.actor_id || log.user || 'SYSTEM';

            let ActionIcon = History;
            let iconColor = 'text-slate-500';
            let iconBg = 'bg-slate-100';

            if (rawAction.includes('STATUS') || rawAction.includes('CHECK')) {
              ActionIcon = CheckCircle;
              iconColor = 'text-blue-600';
              iconBg = 'bg-blue-100';
            } else if (rawAction.includes('NOTE') || rawAction.includes('ACTION')) {
              ActionIcon = MessageSquare;
              iconColor = 'text-amber-600';
              iconBg = 'bg-amber-100';
            } else if (rawAction.includes('ALERT')) {
              ActionIcon = PlusCircle;
              iconColor = 'text-emerald-600';
              iconBg = 'bg-emerald-100';
            } else if (rawAction.includes('CRITICAL') || rawAction.includes('PREDICT')) {
              ActionIcon = ShieldAlert;
              iconColor = 'text-rose-600';
              iconBg = 'bg-rose-100';
            }

            return (
              <div key={logId} className="relative pl-6">
                {/* Timeline Icon */}
                <span className={`absolute left-[-13px] top-1 h-6 w-6 rounded-full flex items-center justify-center ${iconBg} ring-4 ring-white`}>
                  <ActionIcon size={12} className={iconColor} />
                </span>

                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-bold text-slate-900 capitalize">{actionText}</span>
                    <span className="text-xs font-medium text-slate-500">{timeStr}</span>
                  </div>

                  {log.complaint_id && (
                    <div className="text-xs font-mono text-blue-600">
                      Case #{log.complaint_id}
                    </div>
                  )}

                  {rawAction.includes('STATUS') && (log.data_hash || log.previous_status) && (
                    <div className="text-xs text-slate-600 mt-1 bg-slate-50 p-2 rounded border border-slate-200">
                      Details: <span className="font-semibold text-slate-800">{log.data_hash || `${log.previous_status} ➔ ${log.new_status}`}</span>
                    </div>
                  )}

                  {log.details && (
                    <div className="text-xs text-slate-700 mt-1 bg-amber-50 p-2.5 rounded border border-amber-200 italic">
                      "{log.details}"
                    </div>
                  )}

                  {log.entity_type && (
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Entity: <span className="font-mono text-slate-700">{log.entity_type} ({log.entity_id || 'N/A'})</span>
                    </div>
                  )}

                  <div className="text-[10px] font-semibold text-slate-400 mt-1 uppercase tracking-wider flex items-center gap-2">
                    <span>Operator: {actor}</span>
                    {log.data_hash && <span className="text-slate-300 font-mono text-[9px] truncate max-w-[120px]">Hash: {log.data_hash}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
