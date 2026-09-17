import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { 
  getComplaint, 
  getComplaintTransactions, 
  getStoredPrediction 
} from '../api/client';
import { formatProbability } from '../utils/probability';
import { ArrowLeft, FileText, Database, Network, Map, Cpu } from 'lucide-react';
import { RiskHeatmap } from '../components/RiskHeatmap';

export const ComplaintDetails: React.FC = () => {
  const { complaintId } = useParams<{ complaintId: string }>();
  const navigate = useNavigate();
  
  const [complaint, setComplaint] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [prediction, setPrediction] = useState<any>(null);
  
  const [activeTab, setActiveTab] = useState('OVERVIEW');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!complaintId) return;

    const loadData = async () => {
      try {
        setLoading(true);
        const comp = await getComplaint(complaintId);
        setComplaint(comp);

        try {
          const txs = await getComplaintTransactions(complaintId);
          setTransactions(Array.isArray(txs) ? txs : []);
        } catch (e) {
          console.error("No transactions", e);
        }

        try {
          const pred = await getStoredPrediction(complaintId);
          setPrediction(pred);
        } catch (e) {
          console.error("No predictions", e);
        }
      } catch (err) {
        console.error("Failed to load complaint details", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [complaintId]);

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
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500 font-medium animate-pulse">Loading intelligence for {complaintId}...</div>
        </div>
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
        
        {activeTab === 'OVERVIEW' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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
        )}

        {activeTab === 'TRANSACTIONS' && (
          <div>
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
        )}

        {activeTab === 'NETWORK' && (
          <div>
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
        )}

        {activeTab === 'GEOGRAPHY' && (
          <div className="h-[550px]">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Predictive Withdrawal Heatmap</h3>
            <RiskHeatmap complaintId={cId} />
          </div>
        )}

        {activeTab === 'PREDICTION' && (
          <div>
            {prediction && prediction.ranked_candidates && prediction.ranked_candidates.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-slate-900 mb-4">
                  Top Cash Withdrawal Location Predictions ({prediction.ranked_candidates.length} candidates)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {prediction.ranked_candidates.slice(0, 10).map((cand: any, idx: number) => (
                    <div key={idx} className="border border-slate-200 rounded-lg p-4 bg-slate-50 flex justify-between items-center">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                            #{cand.rank || idx + 1}
                          </span>
                          <p className="font-semibold text-slate-900">{cand.location_name || cand.location_id}</p>
                        </div>
                        <p className="text-sm text-slate-500 mt-1">{cand.district}</p>
                        {cand.priority && (
                          <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs font-bold ${cand.priority === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                            {cand.priority} PRIORITY
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        <span className="text-2xl font-bold text-blue-600">{formatProbability(cand.probability)}</span>
                        <p className="text-xs text-slate-400 mt-1">Probability</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                <Cpu size={48} className="text-slate-300 mb-4" />
                <p className="font-medium text-slate-700">No ML prediction has been run for this complaint yet.</p>
                <p className="text-sm text-slate-400 mt-1">Predictions are generated automatically by the background risk engine.</p>
              </div>
            )}
          </div>
        )}

      </div>
    </MainLayout>
  );
};

