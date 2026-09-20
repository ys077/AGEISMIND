import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Activity, Shield, List } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Complaints', path: '/complaints', icon: FileText },
    { name: 'Alerts', path: '/alerts', icon: Shield },
    { name: 'Risk Map', path: '/heatmap', icon: Activity },
    { name: 'Audit Trail', path: '/audit', icon: List },
  ];

  return (
    <nav className="w-64 h-full bg-white border-r border-slate-200 flex flex-col shadow-sm flex-shrink-0">
      <div className="p-6 border-b border-slate-200">
        <h1 className="font-bold text-lg text-slate-900 flex items-center gap-2">
          <Shield className="text-blue-600" size={24} />
          <span>CYBER INTEL</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">Prediction & Analysis</p>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-3">
          {navItems.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`
                }
              >
                <item.icon size={18} />
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
};
