import React, { useState } from 'react';
import { 
  Home, 
  Mail, 
  Search, 
  ThumbsUp, 
  BarChart3, 
  Settings, 
  MoreHorizontal,
  UserCheck,
  Shield,
  LogOut
} from 'lucide-react';

export default function Sidebar({ currentTab, setCurrentTab }) {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const navItems = [
    { id: 'home', label: 'Home', emoji: '🏠' },
    { id: 'check', label: 'Check Email', emoji: '📧' },
    { id: 'result', label: 'Prediction Result', emoji: '🔍' },
    { id: 'feedback', label: 'Feedback', emoji: '👍' },
    { id: 'admin', label: 'Admin Dashboard', emoji: '📊', badge: 8 },
    { id: 'monitoring', label: 'Model / Monitoring', emoji: '⚙️' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200/80 flex flex-col justify-between shrink-0 min-h-screen select-none">
      <div>
        {/* Brand Header */}
        <div 
          onClick={() => setCurrentTab('home')}
          className="flex items-center gap-3 px-6 py-5 border-b border-slate-100 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-xl bg-[#5b5bf7] flex items-center justify-center text-white font-bold text-xl shadow-xs shadow-indigo-300">
            M
          </div>
          <div>
            <h1 className="font-bold text-slate-900 text-base tracking-tight leading-none">MailGuard</h1>
            <p className="text-xs text-slate-400 mt-1 font-medium">Spam intelligence</p>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="px-4 py-6">
          <p className="text-[11px] font-bold text-slate-400 tracking-wider px-3 mb-3">WORKSPACE</p>
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-[#eef2ff] text-[#4f46e5] font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-base">{item.emoji}</span>
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="w-5 h-5 rounded-full bg-rose-100 text-rose-600 text-xs font-bold flex items-center justify-center">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom Area */}
      <div className="p-4 space-y-3 relative">
        {/* System Protected Card */}
        <div 
          onClick={() => setCurrentTab('monitoring')}
          className="bg-[#070b19] p-3.5 rounded-2xl text-white shadow-sm border border-slate-800/40 cursor-pointer hover:border-slate-700 transition"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-semibold text-emerald-400">System protected</span>
          </div>
          <p className="text-[11px] text-slate-400 font-normal leading-tight">
            Model v3.8.2 is running normally.
          </p>
        </div>

        {/* User Profile */}
        <div className="flex items-center justify-between px-2 py-2 pt-2 border-t border-slate-100 relative">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-100 text-[#4f46e5] font-bold text-xs flex items-center justify-center">
              AD
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800 leading-none">Alex Doe</p>
              <p className="text-[11px] text-slate-400 mt-1 leading-none font-medium">Administrator</p>
            </div>
          </div>
          <button 
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-50 transition"
          >
            <MoreHorizontal size={16} />
          </button>

          {/* User Popup Menu */}
          {showUserMenu && (
            <div className="absolute bottom-14 right-2 w-48 bg-white rounded-2xl shadow-xl border border-slate-200/80 p-2 z-40 text-xs animate-fadeIn">
              <div className="px-3 py-2 border-b border-slate-100 mb-1">
                <p className="font-bold text-slate-900">Alex Doe</p>
                <p className="text-[10px] text-slate-400">Security Lead</p>
              </div>
              <button 
                onClick={() => { setCurrentTab('admin'); setShowUserMenu(false); }}
                className="w-full text-left px-3 py-2 rounded-xl text-slate-600 hover:bg-slate-50 flex items-center gap-2"
              >
                <Shield size={13} />
                <span>Admin Console</span>
              </button>
              <button 
                onClick={() => { setCurrentTab('monitoring'); setShowUserMenu(false); }}
                className="w-full text-left px-3 py-2 rounded-xl text-slate-600 hover:bg-slate-50 flex items-center gap-2"
              >
                <UserCheck size={13} />
                <span>System Health</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
