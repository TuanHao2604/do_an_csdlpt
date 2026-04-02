import React, { useState, useEffect } from 'react';
import { 
  Smartphone, Gamepad2, Plane, Car, Film, MessageSquare, 
  MessageCircle, FileText, Search, ChevronRight, ArrowRightLeft, Wallet,
  Eye, EyeOff, CreditCard, RefreshCw, Clock
} from 'lucide-react';
import { getBalance, getTransactions } from '../api';

interface HomeProps {
  onNavigate: (view: string, title?: string) => void;
  userData: any;
}

export default function Home({ onNavigate, userData }: HomeProps) {
  const [showBalance, setShowBalance] = useState(false);
  const [balance, setBalance] = useState<number | null>(null);
  const [recentTxns, setRecentTxns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const accountNumber = userData?.accounts?.[0]?.account_number || 'N/A';

  const fetchData = async () => {
    setLoading(true);
    try {
      const balRes = await getBalance(accountNumber);
      if (balRes.balance !== undefined) setBalance(balRes.balance);

      const txnRes = await getTransactions(accountNumber);
      if (txnRes.transactions) setRecentTxns(txnRes.transactions.slice(0, 5));
    } catch (e) {
      console.error('Failed to fetch data', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (accountNumber !== 'N/A') fetchData();
  }, [accountNumber]);

  const formatCurrency = (amount: number) => {
    return `${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} USD`;
  };

  const utilities = [
    { icon: Smartphone, label: 'Data 4G/5G', badge: '-30%' },
    { icon: Gamepad2, label: 'Thẻ game' },
    { icon: Plane, label: 'Vé máy bay' },
    { icon: Car, label: 'VNPAY Taxi' },
    { icon: Film, label: 'Vé xem phim', badge: '75K' },
    { icon: MessageSquare, label: 'Vietlott SMS' },
  ];

  const supportItems = [
    { icon: FileText, label: 'Hướng dẫn sử dụng' },
    { icon: Search, label: 'Tra soát khiếu nại' },
    { icon: Search, label: 'Tra cứu thông tin' },
    { icon: MessageSquare, label: 'Góp ý dịch vụ' },
  ];

  return (
    <div className="min-h-full bg-gradient-to-b from-[#e8eaf6] to-[#f5f6ff] pb-8">
      {/* Top Section - Blue theme */}
      <div className="bg-[#1a237e] rounded-b-[2.5rem] p-6 pt-12 text-white shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-800 font-bold text-xl border-2 border-white">
                {userData?.full_name?.charAt(0) || 'B'}
              </div>
              <div>
                <p className="text-indigo-200 text-sm">Xin chào,</p>
                <p className="font-semibold text-lg">{userData?.full_name || 'User'}</p>
              </div>
            </div>
            <button onClick={fetchData} className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors">
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/20 mb-6">
            <div className="flex items-center justify-between mb-1">
              <p className="text-indigo-200 text-sm">Số dư khả dụng</p>
              <span className="text-xs bg-indigo-600/50 px-2 py-0.5 rounded-full">{accountNumber}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <h2 className="text-2xl font-bold">
                  {showBalance 
                    ? (balance !== null ? formatCurrency(balance) : 'Đang tải...') 
                    : '***** USD'}
                </h2>
                <button 
                  onClick={() => setShowBalance(!showBalance)}
                  className="p-1.5 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                >
                  {showBalance ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <button 
                onClick={() => onNavigate('placeholder', 'Tài khoản')}
                className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
              >
                <Wallet className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Main Actions */}
          <div className="grid grid-cols-2 gap-4">
            <button 
              onClick={() => onNavigate('transfer')}
              className="bg-white text-[#1a237e] py-3 px-4 rounded-xl font-semibold flex items-center justify-center space-x-2 shadow-md active:scale-95 transition-transform"
            >
              <ArrowRightLeft className="w-5 h-5" />
              <span>Chuyển tiền</span>
            </button>
            <button 
              onClick={() => onNavigate('placeholder', 'Thông tin thẻ')}
              className="bg-indigo-600/50 text-white py-3 px-4 rounded-xl font-semibold flex items-center justify-center space-x-2 border border-indigo-500/50 active:scale-95 transition-transform"
            >
              <CreditCard className="w-5 h-5" />
              <span>Thông tin thẻ</span>
            </button>
          </div>
        </div>
      </div>

      <div className="px-4 mt-6 space-y-6">
        {/* Recent Transactions */}
        {recentTxns.length > 0 && (
          <div>
            <div className="flex justify-between items-center mb-3 px-1">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center space-x-2">
                <Clock className="w-5 h-5 text-indigo-600" />
                <span>Giao dịch gần đây</span>
              </h3>
            </div>
            <div className="bg-white rounded-3xl shadow-sm border border-indigo-50 overflow-hidden">
              {recentTxns.map((txn, index) => (
                <div key={txn.id} className={`p-4 flex items-center justify-between ${index < recentTxns.length - 1 ? 'border-b border-gray-100' : ''}`}>
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      txn.type.includes('in') || txn.type === 'credit' 
                        ? 'bg-green-100 text-green-600' 
                        : 'bg-red-100 text-red-600'
                    }`}>
                      <ArrowRightLeft className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-800 text-sm">
                        {txn.type === 'transfer_out' ? 'Chuyển tiền' : 
                         txn.type === 'transfer_in' ? 'Nhận tiền' :
                         txn.type === 'refund_in' ? 'Hoàn tiền' :
                         txn.type === 'withdraw' ? 'Rút tiền' : txn.type}
                      </p>
                      <p className="text-xs text-gray-500">{txn.counterpart || '—'}</p>
                    </div>
                  </div>
                  <span className={`font-bold text-sm ${
                    txn.type.includes('in') || txn.type === 'credit' 
                      ? 'text-green-600' 
                      : 'text-red-600'
                  }`}>
                    {txn.type.includes('in') || txn.type === 'credit' ? '+' : '-'}
                    {formatCurrency(txn.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tiện ích */}
        <div>
          <div className="flex justify-between items-center mb-3 px-1">
            <h3 className="text-lg font-semibold text-gray-800">Tiện ích cuộc sống</h3>
            <button 
              onClick={() => onNavigate('placeholder', 'Tất cả tiện ích')}
              className="text-indigo-700 text-sm font-medium flex items-center"
            >
              Xem tất cả <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>
          <div className="bg-white rounded-3xl p-5 shadow-sm border border-indigo-50">
            <div className="grid grid-cols-3 gap-y-6 gap-x-4">
              {utilities.map((item, index) => (
                <button 
                  key={index} 
                  onClick={() => onNavigate('placeholder', item.label)}
                  className="flex flex-col items-center group"
                >
                  <div className="relative mb-2">
                    <div className="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-800 group-active:scale-95 transition-transform">
                      <item.icon className="w-7 h-7" strokeWidth={1.5} />
                    </div>
                    {item.badge && (
                      <span className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full border-2 border-white">
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-center text-gray-700 font-medium leading-tight">{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Support */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 px-1">Hỗ trợ 24/7</h3>
          <div className="bg-white rounded-3xl shadow-sm border border-indigo-50 overflow-hidden relative">
            <div className="bg-[#e8eaf6] p-5 pb-6">
              <div className="pr-20">
                <p className="text-gray-800 font-medium mb-4 leading-snug">
                  Bạn đang gặp vấn đề gì cần hỗ trợ?
                </p>
                <div className="flex space-x-3">
                  <button 
                    onClick={() => onNavigate('placeholder', 'Chat hỗ trợ')}
                    className="flex-1 bg-white text-indigo-800 py-2.5 px-4 rounded-full font-semibold flex items-center justify-center space-x-2 shadow-sm border border-indigo-100 active:scale-95 transition-transform"
                  >
                    <MessageCircle className="w-5 h-5" />
                    <span>Chat cùng NovaBank</span>
                  </button>
                  <button 
                    onClick={() => onNavigate('placeholder', 'Gọi tổng đài')}
                    className="w-11 h-11 bg-[#1a237e] text-white rounded-full flex items-center justify-center shadow-sm shrink-0 active:scale-95 transition-transform"
                  >
                    <Smartphone className="w-5 h-5" />
                  </button>
                </div>
              </div>
              <div className="absolute top-2 right-2 w-24 h-24 bg-indigo-200 rounded-full flex items-center justify-center border-4 border-white shadow-md">
                <div className="text-indigo-700 text-center leading-tight font-bold">
                  <span className="text-2xl">🤖</span><br/><span className="text-xs">Hi!</span>
                </div>
              </div>
            </div>
            
            <div className="divide-y divide-gray-100">
              {supportItems.map((item, index) => (
                <button 
                  key={index}
                  onClick={() => onNavigate('placeholder', item.label)}
                  className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors active:bg-gray-100"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-700">
                      <item.icon className="w-5 h-5" strokeWidth={1.5} />
                    </div>
                    <span className="font-medium text-gray-800">{item.label}</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
