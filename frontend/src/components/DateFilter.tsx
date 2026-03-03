import React from 'react';
import { useDateFilter } from '../context/DateFilterContext';

interface Movement {
  fecha: string;
  tipo: 'ingreso' | 'gasto';
}

interface DateFilterProps {
  movements: Movement[];
}

export default function DateFilter({ movements }: DateFilterProps) {
  const { selectedYear, selectedMonth, activeType, setSelectedYear, setSelectedMonth, setActiveType } = useDateFilter();

  // Extraer años únicos
  const years = [...new Set(movements.map((m) => m.fecha.substring(0, 4)))].sort().reverse();

  // Extraer meses para el año seleccionado
  const months = selectedYear 
    ? [...new Set(
        movements
          .filter((m) => m.fecha.startsWith(selectedYear))
          .map((m) => m.fecha.substring(5, 7))
      )].sort()
    : [];

  const monthNames: Record<string, string> = {
    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
  };

  return (
    <div className="flex items-center gap-4 flex-wrap">
      {/* Filtro de Año */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Año:</label>
        <select
          value={selectedYear || ''}
          onChange={(e) => {
            setSelectedYear(e.target.value || null);
            setSelectedMonth(null); // Reset mes cuando cambias año
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
        >
          <option value="">Todos</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>

      {/* Filtro de Mes (solo si hay año seleccionado) */}
      {selectedYear && months.length > 0 && (
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Mes:</label>
          <select
            value={selectedMonth || ''}
            onChange={(e) => setSelectedMonth(e.target.value || null)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
          >
            <option value="">Todos</option>
            {months.map((month) => (
              <option key={month} value={month}>
                {monthNames[month]}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Filtro de Tipo */}
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium text-gray-700">Tipo:</label>
        <select
          value={activeType}
          onChange={(e) => setActiveType(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
        >
          <option value="all">Todos</option>
          <option value="ingreso">Ingresos</option>
          <option value="gasto">Gastos</option>
        </select>
      </div>
    </div>
  );
}