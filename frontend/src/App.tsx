import React, { useState, useEffect } from 'react';
import { Sidebar, TabKey } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { OverviewPage } from './pages/OverviewPage';
import { RevenuePage } from './pages/RevenuePage';
import { CustomersPage } from './pages/CustomersPage';
import { CohortsPage } from './pages/CohortsPage';
import { RiskPage } from './pages/RiskPage';
import { StatisticsPage } from './pages/StatisticsPage';
import { InsightsPage } from './pages/InsightsPage';
import { ModelLabPage } from './pages/ModelLabPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { AssistantPage } from './pages/AssistantPage';
import { api } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [activeModelTag, setActiveModelTag] = useState<string | undefined>();
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    loadActiveModel();
  }, [refreshKey]);

  const loadActiveModel = async () => {
    try {
      const res = await api.getActiveModel();
      if (res.active && res.version_tag) {
        setActiveModelTag(res.version_tag);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Fixed Sidebar */}
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar onRefreshData={handleRefresh} activeModelTag={activeModelTag} />

        <main className="flex-1 overflow-y-auto" key={refreshKey}>
          {activeTab === 'overview' && <OverviewPage />}
          {activeTab === 'revenue' && <RevenuePage />}
          {activeTab === 'customers' && <CustomersPage />}
          {activeTab === 'cohorts' && <CohortsPage />}
          {activeTab === 'risk' && <RiskPage />}
          {activeTab === 'statistics' && <StatisticsPage />}
          {activeTab === 'insights' && <InsightsPage />}
          {activeTab === 'lab' && <ModelLabPage />}
          {activeTab === 'quality' && <DataQualityPage />}
          {activeTab === 'assistant' && <AssistantPage />}
        </main>
      </div>
    </div>
  );
}

export default App;
