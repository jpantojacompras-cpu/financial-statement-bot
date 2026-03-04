import React, { useEffect } from 'react';
import { Check, AlertCircle, X } from 'lucide-react';

interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
  autoClose?: number;
}

export default function Toast({ message, type, onClose, autoClose = 4000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, autoClose);
    return () => clearTimeout(timer);
  }, [onClose, autoClose]);

  const bgColor = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
  }[type];

  const Icon = {
    success: Check,
    error: AlertCircle,
    info: AlertCircle,
  }[type];

  return (
    <div className={`fixed bottom-4 right-4 ${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in z-[999]`}>
      <Icon className="w-5 h-5 flex-shrink-0" />
      <p className="font-semibold">{message}</p>
      <button
        onClick={onClose}
        className="ml-4 hover:bg-white/20 p-1 rounded transition"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}