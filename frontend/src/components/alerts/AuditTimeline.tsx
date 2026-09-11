import React from 'react';
import { History, CheckCircle, MessageSquare, PlusCircle } from 'lucide-react';

export const AuditTimeline: React.FC<{ logs: any[] }> = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 text-sm text-slate-500 text-center flex flex-col items-center justify-center h-full">
        <History className="text-slate-300 mb-2" size={24} />
        No audit records found.
      </div>
    );
  }

  // Sort logs by timestamp descending
  const sortedLogs = [...logs].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col h-full">
      <div className="bg-slate-50 border-b border-slate-200 p-4 sticky top-0 z-10 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Audit Timeline</h3>
          <p className="text-xs text-slate-500">System & Operator Activity Log</p>
        </div>
      </div>

      <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
        <div className="relative border-l-2 border-slate-200 ml-3 space-y-6 pb-4">
          {sortedLogs.map((log) => {
            const timeStr = new Date(log.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
            
            let ActionIcon = History;
            let iconColor = 'text-slate-500';
            let iconBg = 'bg-slate-100';
            
            if (log.action === 'STATUS_UPDATE') {
              ActionIcon = CheckCircle;
              iconColor = 'text-blue-600';
              iconBg = 'bg-blue-100';
            }
            if (log.action === 'INVESTIGATOR_NOTE') {
              ActionIcon = MessageSquare;
              iconColor = 'text-amber-600';
              iconBg = 'bg-amber-100';
            }
            if (log.action === 'ALERT_CREATED') {
              ActionIcon = PlusCircle;
              iconColor = 'text-emerald-600';
              iconBg = 'bg-emerald-100';
            }

            return (
              <div key={log.log_id} className="relative pl-6">
                {/* Timeline Icon */}
                <span className={`absolute left-[-13px] top-1 h-6 w-6 rounded-full flex items-center justify-center ${iconBg} ring-4 ring-white`}>
                  <ActionIcon size={12} className={iconColor} />
                </span>
                
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-bold text-slate-900 capitalize">{log.action.replace('_', ' ').toLowerCase()}</span>
                    <span className="text-xs font-medium text-slate-500">{timeStr}</span>
                  </div>
                  
                  {log.action === 'STATUS_UPDATE' && (
                    <div className="text-sm text-slate-600 mt-1">
                      Status changed from <span className="font-semibold text-slate-800">{log.previous_status || 'Unknown'}</span> to <span className="font-semibold text-blue-600">{log.new_status}</span>
                    </div>
                  )}

                  {log.action === 'INVESTIGATOR_NOTE' && log.details && (
                    <div className="text-sm text-slate-700 mt-1 bg-amber-50 p-3 rounded-lg border border-amber-100 italic">
                      "{log.details}"
                    </div>
                  )}

                  {log.action === 'ALERT_CREATED' && (
                    <div className="text-sm text-slate-600 mt-1">
                      Automated ML withdrawal candidate flagged by prediction engine.
                    </div>
                  )}

                  <div className="text-xs font-medium text-slate-400 mt-2 uppercase tracking-wide">
                    Operator: {log.actor_id}
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
