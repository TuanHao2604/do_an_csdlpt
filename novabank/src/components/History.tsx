import React, { useState, useEffect } from 'react';
import { ArrowLeft, ArrowUpRight, ArrowDownLeft, RefreshCw, Calendar } from 'lucide-react';
import { getTransactions } from '../api';

interface HistoryProps {
  onBack: () => void;
  userData: any;
}

export default function History({ onBack, userData }: HistoryProps) {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const accountNumber = userData?.accounts?.[0]?.account_number || 'N/A';

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await getTransactions(accountNumber);
      if (res.transactions) {
        setTransactions(res.transactions);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (accountNumber !== 'N/A') fetchTransactions();
  }, [accountNumber]);

  const formatCurrency = (amount: number) => {
    return `${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} USD`;
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="bg-[#004d40] text-white p-4 flex items-center justify-between shadow-md z-10">
        <div className="flex items-center">
          <button onClick={onBack} className="p-2 -ml-2 hover:bg-emerald-800 rounded-full transition-colors">
            <ArrowLeft className="w-6 h-6" />
          </button>
          <h1 className="text-lg font-medium ml-2">Lịch sử giao dịch</h1>
        </div>
        <button onClick={fetchTransactions} className="p-2 hover:bg-emerald-800 rounded-full">
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && (
          <div className="text-center py-10 text-gray-500">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-emerald-600" />
            <p>Đang tải...</p>
          </div>
        )}

        {!loading && transactions.length === 0 && (
          <div className="text-center py-10 text-gray-500">
            <Calendar className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="font-medium">Chưa có giao dịch nào</p>
          </div>
        )}

        {!loading && transactions.map((txn) => {
          const isIncoming = txn.type.includes('in') || txn.type === 'credit';
          return (
            <div key={txn.id} className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  isIncoming ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                }`}>
                  {isIncoming ? <ArrowDownLeft className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
                </div>
                <div>
                  <p className="font-medium text-gray-800 text-sm">
                    {txn.type === 'transfer_out' ? 'Chuyển tiền' : 
                     txn.type === 'transfer_in' ? 'Nhận tiền' :
                     txn.type === 'refund_in' ? 'Hoàn tiền' :
                     txn.type === 'withdraw' ? 'Rút tiền' : txn.type}
                  </p>
                  <p className="text-xs text-gray-500">{txn.counterpart || '—'}</p>
                  <p className="text-xs text-gray-400">{txn.created_at?.substring(0, 19)}</p>
                </div>
              </div>
              <div className="text-right">
                <span className={`font-bold text-sm ${isIncoming ? 'text-green-600' : 'text-red-600'}`}>
                  {isIncoming ? '+' : '-'}{formatCurrency(txn.amount)}
                </span>
                <p className={`text-xs mt-0.5 ${txn.status === 'success' ? 'text-green-500' : 'text-gray-400'}`}>
                  {txn.status}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
