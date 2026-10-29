import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import CheckEmailPage from './pages/CheckEmailPage';
import PredictionResultPage from './pages/PredictionResultPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import ModelMonitoringPage from './pages/ModelMonitoringPage';
import FeedbackPage from './pages/FeedbackPage';
import FeedbackModal from './components/FeedbackModal';

export default function App() {
  const [currentTab, setCurrentTab] = useState('home');
  const [latestResult, setLatestResult] = useState(null);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [feedbackScanData, setFeedbackScanData] = useState(null);

  const handleOpenFeedback = (scanData) => {
    setFeedbackScanData(scanData || latestResult);
    setFeedbackModalOpen(true);
  };

  return (
    <div className="flex min-h-screen bg-[#f8fafc] text-[#0f172a] font-sans antialiased selection:bg-indigo-100 selection:text-indigo-800">
      {/* Persistent Left Navigation Sidebar */}
      <Sidebar 
        currentTab={currentTab} 
        setCurrentTab={setCurrentTab} 
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          currentTab={currentTab} 
          setCurrentTab={setCurrentTab} 
        />

        <main className="flex-1 overflow-y-auto pb-12">
          {currentTab === 'home' && (
            <HomePage 
              setCurrentTab={setCurrentTab} 
            />
          )}

          {currentTab === 'check' && (
            <CheckEmailPage 
              setCurrentTab={setCurrentTab} 
              setLatestResult={setLatestResult} 
            />
          )}

          {currentTab === 'result' && (
            <PredictionResultPage
              result={latestResult}
              setCurrentTab={setCurrentTab}
              onOpenFeedback={handleOpenFeedback}
            />
          )}

          {currentTab === 'admin' && (
            <AdminDashboardPage 
              setCurrentTab={setCurrentTab}
              onOpenFeedback={handleOpenFeedback}
              setLatestResult={setLatestResult}
            />
          )}

          {currentTab === 'monitoring' && (
            <ModelMonitoringPage 
              setCurrentTab={setCurrentTab}
            />
          )}

          {currentTab === 'feedback' && (
            <FeedbackPage 
              onOpenFeedback={handleOpenFeedback}
            />
          )}
        </main>
      </div>

      {/* Human-In-The-Loop Feedback Modal */}
      <FeedbackModal
        isOpen={feedbackModalOpen}
        onClose={() => setFeedbackModalOpen(false)}
        scanData={feedbackScanData}
      />
    </div>
  );
}
