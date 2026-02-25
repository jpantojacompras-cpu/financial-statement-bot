import React from 'react';
import { Upload, BarChart3, TrendingUp, BarChart, Files } from 'lucide-react';

interface SidebarProps {
  currentPage: 'upload' | 'movements' | 'dashboard' | 'analysis' | 'files';
  setCurrentPage: (page: 'upload' | 'movements' | 'dashboard' | 'analysis' | 'files') => void;
}

export default function Sidebar({ currentPage, setCurrentPage }: SidebarProps) {
  const menuItems = [
    {
      id: 'upload',
      label: 'Cargar',
      icon: Upload,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      hoverBg: 'hover:bg-purple-50',
    },
    {
      id: 'movements',
      label: 'Movimientos',
      icon: BarChart3,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      hoverBg: 'hover:bg-blue-50',
    },
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      hoverBg: 'hover:bg-green-50',
    },
    {
      id: 'analysis',
      label: 'Análisis',
      icon: BarChart,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      hoverBg: 'hover:bg-orange-50',
    },
    {
      id: 'files',
      label: 'Archivos',
      icon: Files,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100',
      hoverBg: 'hover:bg-indigo-50',
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 shadow-sm flex flex-col h-screen">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">💰</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">FinBot</h1>
            <p className="text-xs text-gray-600">v1.0.0</p>
          </div>
        </div>
      </div>

      {/* Menu */}
      <nav className="p-4 space-y-2 flex-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id as any)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-semibold transition-all ${
                isActive
                  ? `${item.bgColor} ${item.color} shadow-sm`
                  : `text-gray-700 ${item.hoverBg}`
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
              {isActive && (
                <div className="ml-auto w-2 h-2 rounded-full bg-current"></div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-center">
          <p className="text-xs text-gray-600 mb-3">
            Financial Statement Bot
          </p>
          <div className="flex gap-2">
            <button className="flex-1 px-3 py-2 text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors">
              Ayuda
            </button>
            <button className="flex-1 px-3 py-2 text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors">
              Settings
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}