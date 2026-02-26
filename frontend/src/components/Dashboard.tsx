import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { useDateFilter } from '../context/DateFilterContext';

interface Movement {
  fecha: string;
  monto: number;
  tipo: 'ingreso' | 'gasto';
  categoria: string;
}

interface DashboardProps {
  movements: Movement[];
}

export default function Dashboard({ movements }: DashboardProps) {
  const { selectedYear, selectedMonth, activeType } = useDateFilter();

  const filteredMovements = useMemo(() => {
    let filtered = movements;
    
    if (selectedYear) {
      filtered = filtered.filter((m) => m.fecha.startsWith(selectedYear));
    }
    
    if (selectedMonth && selectedYear) {
      filtered = filtered.filter((m) => m.fecha.startsWith(`${selectedYear}-${selectedMonth}`));
    }
    
    if (activeType !== 'all') {
      filtered = filtered.filter((m) => m.tipo === activeType);
    }
    
    return filtered;
  }, [movements, selectedYear, selectedMonth, activeType]);

  const stats = useMemo(() => {
    const totalIngresos = filteredMovements
      .filter((m) => m.tipo === 'ingreso')
      .reduce((sum, m) => sum + m.monto, 0);

    const totalGastos = filteredMovements
      .filter((m) => m.tipo === 'gasto')
      .reduce((sum, m) => sum + m.monto, 0);

    const saldo = totalIngresos - totalGastos;

    const categoriaGastos = filteredMovements
      .filter((m) => m.tipo === 'gasto')
      .reduce((acc, m) => {
        acc[m.categoria] = (acc[m.categoria] || 0) + m.monto;
        return acc;
      }, {} as Record<string, number>);

    return { totalIngresos, totalGastos, saldo, categoriaGastos };
  }, [filteredMovements]);

  const formatCurrency = (value: number) => {
    return '$' + value.toLocaleString('es-CL');
  };

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Total Ingresos</p>
              <p className="text-3xl font-bold text-green-600">
                {formatCurrency(stats.totalIngresos)}
              </p>
            </div>
            <TrendingUp className="text-green-500" size={40} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Total Gastos</p>
              <p className="text-3xl font-bold text-red-600">
                {formatCurrency(stats.totalGastos)}
              </p>
            </div>
            <TrendingDown className="text-red-500" size={40} />
          </div>
        </div>

        <div className={`bg-white rounded-lg shadow p-6 border-l-4 ${
          stats.saldo >= 0 ? 'border-blue-500' : 'border-orange-500'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Saldo</p>
              <p className={`text-3xl font-bold ${
                stats.saldo >= 0 ? 'text-blue-600' : 'text-orange-600'
              }`}>
                {formatCurrency(stats.saldo)}
              </p>
            </div>
            <DollarSign className={stats.saldo >= 0 ? 'text-blue-500' : 'text-orange-500'} size={40} />
          </div>
        </div>
      </div>

      {/* Gastos por categoría */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Gastos por Categoría</h2>
        {Object.keys(stats.categoriaGastos).length === 0 ? (
          <p className="text-gray-600">No hay datos de gastos</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(stats.categoriaGastos).map(([categoria, monto]) => (
              <div key={categoria} className="flex justify-between items-center">
                <span className="text-gray-700 font-medium">{categoria}</span>
                <div className="flex items-center gap-3">
                  <div className="w-48 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${stats.totalGastos > 0 ? (monto / stats.totalGastos) * 100 : 0}%`,
                      }}
                    ></div>
                  </div>
                  <span className="font-semibold text-right w-24 text-red-600">
                    {formatCurrency(monto)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}