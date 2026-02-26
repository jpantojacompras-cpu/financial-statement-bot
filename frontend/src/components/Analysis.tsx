import React, { useMemo } from 'react';
import { useDateFilter } from '../context/DateFilterContext';

interface Movement {
  fecha: string;
  monto: number;
  tipo: 'ingreso' | 'gasto';
  categoria: string;
}

interface AnalysisProps {
  movements: Movement[];
}

export default function Analysis({ movements }: AnalysisProps) {
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

  const analysis = useMemo(() => {
    const totalIngresos = filteredMovements
      .filter((m) => m.tipo === 'ingreso')
      .reduce((sum, m) => sum + m.monto, 0);

    const totalGastos = filteredMovements
      .filter((m) => m.tipo === 'gasto')
      .reduce((sum, m) => sum + m.monto, 0);

    const ratioGasto = totalIngresos > 0 ? (totalGastos / totalIngresos) * 100 : 0;
    
    const promediomovimiento = filteredMovements.length > 0 ? totalGastos / filteredMovements.length : 0;

    const movimientoMasAlto = filteredMovements.length > 0 
      ? filteredMovements.reduce((max, m) => m.monto > max.monto ? m : max, filteredMovements[0])
      : null;

    return {
      totalIngresos,
      totalGastos,
      ratioGasto,
      promediomovimiento,
      movimientoMasAlto,
    };
  }, [filteredMovements]);

  const formatCurrency = (value: number) => {
    return '$' + value.toLocaleString('es-CL');
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">📊 Índices Clave</h3>
          <div className="space-y-3">
            <div>
              <p className="text-gray-600 text-sm">% de Gastos sobre Ingresos</p>
              <p className="text-2xl font-bold text-purple-600">
                {analysis.ratioGasto.toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-gray-600 text-sm">Promedio por Movimiento</p>
              <p className="text-2xl font-bold text-blue-600">
                {formatCurrency(analysis.promediomovimiento)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">🔝 Mayor Movimiento</h3>
          {analysis.movimientoMasAlto ? (
            <div className="space-y-2">
              <p className="text-gray-600 text-sm">Monto</p>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(analysis.movimientoMasAlto.monto)}
              </p>
              <p className="text-gray-600 text-sm mt-3">Categoría</p>
              <p className="text-lg font-semibold">{analysis.movimientoMasAlto.categoria}</p>
            </div>
          ) : (
            <p className="text-gray-600">No hay movimientos</p>
          )}
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg shadow p-6 border-l-4 border-blue-500">
        <h3 className="text-lg font-semibold mb-2">💡 Análisis</h3>
        <p className="text-gray-700">
          {analysis.ratioGasto > 80
            ? '⚠️ Tus gastos son más del 80% de tus ingresos. Considera reducir gastos.'
            : analysis.ratioGasto > 50
            ? '📊 Tus gastos representan aproximadamente el 50-80% de tus ingresos. Está equilibrado.'
            : '✅ Excelente control de gastos. Estás ahorrando más del 50%.'}
        </p>
      </div>
    </div>
  );
}