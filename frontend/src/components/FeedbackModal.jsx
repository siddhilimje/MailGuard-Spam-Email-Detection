import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, X, Check } from 'lucide-react';
import { submitFeedback } from '../api';

export default function FeedbackModal({ isOpen, onClose, scanData }) {
  if (!isOpen) return null;

  const [verdict, setVerdict] = useState(scanData?.is_spam ? 'spam' : 'legitimate');
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await submitFeedback({
      scan_id: scanData?.id || 'MG-10482',
      subject: scanData?.subject || 'Analyzed Email',
      user_verdict: verdict === 'spam' ? 'Spam' : 'Legitimate',
      model_verdict: scanData?.is_spam ? 'Spam' : 'Legitimate',
      comments: comment
    });
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-md w-full p-7 shadow-2xl border border-slate-200/80 relative">
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center text-xs font-bold transition"
        >
          <X size={14} />
        </button>

        {submitted ? (
          <div className="text-center py-8 space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
              <Check size={24} strokeWidth={3} />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Feedback Recorded!</h3>
            <p className="text-xs text-slate-500">
              Your contribution will be included in the active learning retraining cycle.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <p className="text-[11px] font-bold text-[#5b5bf7] uppercase tracking-wider mb-1">
                HUMAN-IN-THE-LOOP
              </p>
              <h3 className="text-xl font-bold text-slate-900">Share your feedback</h3>
              <p className="text-xs text-slate-500 mt-1">
                Help improve MailGuard by confirming or correcting the model's prediction.
              </p>
            </div>

            {/* Verdict Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">
                What is the actual label of this email?
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setVerdict('spam')}
                  className={`py-3 px-4 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-2 ${
                    verdict === 'spam'
                      ? 'bg-rose-50 border-rose-200 text-rose-700 ring-2 ring-rose-500/20'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <ThumbsDown size={14} />
                  <span>It is Spam</span>
                </button>

                <button
                  type="button"
                  onClick={() => setVerdict('legitimate')}
                  className={`py-3 px-4 rounded-xl text-xs font-bold border transition flex items-center justify-center gap-2 ${
                    verdict === 'legitimate'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700 ring-2 ring-emerald-500/20'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <ThumbsUp size={14} />
                  <span>It is Legitimate</span>
                </button>
              </div>
            </div>

            {/* Comment */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Notes (Optional)
              </label>
              <textarea
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Mention why this was misclassified or additional signals..."
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#5b5bf7]/20 focus:border-[#5b5bf7] resize-none"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 rounded-xl bg-[#5b5bf7] hover:bg-[#4f46e5] text-white text-xs font-semibold shadow-sm transition"
            >
              Submit Feedback
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

