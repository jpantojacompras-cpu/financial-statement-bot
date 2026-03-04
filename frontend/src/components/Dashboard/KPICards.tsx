import React from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { Movement } from '../../types/Movement';

interface KPICardsProps {
  movements: Movement[];
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
  }).format(value);
};

export default function KPICards({ movements }: KPICardsProps) {
  const totalIngresos = movements
    .filter(m => m.tipo === 'ingreso')
    .reduce((sum, m) => sum + m.monto, 0);

  const totalGastos = movements
    .filter(m => m.tipo === 'gasto')
    .reduce((sum, m) => sum + m.monto, 0);

  const saldo = totalIngresos - totalGastos;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Card Ingresos */}
      <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-8 shadow-lg border border-green-200 hover:shadow-xl transition-shadow">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-green-700 text-sm font-semibold mb-3 uppercase tracking-wide">Total Ingresos</p>
            <p className="text-4xl font-bold text-green-900">
              {formatCurrency(totalIngresos)}
            </p>
          </div>
          <div className="bg-green-500 p-5 rounded-2xl shadow-lg">
            <TrendingUp className="w-8 h-8 text-white" strokeWidth={3} />
          </div>
        </div>
      </div>

      {/* Card Gastos */}
      <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-2xl p-8 shadow-lg border border-red-200 hover:shadow-xl transition-shadow">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-red-700 text-sm font-semibold mb-3 uppercase tracking-wide">Total Gastos</p>
            <p className="text-4xl font-bold text-red-900">
              {formatCurrency(totalGastos)}
            </p>
          </div>
          <div className="bg-red-500 p-5 rounded-2xl shadow-lg">
            <TrendingDown className="w-8 h-8 text-white" strokeWidth={3} />
          </div>
        </div>
      </div>

      {/* Card Saldo */}
      <div className={`bg-gradient-to-br ${saldo >= 0 ? 'from-blue-50 to-blue-100 border-blue-200' : 'from-orange-50 to-orange-100 border-orange-200'} rounded-2xl p-8 shadow-lg border hover:shadow-xl transition-shadow`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${saldo >= 0 ? 'text-blue-700' : 'text-orange-700'} text-sm font-semibold mb-3 uppercase tracking-wide`}>Saldo Neto</p>
            <p className={`text-4xl font-bold ${saldo >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
              {formatCurrency(saldo)}
            </p>
          </div>
          <div className={`${saldo >= 0 ? 'bg-blue-500' : 'bg-orange-500'} p-5 rounded-2xl shadow-lg`}>
            <DollarSign className="w-8 h-8 text-white" strokeWidth={3} />
          </div>
        </div>
      </div>
    </div>
  );
}