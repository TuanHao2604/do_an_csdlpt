import React from 'react';
import { Home, Gift, QrCode, Grid, Settings } from 'lucide-react';

interface MobileLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export default function MobileLayout({ children, activeTab, onTabChange }: MobileLayoutProps) {
  const navItems = [
    { id: 'home', label: 'Trang chủ', icon: Home },
    { id: 'rewards', label: 'Đổi quà', icon: Gift },
    { id: 'qr', label: 'Quét QR', icon: QrCode, isSpecial: true },
    { id: 'products', label: 'Sản phẩm', icon: Grid },
    { id: 'settings', label: 'Cài đặt', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-200 flex justify-center font-sans">
      {/* Mobile Device Container */}
      <div className="w-full max-w-md bg-white h-screen flex flex-col relative shadow-2xl overflow-hidden sm:border-x sm:border-gray-300">
        
        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden bg-[#f4fbf9] pb-20 scrollbar-hide">
          {children}
        </main>

        {/* Bottom Navigation Bar */}
        <nav className="absolute bottom-0 w-full bg-[#004d40] text-white rounded-t-2xl px-2 pb-safe pt-2 z-50">
          <div className="flex justify-between items-end h-16 relative">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              
              if (item.isSpecial) {
                return (
                  <div key={item.id} className="flex-1 flex justify-center relative -top-4">
                    <button 
                      onClick={() => onTabChange(item.id)}
                      className="flex flex-col items-center group"
                    >
                      <div className="w-14 h-14 bg-[#004d40] rounded-2xl flex items-center justify-center border-2 border-[#f5b041] shadow-lg transform group-active:scale-95 transition-transform">
                        <Icon className="w-7 h-7 text-[#f5b041]" />
                      </div>
                      <span className="text-[10px] mt-1 font-medium text-emerald-100">{item.label}</span>
                    </button>
                  </div>
                );
              }

              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className="flex-1 flex flex-col items-center justify-center pb-2 group"
                >
                  <div className={`p-1 rounded-xl transition-colors ${isActive ? 'bg-emerald-800/50' : 'transparent'}`}>
                    <Icon className={`w-6 h-6 mb-1 ${isActive ? 'text-white' : 'text-emerald-300 group-hover:text-emerald-100'}`} />
                  </div>
                  <span className={`text-[10px] font-medium ${isActive ? 'text-white' : 'text-emerald-300'}`}>
                    {item.label}
                  </span>
                </button>
              );
            })}
          </div>
        </nav>
      </div>
    </div>
  );
}
