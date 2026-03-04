import React from 'react';
import { Loader } from 'lucide-react';

interface CompactLoadingOverlayProps {
  message?: string;
}

const CompactLoadingOverlay: React.FC<CompactLoadingOverlayProps> = ({ 
  message = 'Procesando...' 
}) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-[60] pointer-events-none">
      <div className="bg-white rounded-lg shadow-2xl p-6 flex items-center gap-4 pointer-events-auto">
        <Loader className="w-8 h-8 text-blue-600 animate-spin flex-shrink-0" />
        <div>
          <p className="font-semibold text-gray-900">{message}</p>
          <p className="text-xs text-gray-500 mt-1">Por favor espera...</p>
        </div>
      </div>
    </div>
  );
};

export default CompactLoadingOverlay;