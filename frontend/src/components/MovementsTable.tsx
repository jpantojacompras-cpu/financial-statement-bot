import React, { useState, useMemo } from 'react';
import { Download, Edit, Trash2 } from 'lucide-react';
import { useDateFilter } from '../context/DateFilterContext';

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

export default function MovementsTable({ movements }: MovementsTableProps) {
  const { selectedYear, selectedMonth } = useDateFilter();
  const [activeType, setActiveType] = useState<'all' | 'ingreso' | 'gasto'>('all');

  console.log('📊 MovementsTable filtros:', { selectedYear, selectedMonth, totalMovements: movements.length });

  // FILTRAR POR MES O AÑO
  const filteredByDate = useMemo(() => {
    if (selectedMonth) {
      return movements.filter(m => m.fecha.startsWith(selectedMonth));
    }
    if (selectedYear) {
      return movements.filter(m => m.fecha.startsWith(selectedYear));
    }
    return movements;
  }, [movements, selectedYear, selectedMonth]);

  console.log('📅 Después de filtrar por fecha:', filteredByDate.length);

  // FILTRAR POR TIPO
  const filtered = useMemo(() => {
    if (activeType === 'ingreso') {
      return filteredByDate.filter(m => m.tipo === 'ingreso');
    }
    if (activeType === 'gasto') {
      return filteredByDate.filter(m => m.tipo === 'gasto');
    }
    return filteredByDate;
  }, [filteredByDate, activeType]);

  console.log('💰 Después de filtrar por tipo:', filtered.length);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Tabla de Movimientos</h2>
          <p className="text-gray-600 mt-1">
            Mostrando {filtered.length} de {filteredByDate.length} movimientos
          </p>
          {selectedMonth && <p className="text-sm text-blue-600 font-semibold">Mes: {selectedMonth}</p>}
          {selectedYear && !selectedMonth && <p className="text-sm text-blue-600 font-semibold">Año: {selectedYear}</p>}
        </div>
        <button className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-semibold">
          <Download size={18} />
          Exportar CSV
        </button>
      </div>

      <div className="bg-white rounded-lg border border-gray-300 p-5 shadow-sm">
        <div className="flex gap-3 flex-wrap items-center">
          <label className="font-semibold text-gray-900">Filtro:</label>

          <button
            onClick={() => setActiveType('all')}
            className={`px-5 py-2 rounded-lg font-semibold border-2 transition-all ${
              activeType === 'all'
                ? 'bg-gray-900 text-white border-gray-900'
                : 'bg-white text-gray-900 border-gray-300'
            }`}
          >
            📊 Total ({filteredByDate.length})
          </button>

          <button
            onClick={() => setActiveType('ingreso')}
            className={`px-5 py-2 rounded-lg font-semibold border-2 transition-all ${
              activeType === 'ingreso'
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white text-green-700 border-green-300'
            }`}
          >
            💰 Ingresos ({filteredByDate.filter(m => m.tipo === 'ingreso').length})
          </button>

          <button
            onClick={() => setActiveType('gasto')}
            className={`px-5 py-2 rounded-lg font-semibold border-2 transition-all ${
              activeType === 'gasto'
                ? 'bg-red-600 text-white border-red-600'
                : 'bg-white text-red-700 border-red-300'
            }`}
          >
            📉 Gastos ({filteredByDate.filter(m => m.tipo === 'gasto').length})
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-500">Sin movimientos para mostrar</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Fecha</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Descripción</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Monto</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Tipo</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Categoría</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Archivo</th>
                  <th className="px-6 py-4 text-center text-sm font-semibold text-gray-900">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filtered.map((mov) => (
                  <tr key={mov.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {new Date(mov.fecha).toLocaleDateString('es-ES')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700 max-w-xs truncate">{mov.descripcion}</td>
                    <td className="px-6 py-4 text-sm font-bold text-right">
                      <span className={mov.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'}>
                        {mov.tipo === 'ingreso' ? '+' : '-'} ${mov.monto.toLocaleString('es-CL')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        mov.tipo === 'ingreso' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {mov.tipo === 'ingreso' ? '💰 Ingreso' : '📉 Gasto'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{mov.categoria}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{mov.archivo_referencia}</td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex justify-center gap-3">
                        <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                          <Edit size={18} />
                        </button>
                        <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}