import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '../components/layout/MainLayout';
import { getComplaints } from '../api/client';
import { useAppStore } from '../store/appDataStore';
import { Search, Filter, FileText, ChevronRight, X } from 'lucide-react';

const PAGE_SIZE = 50;

export const ComplaintsList: React.FC = () => {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [showFilters, setShowFilters] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const complaintsList = useAppStore(state => state.complaintsList);
  const dashboardData = useAppStore(state => state.dashboardData);
  const ensureComplaints = useAppStore(state => state.ensureComplaints);

  const hasActiveFilters = Boolean(searchQuery.trim()) || statusFilter !== 'ALL' || categoryFilter !== 'ALL';
  const activeFilterCount = (statusFilter !== 'ALL' ? 1 : 0) + (categoryFilter !== 'ALL' ? 1 : 0);

  const statusOptions = (Object.keys(dashboardData?.status_breakdown || {}).length
    ? Object.keys(dashboardData.status_breakdown)
    : ['Under Investigation', 'FIR Filed', 'Chargesheet Filed', 'Resolved', 'Pending Review']
  ).sort();
  const categoryOptions = (dashboardData?.categories_breakdown || [])
    .map((c: any) => c.category)
    .filter(Boolean);

  useEffect(() => {
    ensureComplaints();
  }, [ensureComplaints]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setSearchQuery(searchInput.trim());
      setPage(1);
    }, 250);
    return () => window.clearTimeout(handle);
  }, [searchInput]);

  useEffect(() => {
    if (!hasActiveFilters && page === 1 && complaintsList?.items) {
      setResult(complaintsList);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    getComplaints(page, PAGE_SIZE, {
      q: searchQuery || undefined,
      status: statusFilter !== 'ALL' ? statusFilter : undefined,
      category: categoryFilter !== 'ALL' ? categoryFilter : undefined,
    })
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page, searchQuery, statusFilter, categoryFilter, hasActiveFilters, complaintsList]);

  const complaints = result?.items || [];
  const total = result?.total || 0;
  const totalPages = result?.total_pages || 1;

  const clearFilters = () => {
    setSearchInput('');
    setSearchQuery('');
    setStatusFilter('ALL');
    setCategoryFilter('ALL');
    setPage(1);
  };

  return (
    <MainLayout>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:justify-between lg:items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Complaints Registry</h2>
          <p className="text-slate-500 text-sm mt-1">Investigate registered cybercrime reports</p>
        </div>
        
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search ID or category..." 
              className="pl-9 pr-9 py-2 border border-slate-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => { setSearchInput(''); setSearchQuery(''); setPage(1); }}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={() => setShowFilters((open) => !open)}
            className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium ${
              showFilters || activeFilterCount > 0
                ? 'bg-blue-50 border-blue-300 text-blue-700'
                : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Filter size={16} />
            Filter
            {activeFilterCount > 0 && (
              <span className="min-w-[18px] h-[18px] px-1 rounded-full bg-blue-600 text-white text-[10px] flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="mb-4 bg-white border border-slate-200 rounded-lg p-3 shadow-sm flex flex-wrap items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white text-slate-700"
          >
            <option value="ALL">All statuses</option>
            {statusOptions.map((status) => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white text-slate-700"
          >
            <option value="ALL">All categories</option>
            {categoryOptions.map((category: string) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          {hasActiveFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear all
            </button>
          )}
        </div>
      )}

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
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    <div className="flex flex-col items-center">
                      <FileText className="text-slate-300 mb-2" size={32} />
                      <p>{hasActiveFilters ? 'No complaints match this search or filter.' : 'No complaints found in the registry.'}</p>
                    </div>
                  </td>
                </tr>
              ) : (
                complaints.map((c: any) => (
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
        
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 flex items-center justify-between">
          <span className="text-sm text-slate-500">
            Showing {total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1} to {Math.min(page * PAGE_SIZE, total)} of {total} entries
          </span>
          <div className="flex gap-2">
            <button 
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border border-slate-300 rounded text-sm bg-white text-slate-500 disabled:opacity-50 hover:bg-slate-50" 
            >
              Previous
            </button>
            <button 
              onClick={() => setPage((p) => p + 1)}
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
