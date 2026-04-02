/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import Login from './components/Login';
import MobileLayout from './components/MobileLayout';
import Home from './components/Home';
import SettingsScreen from './components/SettingsScreen';
import Transfer from './components/Transfer';
import History from './components/History';
import Placeholder from './components/Placeholder';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('home');
  const [currentView, setCurrentView] = useState('main');
  const [placeholderTitle, setPlaceholderTitle] = useState('');
  const [userData, setUserData] = useState<any>(null);

  if (!isAuthenticated) {
    return <Login onLogin={(data: any) => {
      setUserData(data);
      setIsAuthenticated(true);
    }} />;
  }

  const handleNavigate = (view: string, title?: string) => {
    if (view === 'placeholder') {
      setPlaceholderTitle(title || 'Tính năng');
    }
    setCurrentView(view);
  };

  const handleTabChange = (tab: string) => {
    if (tab === 'qr' || tab === 'rewards' || tab === 'products') {
      const titles: Record<string, string> = {
        qr: 'Quét QR',
        rewards: 'Đổi quà',
        products: 'Sản phẩm'
      };
      setPlaceholderTitle(titles[tab]);
      setCurrentView('placeholder');
      setActiveTab(tab);
      return;
    }
    
    setActiveTab(tab);
    setCurrentView('main');
  };

  const renderContent = () => {
    if (currentView === 'transfer') {
      return <Transfer onBack={() => setCurrentView('main')} userData={userData} />;
    }
    
    if (currentView === 'placeholder') {
      return <Placeholder title={placeholderTitle} onBack={() => setCurrentView('main')} />;
    }

    switch (activeTab) {
      case 'home':
        return <Home onNavigate={handleNavigate} userData={userData} />;
      case 'settings':
        return <SettingsScreen onNavigate={handleNavigate} onLogout={() => {
          setIsAuthenticated(false);
          setUserData(null);
        }} />;
      default:
        return <Home onNavigate={handleNavigate} userData={userData} />;
    }
  };

  return (
    <MobileLayout 
      activeTab={activeTab} 
      onTabChange={handleTabChange}
    >
      {renderContent()}
    </MobileLayout>
  );
}
