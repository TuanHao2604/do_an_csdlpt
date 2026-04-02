import React from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet, CreditCard, Plus, Send } from 'lucide-react';
import { mockAccounts, mockTransactions } from '../data/mockData';

export default function Dashboard({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  const totalBalance = mockAccounts.reduce((sum, acc) => sum + acc.balance, 0);

  return (
    <div className="space-y-6">
      {/* Balance Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-gradient-to-br from-blue-600 to-blue-800 rounded-3xl p-8 text-white shadow-xl shadow-blue-900/20 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
          <div className="relative z-10">
            <p className="text-blue-100 font-medium mb-2">Tổng số dư</p>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-8">
              {formatCurrency(totalBalance)}
            </h2>
            
            <div className="flex flex-wrap gap-4">
              <button 
                onClick={() => onNavigate('transfer')}
                className="flex items-center px-5 py-2.5 bg-white text-blue-700 rounded-xl font-medium hover:bg-blue-50 transition-colors shadow-sm cursor-pointer"
              >
                <Send className="w-4 h-4 mr-2" />
                Chuyển tiền
              </button>
              <button className="flex items-center px-5 py-2.5 bg-blue-700/50 text-white rounded-xl font-medium hover:bg-blue-700/70 transition-colors backdrop-blur-sm border border-blue-500/30 cursor-pointer">
                <Plus className="w-4 h-4 mr-2" />
                Nạp tiền
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Thẻ tín dụng</h3>
              <CreditCard className="w-5 h-5 text-gray-400" />
            </div>
            <div className="w-full h-32 bg-gradient-to-r from-gray-800 to-gray-900 rounded-xl p-4 text-white flex flex-col justify-between relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-xl -translate-y-1/2 translate-x-1/4"></div>
              <div className="flex justify-between items-start relative z-10">
                <span className="text-xs text-gray-300">Nova Platinum</span>
                <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="7" cy="12" r="7" fill="#EB001B" fillOpacity="0.8"/>
                  <circle cx="17" cy="12" r="7" fill="#F79E1B" fillOpacity="0.8"/>
                </svg>
              </div>
              <div className="relative z-10">
                <p className="text-sm tracking-widest font-mono">**** **** **** 4281</p>
              </div>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">Hạn mức còn lại</span>
              <span className="font-semibold text-gray-900">{formatCurrency(45000000)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Accounts List */}
        <div className="lg:col-span-1 bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-gray-900">Tài khoản của bạn</h3>
          </div>
          <div className="space-y-4">
            {mockAccounts.map(account => (
              <div key={account.id} className="p-4 rounded-2xl border border-gray-100 hover:border-blue-100 hover:bg-blue-50/50 transition-colors cursor-pointer">
                <div className="flex items-center mb-2">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                    <Wallet className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{account.type === 'Checking' ? 'Tài khoản thanh toán' : 'Tài khoản tiết kiệm'}</p>
                    <p className="text-xs text-gray-500 font-mono">{account.accountNumber}</p>
                  </div>
                </div>
                <p className="text-lg font-bold text-gray-900 mt-2">{formatCurrency(account.balance)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-gray-900">Giao dịch gần đây</h3>
            <button 
              onClick={() => onNavigate('history')}
              className="text-sm font-medium text-blue-600 hover:text-blue-700 cursor-pointer"
            >
              Xem tất cả
            </button>
          </div>
          <div className="space-y-4">
            {mockTransactions.slice(0, 4).map(tx => (
              <div key={tx.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-xl transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    tx.type === 'credit' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  }`}>
                    {tx.type === 'credit' ? <ArrowDownRight className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{tx.description}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(tx.date).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
                <div className={`text-sm font-semibold ${tx.type === 'credit' ? 'text-green-600' : 'text-gray-900'}`}>
                  {tx.type === 'credit' ? '+' : '-'}{formatCurrency(tx.amount)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
