import React, { useState, useEffect } from 'react';
import { Loader } from 'lucide-react';

interface LoadingBarProps {
  isVisible: boolean;
  progress: number; // 0-100
  message?: string;
}

export default function LoadingBar({
  isVisible,
  progress,
  message = 'Cargando...',
}: LoadingBarProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <div className="flex flex-col items-center gap-6">
          {/* Spinner */}
          <Loader className="w-12 h-12 text-blue-600 animate-spin" />

          {/* Mensaje */}
          <div className="text-center">
            <h3 className="text-lg font-bold text-gray-900 mb-2">{message}</h3>
            <p className="text-3xl font-bold text-blue-600">{progress}%</p>
          </div>

          {/* Barra de progreso */}
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-full transition-all duration-300 ease-out"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>

          {/* Detalles */}
          <p className="text-sm text-gray-500 text-center">
            Por favor espera mientras se cargan los archivos...
          </p>
        </div>
      </div>
    </div>
  );
}