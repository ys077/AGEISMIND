import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { getComplaints } from '../api/client';
import { Search, Filter, FileText, ChevronRight } from 'lucide-react';

export const ComplaintsList: React.FC = () => {
  const [complaints, setComplaints] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchComplaints = async () => {
      setLoading(true);
      try {
        const data = await getComplaints(page, 50);
        if (data.items) {
          setComplaints(data.items);
          setTotal(data.total);
          setTotalPages(data.total_pages);
        } else {
          setComplaints(data);
          setTotal(data.length);
        }
      } catch (err) {
        console.error("Failed to fetch complaints", err);
      } finally {
        setLoading(false);
      }
    };
    fetchComplaints();
  }, [page]);

  const handleNext = () => {
    if (page < totalPages) setPage(page + 1);
  };

  const handlePrev = () => {
    if (page > 1) setPage(page - 1);
  };

  return (
    <MainLayout>
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Complaints Registry</h2>
          <p className="text-slate-500 text-sm mt-1">Investigate registered cybercrime reports</p>
        </div>
        
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Search ID or category..." 
              className="pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50">
            <Filter size={16} />
            Filter
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex flex-col h-[calc(100vh-180px)]">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">Category</th>
                <th className="px-6 py-4">Sub-Category</th>
                <th className="px-6 py-4 text-right">Amount Lost</th>
                <th className="px-6 py-4">Report Date</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">Loading complaints...</td>
                </tr>
              ) : complaints.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500 flex flex-col items-center">
                    <FileText className="text-slate-300 mb-2" size={32} />
                    <p>No complaints found in the registry.</p>
                  </td>
                </tr>
              ) : (
                complaints.map((c) => (
                  <tr 
                    key={c.complaint_id} 
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                  >
                    <td className="px-6 py-4 text-sm font-medium text-blue-600">#{c.complaint_id?.substring(0, 8)}</td>
                    <td className="px-6 py-4 text-sm text-slate-700">{c.crime_category}</td>
                    <td className="px-6 py-4 text-sm text-slate-500">{c.fraud_type}</td>
                    <td className="px-6 py-4 text-sm font-medium text-slate-900 text-right">
                      ₹{c.fraud_amount?.toLocaleString() || '0'}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {new Date(c.complaint_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.status === 'Resolved' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-slate-400">
                      <ChevronRight size={18} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination placeholder */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 flex items-center justify-between">
          <span className="text-sm text-slate-500">
            Showing {(page - 1) * 50 + 1} to {Math.min(page * 50, total)} of {total} entries
          </span>
          <div className="flex gap-2">
            <button 
              onClick={handlePrev}
              disabled={page === 1}
              className="px-3 py-1 border border-slate-300 rounded text-sm bg-white text-slate-500 disabled:opacity-50 hover:bg-slate-50" 
            >
              Previous
            </button>
            <button 
              onClick={handleNext}
              disabled={page >= totalPages}
              className="px-3 py-1 border border-slate-300 rounded text-sm bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};
