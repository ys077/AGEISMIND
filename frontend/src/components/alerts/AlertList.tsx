import React from 'react';
import { Clock, ShieldAlert } from 'lucide-react';

export interface AlertDetail {
  alert_id: string;
  prediction_id: string;
  complaint_id: string;
  district: string;
  priority: string;
  probability: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AlertListProps {
  alerts: AlertDetail[];
  onSelectAlert: (alert_id: string) => void;
  selectedAlertId?: string;
  loading?: boolean;
}

export const AlertList: React.FC<AlertListProps> = ({ alerts, onSelectAlert, selectedAlertId, loading }) => {
  if (loading) {
    return <div className="p-6 text-sm text-slate-500 animate-pulse text-center">Loading incoming alerts...</div>;
  }

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-200 px-4 py-4 sticky top-0 z-10 flex justify-between items-center">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Priority Alerts</h3>
          <p className="text-xs text-slate-500">Live Prediction Telemetry</p>
        </div>
        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold">
          {alerts.length}
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {alerts.length === 0 ? (
          <div className="p-8 text-sm text-slate-500 text-center flex flex-col items-center">
            <ShieldAlert className="text-slate-300 mb-2" size={24} />
            No active alerts detected.
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {alerts.map((alert) => {
              const isSelected = alert.alert_id === selectedAlertId;
              const isHigh = alert.priority === 'HIGH';
              const isMedium = alert.priority === 'MEDIUM';
              
              return (
                <li 
                  key={alert.alert_id} 
                  className={`cursor-pointer transition-all ${
                    isSelected ? 'bg-blue-50 border-l-4 border-l-blue-600' : 'hover:bg-slate-50 border-l-4 border-l-transparent'
                  }`}
                  onClick={() => onSelectAlert(alert.alert_id)}
                >
                  <div className="px-4 py-4 flex flex-col gap-3">
                    <div className="flex justify-between items-start">
                      <span className="font-semibold text-sm text-slate-900 truncate pr-2">#{alert.complaint_id.substring(0, 8)}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase whitespace-nowrap ${
                        isHigh ? 'text-red-700 bg-red-100 border border-red-200' : 
                        isMedium ? 'text-amber-700 bg-amber-100 border border-amber-200' : 
                        'text-blue-700 bg-blue-100 border border-blue-200'
                      }`}>
                        {alert.priority}
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-end">
                      <div className="flex flex-col">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Location Target</span>
                        <span className="text-xs font-medium text-slate-700 truncate max-w-[140px]">{alert.district}</span>
                      </div>
                      <div className="flex flex-col text-right">
                        <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Confidence</span>
                        <span className={`text-sm font-bold ${isHigh ? 'text-red-600' : 'text-blue-600'}`}>
                          {(alert.probability * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <div className="flex justify-between items-center mt-1 border-t border-slate-100 pt-2">
                      <span className="flex items-center gap-1 text-[10px] text-slate-500 font-medium">
                        <Clock size={10} /> 
                        {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      <span className="text-[10px] font-bold text-slate-600 uppercase tracking-wide bg-slate-100 px-1.5 py-0.5 rounded">
                        {alert.status}
                      </span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
};
