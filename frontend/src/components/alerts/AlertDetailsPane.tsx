import React, { useState, useEffect } from 'react';
import { getAlertDetail } from '../../api/client';
import { formatProbability } from '../../utils/probability';
import { InvestigatorActionPanel } from './InvestigatorActionPanel';
import { Map, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const AlertDetailsPane: React.FC<{
  alertId: string | null;
  onAlertUpdated: () => void;
  onViewMap: (complaintId: string) => void;
  onDetailLoaded?: (detail: any) => void;
}> = ({ alertId, onAlertUpdated, onViewMap, onDetailLoaded }) => {
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!alertId) {
      setDetail(null);
      return;
    }
    
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const data = await getAlertDetail(alertId);
        setDetail(data);
        setError(null);
        onDetailLoaded?.(data);
      } catch (err) {
        console.error(err);
        setError("Unable to retrieve alert details.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchDetail();
  }, [alertId]);

  if (!alertId) return (
    <div className="flex flex-col items-center justify-center h-full bg-slate-50 border border-slate-200 rounded-lg text-slate-500 text-sm">
      <AlertCircle className="text-slate-300 mb-2" size={32} />
      Select an alert from the list to view details
    </div>
  );
  
  if (loading) return (
    <div className="flex items-center justify-center h-full bg-white border border-slate-200 rounded-lg text-slate-500 text-sm animate-pulse">
      Loading dossier...
    </div>
  );

  if (error) return (
    <div className="flex items-center justify-center h-full bg-white border border-red-200 rounded-lg text-red-500 text-sm">
      {error}
    </div>
  );

  if (!detail) return null;

  const isHigh = detail.priority === 'HIGH';

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-lg shadow-sm overflow-y-auto custom-scrollbar">
      {/* Header */}
      <div className="bg-slate-50 border-b border-slate-200 p-6 flex justify-between items-start sticky top-0 z-10">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-3">
            Complaint #{detail.complaint_id.substring(0, 8)}
            <span className={`px-2.5 py-0.5 rounded text-xs font-bold tracking-wider uppercase ${
              isHigh ? 'text-red-700 bg-red-100 border border-red-200' : 
              'text-amber-700 bg-amber-100 border border-amber-200'
            }`}>
              {detail.priority} Priority
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-1 uppercase tracking-wide">Alert ID: {detail.alert_id}</p>
        </div>
        <button 
          onClick={() => onViewMap(detail.complaint_id)}
          className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-3 py-1.5 rounded text-sm font-medium hover:bg-slate-50 hover:text-blue-600 transition-colors"
        >
          <Map size={16} />
          View Map
        </button>
      </div>

      <div className="p-6 space-y-8">
        {/* Prediction Intelligence */}
        <section>
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">Prediction Intelligence</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">Target District</span>
              <span className="text-lg font-medium text-slate-900">{detail.district}</span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">Confidence Score</span>
              <span className={`text-2xl font-bold ${isHigh ? 'text-red-600' : 'text-blue-600'}`}>
                {formatProbability(detail.probability)}
              </span>
            </div>
          </div>
        </section>

        {/* Explainable AI */}
        <section>
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">SHAP Explainability Analysis</h3>
          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-5">
            
            <div>
              <h4 className="text-xs font-bold text-red-600 uppercase mb-3 flex items-center gap-2">
                <ArrowUpRight size={14} /> Risk Escalators
              </h4>
              <ul className="space-y-2.5">
                {detail.top_positive_factors?.slice(0, 3).map((f: any, i: number) => {
                  const val = f.contribution ?? f.shap_value ?? 0;
                  return (
                  <li key={i} className="text-sm text-slate-700 flex items-start gap-3 bg-red-50/50 p-2.5 rounded border-l-2 border-l-red-500">
                    <span className="text-red-600 font-bold min-w-[50px]">+{val.toFixed(3)}</span>
                    <span className="flex-1">{f.explanation_text || f.factor_name || f.feature_name} <span className="text-slate-400 text-xs ml-1">(Val: {f.feature_value})</span></span>
                  </li>
                )})}
              </ul>
            </div>

            {detail.top_negative_factors?.length > 0 && (
              <div className="pt-4 border-t border-slate-100">
                <h4 className="text-xs font-bold text-emerald-600 uppercase mb-3 flex items-center gap-2">
                  <ArrowDownRight size={14} /> Mitigating Factors
                </h4>
                <ul className="space-y-2.5">
                  {detail.top_negative_factors?.slice(0, 2).map((f: any, i: number) => {
                    const val = f.contribution ?? f.shap_value ?? 0;
                    return (
                    <li key={i} className="text-sm text-slate-700 flex items-start gap-3 bg-emerald-50/50 p-2.5 rounded border-l-2 border-l-emerald-500">
                      <span className="text-emerald-600 font-bold min-w-[50px]">{val.toFixed(3)}</span>
                      <span className="flex-1">{f.explanation_text || f.factor_name || f.feature_name} <span className="text-slate-400 text-xs ml-1">(Val: {f.feature_value})</span></span>
                    </li>
                  )})}
                </ul>
              </div>
            )}
          </div>
        </section>

        {/* Action Panel */}
        <section>
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-200 pb-2 mb-4">Investigator Actions</h3>
          <InvestigatorActionPanel 
            alertId={alertId} 
            currentStatus={detail.status} 
            onActionComplete={() => {
              onAlertUpdated();
              getAlertDetail(alertId).then(setDetail).catch(console.error);
            }} 
          />
        </section>
      </div>
    </div>
  );
};
