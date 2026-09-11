import React from 'react';
import { Sidebar } from './Sidebar';
import { ShieldAlert } from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-inter">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full relative overflow-hidden">
        
        {/* Synthetic Data Disclaimer Banner */}
        <div className="bg-amber-50 border-b border-amber-200 text-center py-2 px-4 z-50 flex items-center justify-center gap-3">
          <ShieldAlert size={16} className="text-amber-600" />
          <span className="text-xs font-semibold text-amber-800 uppercase tracking-wide">
            SYNTHETIC PROTOTYPE DATA — Predictions represent probabilistic investigative leads and do not establish criminal responsibility.
          </span>
        </div>

        {/* Dynamic Page Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {children}
        </div>
      </main>
    </div>
  );
};
