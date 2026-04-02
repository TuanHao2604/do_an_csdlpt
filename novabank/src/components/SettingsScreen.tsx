import React from 'react';
import { 
  User, Palette, Image as ImageIcon, Globe, Keyboard, 
  Fingerprint, ScanFace, KeyRound, LogIn, Lock, 
  FileText, Users, Mail, FileSignature, SlidersHorizontal, 
  LineChart, Trash2, LogOut, ChevronRight, ChevronDown
} from 'lucide-react';

interface SettingsScreenProps {
  onNavigate: (view: string, title?: string) => void;
  onLogout: () => void;
}

export default function SettingsScreen({ onNavigate, onLogout }: SettingsScreenProps) {
  const personalSettings = [
    { icon: User, label: 'Đổi ảnh đại diện' },
    { icon: Palette, label: 'Đổi giao diện' },
    { icon: ImageIcon, label: 'Đổi ảnh nền' },
    { icon: Globe, label: 'Ngôn ngữ', value: 'VN', valueIcon: '🇻🇳' },
    { icon: Keyboard, label: 'Bàn phím' },
  ];

  const securitySettings = [
    { icon: ScanFace, label: 'Cài đặt sinh trắc học' },
    { icon: Fingerprint, label: 'Cài đặt vân tay' },
    { icon: KeyRound, label: 'Cài đặt Smart OTP' },
    { icon: LogIn, label: 'Cài đặt đăng nhập' },
    { icon: Lock, label: 'Đổi mật khẩu' },
  ];

  const serviceSettings = [
    { icon: FileText, label: 'Báo cáo giao dịch' },
    { icon: Users, label: 'Danh bạ chuyển tiền' },
    { icon: Mail, label: 'Nhận email thông báo' },
    { icon: FileSignature, label: 'Mẫu thanh toán' },
    { icon: SlidersHorizontal, label: 'Đổi hạn mức giao dịch' },
    { icon: LineChart, label: 'Biến động số dư' },
    { icon: Trash2, label: 'Đóng tài khoản' },
  ];

  const renderSection = (title: string, items: any[]) => (
    <div className="mb-6">
      <div className="flex justify-between items-center px-4 mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="w-6 h-6 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-800">
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden mx-4">
        <div className="divide-y divide-gray-50">
          {items.map((item, index) => (
            <button
              key={index}
              onClick={() => onNavigate('placeholder', item.label)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors active:bg-gray-100"
            >
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 rounded-full border border-emerald-100 flex items-center justify-center text-emerald-800">
                  <item.icon className="w-5 h-5" strokeWidth={1.5} />
                </div>
                <span className="text-gray-800 font-medium">{item.label}</span>
              </div>
              <div className="flex items-center space-x-2">
                {item.value && (
                  <div className="flex items-center space-x-1 bg-gray-100 px-2 py-1 rounded-full">
                    <span className="text-sm">{item.valueIcon}</span>
                    <span className="text-xs font-semibold text-gray-700">{item.value}</span>
                  </div>
                )}
                {!item.value && <ChevronRight className="w-5 h-5 text-gray-300" />}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-full bg-gradient-to-b from-[#e0f2f1] to-[#f4fbf9] pb-8 pt-4">
      {/* Header */}
      <div className="px-4 flex justify-end mb-4">
        <button 
          onClick={onLogout}
          className="flex items-center space-x-1 bg-red-50 text-red-600 px-3 py-1.5 rounded-full border border-red-100 active:bg-red-100 transition-colors"
        >
          <span className="text-sm font-medium">Thoát</span>
          <LogOut className="w-4 h-4" />
        </button>
      </div>

      {/* Profile Info */}
      <div className="flex flex-col items-center mb-8">
        <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center mb-3 border-4 border-white shadow-sm">
          <User className="w-12 h-12 text-gray-400" />
        </div>
        <p className="text-gray-600 text-sm">Chào buổi chiều!</p>
        <h2 className="text-xl font-bold text-[#004d40]">Nguyen Tuan Hao</h2>
      </div>

      {/* Settings Sections */}
      {renderSection('Cài đặt cá nhân', personalSettings)}
      {renderSection('Cài đặt An toàn - Bảo mật', securitySettings)}
      {renderSection('Cài đặt dịch vụ', serviceSettings)}

      <div className="text-center mt-8 mb-4">
        <p className="text-sm text-gray-400">Phiên bản 5.3.01</p>
      </div>
    </div>
  );
}
