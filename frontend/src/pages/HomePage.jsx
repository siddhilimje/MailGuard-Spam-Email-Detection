import React from 'react';
import { ArrowRight, ShieldCheck, Zap, Activity } from 'lucide-react';

export default function HomePage({ setCurrentTab }) {
  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-fadeIn">
      {/* Massive Dark Hero Banner */}
      <div className="bg-[#070b19] text-white rounded-3xl p-10 md:p-14 shadow-xl border border-slate-800/60 relative overflow-hidden">
        {/* Subtle decorative glow */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-[#5b5bf7]/10 blur-3xl pointer-events-none"></div>

        {/* Top Model Online Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/10 text-white/90 text-xs font-medium mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>AI model is online</span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight max-w-2xl leading-[1.15] mb-5">
          Know what's safe <br />
          before you click.
        </h1>

        {/* Subtext */}
        <p className="text-slate-300/90 text-base md:text-lg max-w-xl font-normal leading-relaxed mb-8">
          MailGuard analyzes suspicious messages in seconds and explains the signals behind every prediction.
        </p>

        {/* Action Row */}
        <div className="flex items-center gap-5 mb-14">
          <button
            onClick={() => setCurrentTab('check')}
            className="flex items-center gap-2 bg-[#5b5bf7] hover:bg-[#4f46e5] text-white font-semibold text-sm px-6 py-3.5 rounded-xl shadow-md shadow-indigo-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <span>Check an email</span>
            <ArrowRight size={16} />
          </button>

          <button
            onClick={() => setCurrentTab('monitoring')}
            className="text-slate-300 hover:text-white text-sm font-medium transition"
          >
            View model health
          </button>
        </div>

        {/* Bottom Hero Stats */}
        <div className="grid grid-cols-3 gap-6 pt-8 border-t border-white/10 max-w-lg">
          <div>
            <p className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">99.2%</p>
            <p className="text-xs text-slate-400 mt-1 font-medium">Accuracy</p>
          </div>
          <div>
            <p className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">1.2s</p>
            <p className="text-xs text-slate-400 mt-1 font-medium">Avg. scan</p>
          </div>
          <div>
            <p className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">24/7</p>
            <p className="text-xs text-slate-400 mt-1 font-medium">Protection</p>
          </div>
        </div>
      </div>
    </div>
  );
}

