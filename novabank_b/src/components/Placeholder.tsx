import React from 'react';
import { Wrench, ArrowLeft } from 'lucide-react';

interface PlaceholderProps {
  title?: string;
  onBack: () => void;
}

export default function Placeholder({ title = 'Tính năng', onBack }: PlaceholderProps) {
  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="bg-emerald-800 text-white p-4 flex items-center">
        <button onClick={onBack} className="p-2 -ml-2 hover:bg-emerald-700 rounded-full transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-lg font-medium ml-2">{title}</h1>
      </div>
      
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-20 h-20 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-6 shadow-inner">
          <Wrench className="w-10 h-10" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Đang phát triển</h2>
        <p className="text-gray-500 max-w-xs mx-auto">
          Tính năng <span className="font-semibold text-emerald-700">"{title}"</span> hiện đang được chúng tôi xây dựng và sẽ sớm ra mắt trong thời gian tới.
        </p>
        
        <button 
          onClick={onBack}
          className="mt-8 px-6 py-3 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors shadow-md"
        >
          Quay lại trang chủ
        </button>
      </div>
    </div>
  );
}
