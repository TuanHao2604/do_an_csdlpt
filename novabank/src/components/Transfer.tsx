import React, { useState } from 'react';
import { Building, CreditCard, ArrowRight, CheckCircle2, ArrowLeft, Wallet, AlertTriangle, Loader2, XCircle } from 'lucide-react';
import { internalTransfer, crossBankTransfer, setCrashSimulation } from '../api';

interface TransferProps {
  onBack: () => void;
  userData: any;
}

export default function Transfer({ onBack, userData }: TransferProps) {
  const [step, setStep] = useState(1);
  const [amount, setAmount] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [bank, setBank] = useState('nova_a');
  const [description, setDescription] = useState('');
  const [transferResult, setTransferResult] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [isCrashSimulated, setIsCrashSimulated] = useState(false);

  const myAccount = userData?.accounts?.[0]?.account_number || 'A1001';
  const myBalance = userData?.accounts?.[0]?.balance || 0;

  const formatCurrency = (amount: number) => {
    return `${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} USD`;
  };

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setStep(2);
  };

  const handleConfirm = async () => {
    setIsProcessing(true);
    setError('');
    try {
      const amt = parseFloat(amount);
      let result;

      if (bank === 'nova_a') {
        // Internal transfer (cùng bank A)
        result = await internalTransfer(myAccount, accountNumber, amt);
      } else {
        // Cross-bank transfer qua coordinator (2PC)
        await setCrashSimulation(isCrashSimulated);
        result = await crossBankTransfer(myAccount, accountNumber, amt);
        if (isCrashSimulated) await setCrashSimulation(false);
      }

      setTransferResult(result);
      setStep(3);
    } catch (err: any) {
      setError(err.message || 'Giao dịch thất bại');
    } finally {
      setIsProcessing(false);
    }
  };

  const resetForm = () => {
    setStep(1);
    setAmount('');
    setAccountNumber('');
    setDescription('');
    setTransferResult(null);
    setError('');
    setIsCrashSimulated(false);
  };

  const isSuccess = transferResult?.status === 'success' || transferResult?.status === 'committed';

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-[#004d40] text-white p-4 flex items-center shadow-md z-10">
        <button onClick={step === 1 ? onBack : () => setStep(step - 1)} className="p-2 -ml-2 hover:bg-emerald-800 rounded-full transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-lg font-medium ml-2">Chuyển tiền {bank === 'nova_b' ? '(2PC Liên ngân hàng)' : ''}</h1>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Progress Bar */}
        <div className="flex bg-white border-b border-gray-200 px-4">
          {[1, 2, 3].map((s) => (
            <div 
              key={s} 
              className={`flex-1 py-3 text-center text-sm font-medium relative ${
                step === s ? 'text-[#004d40]' : 'text-gray-400'
              }`}
            >
              {s === 1 ? 'Nhập thông tin' : s === 2 ? 'Xác nhận' : 'Kết quả'}
              {step === s && (
                <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#004d40]"></div>
              )}
            </div>
          ))}
        </div>

        <div className="p-4">
          {step === 1 && (
            <form onSubmit={handleNext} className="space-y-5">
              {/* Source Account */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
                <label className="block text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">Từ tài khoản</label>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                      <Wallet className="w-5 h-5 text-emerald-700" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{myAccount}</p>
                      <p className="text-xs text-gray-500">NovaBank A - SQL Server</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[#004d40]">{formatCurrency(myBalance)}</p>
                  </div>
                </div>
              </div>

              {/* Destination Info */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-4">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Đến người nhận</label>
                
                <div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Building className="h-5 w-5 text-gray-400" />
                    </div>
                    <select
                      value={bank}
                      onChange={(e) => setBank(e.target.value)}
                      className="block w-full pl-10 pr-10 py-3 border border-gray-200 rounded-xl focus:ring-[#004d40] focus:border-[#004d40] text-sm appearance-none bg-gray-50 outline-none font-medium text-gray-800"
                    >
                      <option value="nova_a">🏦 NovaBank A (Nội bộ - SQL Server)</option>
                      <option value="nova_b">🏦 NovaBank B (Liên ngân hàng - PostgreSQL)</option>
                    </select>
                  </div>
                  {bank === 'nova_b' && (
                    <div className="mt-2 p-3 bg-amber-50 border border-amber-200 rounded-lg space-y-3">
                      <p className="text-xs text-amber-700 flex items-center space-x-1">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Giao dịch liên ngân hàng sử dụng <strong>Two-Phase Commit (2PC)</strong></span>
                      </p>
                      
                      <label className="flex items-center cursor-pointer justify-between p-2 bg-white rounded-md border border-amber-100 shadow-sm">
                        <span className="text-xs font-semibold text-amber-900">Giả lập treo hệ thống (Crash)</span>
                        <div className="relative">
                          <input 
                            type="checkbox" 
                            className="sr-only" 
                            checked={isCrashSimulated}
                            onChange={(e) => setIsCrashSimulated(e.target.checked)}
                          />
                          <div className={`block w-10 h-6 rounded-full transition-colors ${isCrashSimulated ? 'bg-amber-500' : 'bg-gray-300'}`}></div>
                          <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${isCrashSimulated ? 'translate-x-4' : ''}`}></div>
                        </div>
                      </label>
                    </div>
                  )}
                </div>

                <div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <CreditCard className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="text"
                      required
                      value={accountNumber}
                      onChange={(e) => setAccountNumber(e.target.value)}
                      className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl focus:ring-[#004d40] focus:border-[#004d40] text-sm bg-gray-50 outline-none font-medium text-gray-800"
                      placeholder={bank === 'nova_b' ? 'Nhập số TK Bank B (vd: B1001)' : 'Nhập số TK Bank A (vd: A1002)'}
                    />
                  </div>
                </div>
              </div>

              {/* Amount & Description */}
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">Số tiền & Nội dung</label>
                  <div className="relative">
                    <input
                      type="number"
                      required
                      min="1"
                      step="0.01"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="block w-full pl-4 pr-12 py-3 text-lg font-bold border border-gray-200 rounded-xl focus:ring-[#004d40] focus:border-[#004d40] bg-gray-50 outline-none text-[#004d40]"
                      placeholder="0.00"
                    />
                    <div className="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                      <span className="text-gray-500 font-medium">USD</span>
                    </div>
                  </div>
                  <div className="mt-3 flex overflow-x-auto pb-2 gap-2 scrollbar-hide">
                    {[50, 100, 200, 500].map(val => (
                      <button
                        key={val}
                        type="button"
                        onClick={() => setAmount(val.toString())}
                        className="px-4 py-1.5 text-xs font-medium bg-emerald-50 text-emerald-700 rounded-full border border-emerald-100 whitespace-nowrap active:bg-emerald-100"
                      >
                        {val} USD
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <input
                    type="text"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="block w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-[#004d40] focus:border-[#004d40] text-sm bg-gray-50 outline-none"
                    placeholder="Nhập nội dung chuyển tiền"
                  />
                </div>
              </div>

              <div className="pt-4 pb-8">
                <button
                  type="submit"
                  className="w-full flex justify-center items-center py-3.5 px-4 rounded-xl shadow-md text-base font-semibold text-white bg-[#004d40] hover:bg-emerald-900 active:scale-[0.98] transition-all"
                >
                  Tiếp tục
                </button>
              </div>
            </form>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 text-center">
                <p className="text-sm text-gray-500 mb-2">Số tiền chuyển</p>
                <h2 className="text-3xl font-bold text-[#004d40]">{formatCurrency(Number(amount))}</h2>
              </div>

              <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-4">
                <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Từ tài khoản</span>
                  <span className="font-semibold text-gray-900">{myAccount}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Đến tài khoản</span>
                  <span className="font-semibold text-gray-900">{accountNumber}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Ngân hàng</span>
                  <span className="font-semibold text-gray-900">{bank === 'nova_a' ? 'NovaBank A' : 'NovaBank B'}</span>
                </div>
                <div className="flex justify-between items-center pb-3 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Loại giao dịch</span>
                  <span className={`font-semibold px-2 py-0.5 rounded-full text-xs ${
                    bank === 'nova_b' 
                      ? 'bg-amber-100 text-amber-800' 
                      : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {bank === 'nova_b' ? '2PC Liên ngân hàng' : 'Nội bộ'}
                  </span>
                </div>
                <div className="flex justify-between items-start pb-3 border-b border-gray-100">
                  <span className="text-sm text-gray-500 w-1/3">Nội dung</span>
                  <span className="font-medium text-gray-900 text-right w-2/3 break-words">{description || 'Chuyen tien'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Phí giao dịch</span>
                  <span className="font-semibold text-emerald-600">Miễn phí</span>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div className="pt-4 pb-8">
                <button
                  onClick={handleConfirm}
                  disabled={isProcessing}
                  className="w-full flex justify-center items-center py-3.5 px-4 rounded-xl shadow-md text-base font-semibold text-white bg-[#004d40] hover:bg-emerald-900 active:scale-[0.98] transition-all disabled:opacity-70"
                >
                  {isProcessing ? (
                    <div className="flex items-center space-x-2">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>{bank === 'nova_b' ? 'Đang xử lý 2PC...' : 'Đang chuyển...'}</span>
                    </div>
                  ) : (
                    'Xác nhận chuyển'
                  )}
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 text-center mt-4">
              <div className={`w-20 h-20 ${isSuccess ? 'bg-emerald-100' : 'bg-red-100'} rounded-full flex items-center justify-center mx-auto mb-6`}>
                {isSuccess ? (
                  <CheckCircle2 className="w-10 h-10 text-emerald-600" />
                ) : (
                  <XCircle className="w-10 h-10 text-red-600" />
                )}
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">
                {isSuccess ? 'Giao dịch thành công' : 'Giao dịch thất bại'}
              </h2>
              <p className={`text-3xl font-bold ${isSuccess ? 'text-[#004d40]' : 'text-red-600'} mb-4`}>
                {formatCurrency(Number(amount))}
              </p>
              
              <div className="bg-gray-50 rounded-xl p-4 text-left space-y-3 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Trạng thái</span>
                  <span className={`font-bold px-2 py-0.5 rounded-full text-xs ${
                    isSuccess ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {transferResult?.status?.toUpperCase()}
                  </span>
                </div>
                {transferResult?.txn_id && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Transaction ID</span>
                    <span className="font-mono text-xs text-gray-700 break-all max-w-[200px] text-right">
                      {transferResult.txn_id}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Người nhận</span>
                  <span className="font-medium text-gray-900">{accountNumber}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Ngân hàng</span>
                  <span className="font-medium text-gray-900">{bank === 'nova_a' ? 'NovaBank A' : 'NovaBank B'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Giao thức</span>
                  <span className="font-medium text-gray-900">{bank === 'nova_b' ? '2PC' : 'Internal'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Thời gian</span>
                  <span className="font-medium text-gray-900">
                    {new Date().toLocaleDateString('vi-VN')} {new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>
              </div>

              {transferResult?.reason && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-4 text-left">
                  <p className="text-sm text-red-700 flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>Lý do: {typeof transferResult.reason === 'string' ? transferResult.reason : JSON.stringify(transferResult.reason)}</span>
                  </p>
                </div>
              )}
              
              <div className="space-y-3">
                <button
                  onClick={resetForm}
                  className="w-full py-3.5 px-4 rounded-xl shadow-sm text-base font-semibold text-white bg-[#004d40] active:scale-[0.98] transition-all"
                >
                  Giao dịch mới
                </button>
                <button
                  onClick={onBack}
                  className="w-full py-3.5 px-4 rounded-xl text-base font-semibold text-[#004d40] bg-emerald-50 active:bg-emerald-100 transition-all"
                >
                  Về trang chủ
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
