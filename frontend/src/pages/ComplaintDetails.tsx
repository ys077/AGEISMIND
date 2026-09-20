import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { useAppStore } from '../store/appDataStore';
import { formatProbability } from '../utils/probability';
import { ArrowLeft, FileText, Database, Network, Map, Cpu, Loader2 } from 'lucide-react';
import { RiskHeatmap } from '../components/RiskHeatmap';

const LoadingScreen = ({ complaintId }: { complaintId: string }) => {
  return (
    <div className="flex flex-col items-center justify-center h-[70vh]">
      <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-6" />
      <div className="text-xl font-bold text-slate-900 mb-3">
        Loading Intelligence for {complaintId}
      </div>
      <div className="text-sm font-medium text-slate-500 animate-pulse h-6">
        Retrieving core database records...
      </div>
    </div>
  );
};

const InvestigationPipeline = ({ complaint, transactions, prediction }: any) => {
  const steps = [
    { id: 'complaint', label: 'Complaint', status: complaint ? 'COMPLETED' : 'PENDING' },
    { id: 'transactions', label: 'Transactions', status: transactions && transactions.length > 0 ? 'COMPLETED' : (transactions ? 'NO DATA' : 'PENDING') },
    { id: 'network', label: 'Network', status: transactions && transactions.length > 0 ? 'COMPLETED' : 'PENDING' },
    { id: 'geography', label: 'Time & Geography', status: transactions && transactions.length > 0 ? 'COMPLETED' : 'PENDING' },
    { id: 'prediction', label: 'ML Prediction', status: prediction ? 'COMPLETED' : 'PENDING' },
    { id: 'risk', label: 'Risk Classification', status: prediction ? 'COMPLETED' : 'PENDING' },
    { id: 'shap', label: 'SHAP', status: prediction ? 'COMPLETED' : 'PENDING' },
    { id: 'heatmap', label: 'Heatmap', status: prediction ? 'COMPLETED' : 'PENDING' }
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-5 mb-6">
      <h3 className="text-sm font-bold text-slate-800 mb-4 uppercase tracking-wider">Investigation Pipeline</h3>
      <div className="flex items-center justify-between overflow-x-auto pb-2">
        {steps.map((step, idx) => (
          <div key={step.id} className="flex items-center">
            <div className="flex flex-col items-center gap-2">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2
                ${step.status === 'COMPLETED' ? 'bg-emerald-500 border-emerald-500 text-white' : 
                  step.status === 'NO DATA' ? 'bg-slate-200 border-slate-300 text-slate-500' :
                  'bg-white border-slate-300 text-slate-300'}`}
              >
                {step.status === 'COMPLETED' ? '✓' : (step.status === 'NO DATA' ? '!' : '○')}
              </div>
              <span className={`text-[10px] font-semibold uppercase text-center w-20 leading-tight
                ${step.status === 'COMPLETED' ? 'text-slate-800' : 'text-slate-400'}`}>
                {step.label}
              </span>
            </div>
            {idx < steps.length - 1 && (
              <div className={`w-8 h-0.5 mx-2 -mt-6
                ${step.status === 'COMPLETED' ? 'bg-emerald-500' : 'bg-slate-200'}`}></div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export const ComplaintDetails: React.FC = () => {
  const { complaintId } = useParams<{ complaintId: string }>();
  const navigate = useNavigate();
  
  const [complaint, setComplaint] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [prediction, setPrediction] = useState<any>(null);
  
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [loading, setLoading] = useState(true);
  const [predictionJobId, setPredictionJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);

  const [isStartingEngine, setIsStartingEngine] = useState(false);

  const { fetchCaseComplete } = useAppStore();

  useEffect(() => {
    let intervalId: any;
    if (predictionJobId && jobStatus?.status !== 'COMPLETED' && jobStatus?.status !== 'FAILED') {
      intervalId = setInterval(async () => {
        try {
          const { getPredictionJobStatus } = await import('../api/client');
          const status = await getPredictionJobStatus(predictionJobId);
          setJobStatus(status);
          
          if (status.status === 'COMPLETED' || status.status === 'FAILED') {
            clearInterval(intervalId);
            // Fetch fresh predictions directly from the backend bypassing cache
            if (status.status === 'COMPLETED' && complaintId) {
              const { getStoredPrediction } = await import('../api/client');
              const pred = await getStoredPrediction(complaintId);
              setPrediction(pred);
            }
          }
        } catch (err) {
          console.error("Failed to poll prediction job status", err);
        }
      }, 300);
    }
    return () => clearInterval(intervalId);
  }, [predictionJobId, jobStatus, complaintId, fetchCaseComplete]);

  useEffect(() => {
    if (!complaintId) return;

    const loadData = async () => {
      try {
        setLoading(true);
        const fullCase = await fetchCaseComplete(complaintId);
        setComplaint(fullCase.complaint);
        setTransactions(fullCase.transactions || []);
        
        // Unblock the main UI immediately
        setLoading(false);
        
        // We purposefully do NOT auto-load predictions here so that 
        // the user can experience the live Intelligence processing flow
        // by clicking "Run Predictive Engine" for ANY complaint they open.
        setPrediction(null);
      } catch (err) {
        console.error("Failed to load complaint details", err);
        setLoading(false);
      }
    };

    loadData();
  }, [complaintId, fetchCaseComplete]);

  const tabs = [
    { id: 'OVERVIEW', label: 'Overview', icon: FileText },
    { id: 'TRANSACTIONS', label: 'Transactions', icon: Database },
    { id: 'NETWORK', label: 'Network Graph', icon: Network },
    { id: 'GEOGRAPHY', label: 'Geography & Heatmap', icon: Map },
    { id: 'PREDICTION', label: 'AI Prediction', icon: Cpu },
  ];

  if (loading) {
    return (
      <MainLayout>
        <LoadingScreen complaintId={complaintId || 'Unknown'} />
      </MainLayout>
    );
  }

  if (!complaint) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center h-64">
          <div className="text-red-500 font-semibold text-lg mb-2">Complaint not found</div>
          <p className="text-slate-500 text-sm mb-4">Could not load details for complaint ID: {complaintId}</p>
          <button 
            onClick={() => navigate('/complaints')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Back to Complaints Registry
          </button>
        </div>
      </MainLayout>
    );
  }

  const cId = complaint.complaint_id || complaint.id || complaintId || 'N/A';
  const cCategory = complaint.crime_category || complaint.category || 'Cyber Fraud';
  const cSubCategory = complaint.fraud_type || complaint.sub_category || 'Unauthorized Transfer';
  const cAmount = complaint.fraud_amount ?? complaint.amount_lost ?? 0;
  const cDate = complaint.complaint_date || complaint.report_date || complaint.created_at;
  const cStatus = complaint.status || 'PENDING REVIEW';

  return (
    <MainLayout>
      <div className="mb-6">
        <button 
          onClick={() => navigate('/complaints')}
          className="flex items-center gap-1 text-sm text-slate-500 hover:text-blue-600 mb-4 transition-colors font-medium"
        >
          <ArrowLeft size={16} /> Back to Registry
        </button>

        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-900">Complaint #{cId}</h2>
              <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${cStatus === 'Resolved' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' : 'bg-amber-100 text-amber-800 border border-amber-200'}`}>
                {cStatus.toUpperCase()}
              </span>
            </div>
            <p className="text-slate-500 text-sm mt-1">{cCategory} &gt; {cSubCategory}</p>
          </div>

          <div className="text-right">
            <p className="text-sm text-slate-500 mb-1">Total Fraud Amount</p>
            <p className="text-2xl font-bold text-slate-900">₹{Number(cAmount).toLocaleString()}</p>
          </div>
        </div>
      </div>

      <InvestigationPipeline complaint={complaint} transactions={transactions} prediction={prediction} />

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 py-4 px-1 border-b-2 text-sm font-medium transition-colors
                ${activeTab === tab.id 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }
              `}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content Area */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 min-h-[500px]">
        
        <div className={activeTab === 'OVERVIEW' ? "grid grid-cols-1 md:grid-cols-2 gap-8" : "hidden"}>
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Case Summary</h3>
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
                {complaint.description || `Cybercrime incident reported under ${cCategory} (${cSubCategory}). Fraudulent transactions recorded total ₹${Number(cAmount).toLocaleString()}.`}
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Key Details</h3>
              <div className="space-y-4">
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-sm text-slate-500">Report Date</span>
                  <span className="text-sm font-medium text-slate-900">{cDate ? new Date(cDate).toLocaleDateString() : 'N/A'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-sm text-slate-500">Victim City</span>
                  <span className="text-sm font-medium text-slate-900">{complaint.victim_city || 'Tamil Nadu'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-sm text-slate-500">Source Channel</span>
                  <span className="text-sm font-medium text-slate-900">{complaint.source_channel || 'NCCP Portal'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-100 pb-2">
                  <span className="text-sm text-slate-500">District ID</span>
                  <span className="text-sm font-mono text-slate-900">{complaint.district_id || 'TN_DIST'}</span>
                </div>
              </div>
            </div>
          </div>

        <div className={activeTab === 'TRANSACTIONS' ? "block" : "hidden"}>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Transaction History ({transactions.length})</h3>
            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                    <th className="px-4 py-3">Txn ID</th>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Sender Account</th>
                    <th className="px-4 py-3">Receiver Account</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.map((tx: any, index: number) => {
                    const txId = tx.transaction_id || tx.id || `TX_${index}`;
                    const txTime = tx.transaction_time || tx.timestamp;
                    const sender = tx.sender_account || tx.source_account_id || 'N/A';
                    const receiver = tx.receiver_account || tx.destination_account_id || 'N/A';
                    const amt = tx.amount ?? 0;
                    return (
                      <tr key={txId} className="hover:bg-slate-50">
                        <td className="px-4 py-3 text-sm font-mono text-slate-500">{String(txId).substring(0, 12)}</td>
                        <td className="px-4 py-3 text-sm text-slate-700">{txTime ? new Date(txTime).toLocaleString() : 'N/A'}</td>
                        <td className="px-4 py-3 text-sm font-mono text-blue-600">{sender}</td>
                        <td className="px-4 py-3 text-sm font-mono text-blue-600">{receiver}</td>
                        <td className="px-4 py-3 text-sm text-slate-600">{tx.transaction_type || 'IMPS'}</td>
                        <td className="px-4 py-3 text-sm font-medium text-slate-900 text-right">₹{Number(amt).toLocaleString()}</td>
                      </tr>
                    );
                  })}
                  {transactions.length === 0 && (
                    <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No transactions recorded for this complaint.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        <div className={activeTab === 'NETWORK' ? "block" : "hidden"}>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Fraud Network Flow</h3>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 flex flex-col items-center justify-center min-h-[350px]">
              <Network size={48} className="text-blue-500 mb-4 animate-bounce" />
              <h4 className="text-base font-semibold text-slate-800 mb-1">Mule Account Network</h4>
              <p className="text-sm text-slate-500 text-center max-w-md mb-4">
                Network visualization connects sender accounts to receiver layer-1 and layer-2 mule accounts.
              </p>
              <div className="w-full max-w-lg space-y-2">
                {transactions.slice(0, 5).map((tx, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-white border border-slate-200 p-3 rounded text-sm">
                    <span className="font-mono text-blue-600">{tx.sender_account || tx.source_account_id}</span>
                    <span className="text-slate-400">➔ ₹{Number(tx.amount || 0).toLocaleString()} ➔</span>
                    <span className="font-mono text-emerald-600">{tx.receiver_account || tx.destination_account_id}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        <div className={activeTab === 'GEOGRAPHY' ? "block" : "hidden"}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-slate-900">Predictive Withdrawal Heatmap</h3>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-3 h-[550px]">
                <RiskHeatmap key={prediction ? 'has-pred' : 'no-pred'} mode="complaint" complaintId={complaintId} />
              </div>
              <div className="lg:col-span-1 space-y-4">
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                  <h4 className="text-sm font-bold text-slate-800 mb-1 uppercase tracking-wider">Top Predicted Withdrawal Locations</h4>
                  <p className="text-xs text-slate-500 mb-4">Model-ranked candidate withdrawal locations</p>
                  
                  {prediction?.ranked_candidates && prediction.ranked_candidates.length > 0 ? (
                    <div className="space-y-3">
                      {prediction.ranked_candidates.slice(0, 3).map((cand: any, idx: number) => (
                        <div key={idx} className="bg-white border border-slate-200 rounded p-3 relative overflow-hidden">
                          <div className={`absolute left-0 top-0 bottom-0 w-1 ${cand.priority === 'CRITICAL' ? 'bg-red-500' : cand.priority === 'HIGH' ? 'bg-orange-500' : cand.priority === 'MEDIUM' ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>
                          <div className="pl-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-bold text-slate-700">#{cand.rank || idx + 1} {cand.location_name || cand.location_id}</span>
                              <span className="text-xs font-bold text-slate-900">{formatProbability(cand.probability)}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] text-slate-500">{cand.district}</span>
                              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${cand.priority === 'CRITICAL' ? 'bg-red-100 text-red-700' : cand.priority === 'HIGH' ? 'bg-orange-100 text-orange-700' : cand.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                                {cand.priority}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500 text-center py-4">No predictions available</div>
                  )}
                </div>
              </div>
            </div>
          </div>

        <div className={activeTab === 'PREDICTION' ? "block" : "hidden"}>
            {prediction && prediction.ranked_candidates && prediction.ranked_candidates.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  {prediction.candidate_count ? prediction.candidate_count.toLocaleString() : prediction.ranked_candidates.length.toLocaleString()} candidate locations evaluated
                </h3>
                <p className="text-sm text-slate-600 mb-4">Top 10 predicted withdrawal locations</p>
                
                {prediction.ranked_candidates[0]?.probability < 0.01 && (
                  <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg mb-6 shadow-sm">
                    <h4 className="font-bold text-amber-800 text-sm mb-1 uppercase">Low Predictive Signal</h4>
                    <p className="text-sm text-amber-700">All currently scored candidates have low model probability. The locations below are ranked relative to this complaint and should be treated as investigative leads rather than confirmed withdrawal locations.</p>
                  </div>
                )}
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {prediction.ranked_candidates.map((cand: any, idx: number) => (
                    <div key={idx} className="flex flex-col mb-4">
                      <div className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex justify-between items-center shadow-sm">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                            #{cand.rank || idx + 1}
                          </span>
                          <p className="font-semibold text-slate-900">{cand.location_name || cand.location_id}</p>
                        </div>
                        <p className="text-sm text-slate-500 mt-1">District: {cand.district}</p>
                        {cand.priority && (
                          <span className={`inline-block mt-2 px-2 py-0.5 rounded text-[10px] font-bold ${
                            cand.priority === 'CRITICAL' ? 'bg-purple-100 text-purple-700' :
                            cand.priority === 'HIGH' ? 'bg-red-100 text-red-700' : 
                            cand.priority === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                            'bg-emerald-100 text-emerald-700'
                          }`}>
                            {cand.priority} PRIORITY
                          </span>
                        )}
                        <span className="inline-block mt-2 ml-2 px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">
                          {cand.model_version || prediction.model_version || 'v1'}
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-2xl font-bold text-slate-800">{formatProbability(cand.probability)}</span>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase font-semibold">Model Probability</p>
                      </div>
                    </div>
                    {cand.factors && cand.factors.length > 0 && (
                      <div className="bg-white border border-slate-200 border-t-0 rounded-b-lg p-3 grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[10px] font-bold text-emerald-700 uppercase mb-1">Top Positive Factors</p>
                          <ul className="text-xs text-slate-600 space-y-1">
                            {cand.factors.filter((f: any) => f.direction === 'POSITIVE' || f.contribution > 0).slice(0, 3).map((f: any, i: number) => (
                              <li key={i} className="flex justify-between border-b border-slate-50 pb-0.5">
                                <span>{f.factor_name}</span>
                                <span className="text-emerald-600 font-mono">+{Number(f.contribution).toFixed(3)}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-rose-700 uppercase mb-1">Top Negative Factors</p>
                          <ul className="text-xs text-slate-600 space-y-1">
                            {cand.factors.filter((f: any) => f.direction === 'NEGATIVE' || f.contribution < 0).slice(0, 3).map((f: any, i: number) => (
                              <li key={i} className="flex justify-between border-b border-slate-50 pb-0.5">
                                <span>{f.factor_name}</span>
                                <span className="text-rose-600 font-mono">{Number(f.contribution).toFixed(3)}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
                
              </div>
            ) : (
              predictionJobId ? (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-6">
                  <div className="flex items-center gap-3 mb-6 border-b border-slate-200 pb-4">
                    <Cpu size={24} className="text-blue-600 animate-pulse" />
                    <h3 className="text-lg font-bold text-slate-900">PREDICTIVE ENGINE</h3>
                    <span className="ml-auto px-3 py-1 bg-blue-100 text-blue-800 text-xs font-bold rounded-full">
                      {jobStatus?.status || 'INITIALIZING'}
                    </span>
                  </div>
                  
                  <div className="space-y-4">
                    {["INITIALIZING", "LOADING_FEATURES", "TRANSACTION_FEATURES", "NETWORK_FEATURES", "GEOGRAPHIC_FEATURES", "ML_MODEL_EVALUATION", "SHAP_EXPLANATION", "RISK_CLASSIFICATION", "PERSISTING_PREDICTIONS"].map((stage, idx) => {
                      const isCompleted = jobStatus?.completed_stages?.includes(stage);
                      const isCurrent = jobStatus?.stage === stage;
                      const isPending = !isCompleted && !isCurrent;
                      
                      if (isPending && idx > (jobStatus?.completed_stages?.length || 0) + 1) return null; // hide far future stages
                      
                      return (
                        <div key={stage} className={`flex items-center gap-3 ${isPending ? 'opacity-40' : 'opacity-100'}`}>
                          <div className={`w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-bold ${
                            isCompleted ? 'bg-emerald-500 text-white' : 
                            isCurrent ? 'bg-blue-500 text-white animate-pulse' : 
                            'border border-slate-300 text-slate-300'
                          }`}>
                            {isCompleted ? '✓' : idx + 1}
                          </div>
                          <span className={`text-sm font-mono ${isCompleted ? 'text-slate-700' : isCurrent ? 'text-blue-700 font-bold' : 'text-slate-400'}`}>
                            {stage.replace(/_/g, ' ')}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-slate-500 border border-slate-200 border-dashed rounded-lg bg-slate-50">
                  <Cpu size={48} className="text-slate-300 mb-4" />
                  <p className="font-medium text-slate-700">Prediction Pending</p>
                  <p className="text-sm text-slate-400 mt-1 mb-4">No prediction has been executed for this complaint.</p>
                  <button
                    onClick={async () => {
                      try {
                        setIsStartingEngine(true);
                        const { runPredictionJob } = await import('../api/client');
                        const res = await runPredictionJob(complaintId!);
                        setPredictionJobId(res.job_id);
                        setJobStatus(res);
                      } catch (err) {
                        console.error("Failed to start prediction", err);
                        alert("Failed to start predictive engine.");
                      } finally {
                        setIsStartingEngine(false);
                      }
                    }}
                    disabled={isStartingEngine}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold shadow-sm transition-colors ${
                      isStartingEngine 
                        ? 'bg-blue-400 text-white cursor-not-allowed' 
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {isStartingEngine ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Initializing Engine...
                      </>
                    ) : (
                      <>
                        <Cpu size={18} /> Run Predictive Engine
                      </>
                    )}
                  </button>
                </div>
              )
            )}
          </div>
      </div>
    </MainLayout>
  );
};

