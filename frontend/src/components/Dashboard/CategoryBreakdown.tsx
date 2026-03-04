import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { Movement } from '../../types/Movement';

interface CategoryBreakdownProps {
  movements: Movement[];
}

const COLORS = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e', '#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#8b5cf6', '#d946ef'];

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
  }).format(value);
};

export default function CategoryBreakdown({ movements }: CategoryBreakdownProps) {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'gastos' | 'ingresos'>('gastos');

  // Agrupar por categoría (gastos e ingresos)
  const getCategoriesData = (tipo: 'gasto' | 'ingreso') => {
    return movements
      .filter(m => m.tipo === tipo)
      .reduce((acc, mov) => {
        const cat = mov.categoria || 'Sin Categoría';
        if (!acc[cat]) {
          acc[cat] = { total: 0, items: [] };
        }
        acc[cat].total += Math.abs(mov.monto);
        acc[cat].items.push(mov);
        return acc;
      }, {} as { [key: string]: { total: number; items: Movement[] } });
  };

  const gastosData = getCategoriesData('gasto');
  const ingresosData = getCategoriesData('ingreso');

  const categoriesData = activeTab === 'gastos' ? gastosData : ingresosData;
  const categories = Object.entries(categoriesData)
    .sort((a, b) => b[1].total - a[1].total);

  const chartData = categories.map(([name, data]) => ({
    name,
    value: data.total,
  }));

  const total = categories.reduce((sum, [, data]) => sum + data.total, 0);

  if (categories.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 shadow-lg text-center">
        <p className="text-gray-500">No hay {activeTab} para mostrar</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Tabs */}
      <div className="flex gap-4 bg-white rounded-2xl p-6 shadow-lg">
        <button
          onClick={() => setActiveTab('gastos')}
          className={`px-6 py-2 rounded-lg font-semibold transition ${
            activeTab === 'gastos'
              ? 'bg-red-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          💸 Gastos por Categoría
        </button>
        <button
          onClick={() => setActiveTab('ingresos')}
          className={`px-6 py-2 rounded-lg font-semibold transition ${
            activeTab === 'ingresos'
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          💰 Ingresos por Categoría
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Gráfico Pie */}
        <div className="lg:col-span-1 bg-white rounded-2xl p-8 shadow-lg">
          <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">📊 Distribución</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => formatCurrency(value as number)}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Listado de Categorías */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-8 shadow-lg">
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            {activeTab === 'gastos' ? '💸 Gastos por Categoría' : '💰 Ingresos por Categoría'}
          </h3>
          
          <div className="space-y-3">
            {categories.map(([category, data], idx) => {
              const isExpanded = expandedCategory === category;
              const percentage = (data.total / total) * 100;
              const color = activeTab === 'gastos' ? 'text-red-600' : 'text-green-600';

              return (
                <div key={category} className="border border-gray-200 rounded-xl overflow-hidden hover:border-gray-300 transition">
                  {/* Header categoría */}
                  <button
                    onClick={() => setExpandedCategory(isExpanded ? null : category)}
                    className="w-full flex items-center justify-between hover:bg-gray-50 p-4 transition"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></div>
                      <div className="text-left">
                        <h4 className="font-semibold text-gray-900">{category}</h4>
                        <p className="text-xs text-gray-500">{data.items.length} movimientos</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={`font-bold ${color}`}>{formatCurrency(data.total)}</p>
                        <p className="text-xs text-gray-500">{percentage.toFixed(1)}%</p>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </button>

                  {/* Detalles expandibles */}
                  {isExpanded && (
                    <div className="bg-gray-50 border-t border-gray-200 p-4 space-y-2 max-h-96 overflow-y-auto">
                      {data.items.map(item => (
                        <div key={item.id} className="flex items-center justify-between text-sm bg-white p-3 rounded-lg">
                          <div>
                            <p className="text-gray-900 font-medium">{item.descripcion}</p>
                            <p className="text-xs text-gray-500">{item.fecha}</p>
                          </div>
                          <p className={`font-semibold ${activeTab === 'gastos' ? 'text-red-600' : 'text-green-600'}`}>
                            {activeTab === 'gastos' ? '-' : '+'}
                            {formatCurrency(Math.abs(item.monto))}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}