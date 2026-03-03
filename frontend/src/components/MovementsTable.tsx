import React, { useMemo, useState } from 'react';
import { useDateFilter } from '../context/DateFilterContext';
import { ChevronDown } from 'lucide-react';

interface Movement {
  id: number;
  fecha: string;
  descripcion: string;
  monto: number;
  tipo: 'ingreso' | 'gasto';
  archivo_referencia: string;
  categoria: string;
  subcategoria: string;
}

interface MovementsTableProps {
  movements: Movement[];
}

type SortField = 'fecha' | 'monto' | 'tipo' | 'categoria' | 'none';
type SortDirection = 'asc' | 'desc';

export default function MovementsTable({ movements }: MovementsTableProps) {
  const { selectedYear, selectedMonth, activeType } = useDateFilter();
  const [sortField, setSortField] = useState<SortField>('fecha');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const filteredMovements = useMemo(() => {
    let filtered = [...movements];

    // Filtro por año
    if (selectedYear) {
      filtered = filtered.filter((m) => m.fecha.startsWith(selectedYear));
    }

    // Filtro por mes
    if (selectedMonth && selectedYear) {
      const monthFilter = `${selectedYear}-${selectedMonth}`;
      filtered = filtered.filter((m) => m.fecha.startsWith(monthFilter));
    }

    // Filtro por tipo
    if (activeType !== 'all') {
      filtered = filtered.filter((m) => m.tipo === activeType);
    }

    // ORDENAMIENTO
    if (sortField !== 'none') {
      filtered.sort((a, b) => {
        let aValue: any;
        let bValue: any;

        switch (sortField) {
          case 'fecha':
            aValue = new Date(a.fecha).getTime();
            bValue = new Date(b.fecha).getTime();
            break;
          case 'monto':
            aValue = a.monto;
            bValue = b.monto;
            break;
          case 'tipo':
            aValue = a.tipo;
            bValue = b.tipo;
            break;
          case 'categoria':
            aValue = a.categoria.toLowerCase();
            bValue = b.categoria.toLowerCase();
            break;
          default:
            return 0;
        }

        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [movements, selectedYear, selectedMonth, activeType, sortField, sortDirection]);

  const totalIngresos = filteredMovements
    .filter((m) => m.tipo === 'ingreso')
    .reduce((sum, m) => sum + (m.monto || 0), 0);

  const totalGastos = filteredMovements
    .filter((m) => m.tipo === 'gasto')
    .reduce((sum, m) => sum + (m.monto || 0), 0);

  const saldo = totalIngresos - totalGastos;

  const formatCurrency = (value: number) => {
    return '$' + value.toLocaleString('es-CL');
  };

  const getTipoTexto = (tipo: string) => {
    return tipo === 'ingreso' ? 'Ingreso' : 'Gasto';
  };

  const getUniqueKey = (mov: Movement, index: number) => {
    return `${mov.fecha}-${mov.monto}-${mov.tipo}-${index}`;
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Si hace click en el mismo campo, cambiar dirección
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Si hace click en un campo diferente, ordenar ascendente
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => {
    const isActive = sortField === field;
    const arrow = sortDirection === 'asc' ? '↑' : '↓';

    return (
      <th
        className="px-6 py-3 text-left text-sm font-semibold cursor-pointer hover:bg-gray-200 transition-colors"
        onClick={() => handleSort(field)}
      >
        <div className="flex items-center gap-2">
          {label}
          {isActive && <span className="text-blue-600">{arrow}</span>}
        </div>
      </th>
    );
  };

  if (filteredMovements.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <p className="text-gray-600 text-lg">No hay movimientos para mostrar</p>
        <p className="text-gray-500 text-sm mt-2">
          Año: {selectedYear || 'Todos'} | Mes: {selectedMonth || 'Todos'} | Tipo: {activeType === 'all' ? 'Todos' : activeType}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Opciones de ordenamiento */}
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-sm font-semibold text-gray-700 mb-3">Ordenar por:</p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleSort('fecha')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              sortField === 'fecha'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Fecha {sortField === 'fecha' && (sortDirection === 'asc' ? '↑' : '↓')}
          </button>
          <button
            onClick={() => handleSort('monto')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              sortField === 'monto'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Monto {sortField === 'monto' && (sortDirection === 'asc' ? '↑' : '↓')}
          </button>
          <button
            onClick={() => handleSort('tipo')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              sortField === 'tipo'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Tipo {sortField === 'tipo' && (sortDirection === 'asc' ? '↑' : '↓')}
          </button>
          <button
            onClick={() => handleSort('categoria')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              sortField === 'categoria'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Categoría {sortField === 'categoria' && (sortDirection === 'asc' ? '↑' : '↓')}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-100 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">Fecha</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Descripción</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Monto</th>
              <th className="px-6 py-3 text-center text-sm font-semibold">Tipo</th>
              <th className="px-6 py-3 text-left text-sm font-semibold">Categoría</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {filteredMovements.map((mov, index) => (
              <tr key={getUniqueKey(mov, index)} className="hover:bg-gray-50">
                <td className="px-6 py-3 text-sm text-gray-700">{mov.fecha}</td>
                <td className="px-6 py-3 text-sm text-gray-700">{mov.descripcion}</td>
                <td
                  className={`px-6 py-3 text-sm font-semibold text-right ${
                    mov.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {formatCurrency(mov.monto)}
                </td>
                <td className="px-6 py-3 text-sm text-center">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      mov.tipo === 'ingreso'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {getTipoTexto(mov.tipo)}
                  </span>
                </td>
                <td className="px-6 py-3 text-sm text-gray-700">{mov.categoria}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">Total Ingresos</p>
          <p className="text-3xl font-bold text-green-600">{formatCurrency(totalIngresos)}</p>
          <p className="text-xs text-gray-500 mt-2">{filteredMovements.filter(m => m.tipo === 'ingreso').length} movimientos</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">Total Gastos</p>
          <p className="text-3xl font-bold text-red-600">{formatCurrency(totalGastos)}</p>
          <p className="text-xs text-gray-500 mt-2">{filteredMovements.filter(m => m.tipo === 'gasto').length} movimientos</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">Saldo</p>
          <p className={`text-3xl font-bold ${saldo >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
            {formatCurrency(saldo)}
          </p>
          <p className="text-xs text-gray-500 mt-2">{filteredMovements.length} movimientos totales</p>
        </div>
      </div>
    </div>
  );
}