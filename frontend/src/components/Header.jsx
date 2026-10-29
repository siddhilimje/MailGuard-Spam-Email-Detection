import React, { useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, ShieldCheck, X } from 'lucide-react';

const TAB_TITLES = {
  home: { emoji: '🏠', label: 'Home' },
  check: { emoji: '📧', label: 'Check Email' },
  result: { emoji: '🔍', label: 'Prediction Result' },
  feedback: { emoji: '👍', label: 'Feedback' },
  admin: { emoji: '📊', label: 'Admin Dashboard' },
  monitoring: { emoji: '⚙️', label: 'Model / Monitoring' }
};

export default function Header({ currentTab, setCurrentTab }) {
  const [showNotifications, setShowNotifications] = useState(false);
  const current = TAB_TITLES[currentTab] || TAB_TITLES.home;

  const notifications = [
    {
      id: 1,
      title: 'Review queue has 8 high priority items',
      time: 'Just now',
      type: 'warning',
      actionTab: 'feedback'
    },
    {
      id: 2,
      title: 'Model v3.8.2 latency target met (1.4s)',
      time: '25 min ago',
      type: 'success',
      actionTab: 'monitoring'
    },
    {
      id: 3,
      title: 'Threat intelligence feed degraded (retrying)',
      time: '1 hour ago',
      type: 'warning',
      actionTab: 'monitoring'
    }
  ];

  return (
    <header className="h-16 px-8 bg-white/80 backdrop-blur-md border-b border-slate-200/80 flex items-center justify-between sticky top-0 z-20">
      {/* Breadcrumb Title */}
      <div className="flex items-center gap-2 text-slate-800 font-semibold text-sm">
        <span className="text-base">{current.emoji}</span>
        <span>{current.label}</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 relative">
        {/* Live Protection Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-100/80 text-slate-700 text-xs font-semibold shadow-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Live protection</span>
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-9 h-9 rounded-full border border-slate-200/80 bg-white flex items-center justify-center text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition shadow-xs relative"
            title="Notifications"
          >
            <Bell size={15} />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-amber-500 ring-2 ring-white"></span>
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-200/80 p-4 z-40 animate-fadeIn">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <span className="text-xs font-bold text-slate-900">System Notifications</span>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="space-y-2.5">
                {notifications.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => {
                      if (setCurrentTab) setCurrentTab(n.actionTab);
                      setShowNotifications(false);
                    }}
                    className="w-full text-left p-2.5 rounded-xl bg-slate-50 hover:bg-indigo-50/60 transition flex items-start gap-2.5 group"
                  >
                    <span className="mt-0.5">
                      {n.type === 'warning' ? (
                        <AlertTriangle size={13} className="text-amber-500" />
                      ) : (
                        <CheckCircle2 size={13} className="text-emerald-500" />
                      )}
                    </span>
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-slate-800 group-hover:text-indigo-700 leading-tight">
                        {n.title}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-1">{n.time}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
