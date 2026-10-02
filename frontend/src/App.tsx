import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import type { TabType } from './components/Sidebar';
import { Header } from './components/Header';
import { useSidebarController } from './controller/sidebarController';
import { DashboardPage } from './pages/DashboardPage';
import { Nifty50Page } from './pages/Nifty50Page';
import { OptionChainPage } from './pages/OptionChainPage';
import { NewsPage } from './pages/NewsPage';
import { WatchlistPage } from './pages/WatchlistPage';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const sidebar = useSidebarController();

  // Render core active tab page
  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'option-chain':
        return <OptionChainPage />;
      case 'nifty50':
        return <Nifty50Page />;
      case 'news':
        return <NewsPage />;
      case 'watchlist':
        return <WatchlistPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="app-container">
      {/* Adjustable Groww Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isCollapsed={sidebar.isCollapsed}
        onToggleCollapse={sidebar.toggleCollapse}
        width={sidebar.width}
      />

      {/* Main Content Viewport */}
      <div className="main-content">
        <Header />
        {renderTabContent()}
      </div>
    </div>
  );
};

export default App;
