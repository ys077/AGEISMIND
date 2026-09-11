import React, { useState } from 'react';
import { updateAlertStatus, addInvestigatorAction } from '../../api/client';
import { AlertTriangle, Send } from 'lucide-react';

export const InvestigatorActionPanel: React.FC<{ 
  alertId: string, 
  currentStatus: string,
  onActionComplete: () => void 
}> = ({ alertId, currentStatus, onActionComplete }) => {
  const [status, setStatus] = useState<string>(currentStatus);
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStatusChange = async (newStatus: string) => {
    setLoading(true);
    setError(null);
    try {
      await updateAlertStatus(alertId, newStatus);
      setStatus(newStatus);
      onActionComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to update status");
    } finally {
      setLoading(false);
    }
  };

  const handleAddNotes = async () => {
    if (!notes.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await addInvestigatorAction(alertId, { action_type: 'INVESTIGATOR_NOTE', notes });
      setNotes('');
      onActionComplete();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save note");
    } finally {
      setLoading(false);
    }
  };

  const statusOptions = ["NEW", "ACKNOWLEDGED", "IN_REVIEW", "ACTION_TAKEN", "CLOSED"];

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 flex flex-col gap-5">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 text-sm p-3 rounded-md flex items-center gap-2">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* Status Control */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-2">Update Operational Status</label>
        <div className="flex flex-wrap gap-2">
          {statusOptions.map(s => (
            <button
              key={s}
              onClick={() => handleStatusChange(s)}
              disabled={loading || status === s}
              className={`px-3 py-1.5 rounded-md text-xs font-bold tracking-wide transition-colors ${
                status === s 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'bg-white text-slate-600 border border-slate-300 hover:border-blue-400 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed'
              }`}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Notes Control */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-2">Add Investigation Note</label>
        <div className="relative">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            disabled={loading}
            placeholder="Type your notes or actions taken here..."
            className="w-full bg-white border border-slate-300 rounded-md text-sm text-slate-900 p-3 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 min-h-[100px] resize-y"
          />
          <div className="flex justify-end mt-3">
            <button
              onClick={handleAddNotes}
              disabled={loading || !notes.trim()}
              className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={14} />
              {loading ? 'Saving...' : 'Add Note'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
