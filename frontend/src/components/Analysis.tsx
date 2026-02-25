import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
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

interface AnalysisProps {
  movements: Movement[];
}

export default function Analysis({ movements }: AnalysisProps) {
  const { selectedYear, selectedMonth } = useDateFilter();

  const filteredMovements = useMemo(() => {
    return movements.filter((mov) => {
      if (selectedMonth) {
        return mov.fecha.startsWith(selectedMonth);
      }
      if (selectedYear) {
        return mov.fecha.startsWith(selectedYear);
      }
      return true;
    });
  }, [movements, selectedYear, selectedMonth]);

  const monthLabels: { [key: string]: string } = {
    '01': 'Enero',
    '02': 'Febrero',
    '03': 'Marzo',
    '04': 'Abril',
    '05': 'Mayo',
    '06': 'Junio',
    '07': 'Julio',
    '08': 'Agosto',
    '09': 'Septiembre',
    '10': 'Octubre',
    '11': 'Noviembre',
    '12': 'Diciembre',
  };

  const filterLabel = useMemo(() => {
    if (selectedMonth) {
      const [year, month] = selectedMonth.split('-');
      return `${monthLabels[month]} ${year}`;
    }
    if (selectedYear) {
      return `Año ${selectedYear}`;
    }
    return 'Todos los períodos';
  }, [selectedYear, selectedMonth]);

  const categoryAnalysis = useMemo(() => {
    const categoryMap = new Map<string, { ingresos: number; gastos: number; count: number }>();

    filteredMovements.forEach((mov) => {
      const cat = mov.categoria === 'Sin Categoría' ? mov.descripcion.substring(0, 20) : mov.categoria;
      if (!categoryMap.has(cat)) {
        categoryMap.set(cat, { ingresos: 0, gastos: 0, count: 0 });
      }

      const catData = categoryMap.get(cat)!;
      if (mov.tipo === 'ingreso') {
        catData.ingresos += mov.monto;
      } else {
        catData.gastos += mov.monto;
      }
      catData.count += 1;
    });

    return Array.from(categoryMap.entries())
      .map(([cat, data]) => ({
        categoria: cat,
        ...data,
        balance: data.ingresos - data.gastos,
      }))
      .sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance));
  }, [filteredMovements]);

  const topExpenses = useMemo(() => {
    return filteredMovements
      .filter((m) => m.tipo === 'gasto')
      .sort((a, b) => b.monto - a.monto)
      .slice(0, 10);
  }, [filteredMovements]);

  const topIncomes = useMemo(() => {
    return filteredMovements
      .filter((m) => m.tipo === 'ingreso')
      .sort((a, b) => b.monto - a.monto)
      .slice(0, 10);
  }, [filteredMovements]);

  return (
    <div className="space-y-6">
      {/* Filtro activo */}
      {(selectedMonth || selectedYear) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-900 font-semibold">
            📅 Filtro activo: {filterLabel}
          </p>
        </div>
      )}

      {/* Análisis por Categoría */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Análisis por Categoría</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left font-semibold text-gray-900 py-3 px-4">Categoría</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Ingresos</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Gastos</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Balance</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Cantidad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {categoryAnalysis.map((cat, idx) => (
                <tr key={idx} className="hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-4 font-medium text-gray-900">{cat.categoria}</td>
                  <td className="text-right py-3 px-4">
                    <span className="text-green-600 font-semibold">
                      ${cat.ingresos.toLocaleString('es-CL')}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4">
                    <span className="text-red-600 font-semibold">
                      ${cat.gastos.toLocaleString('es-CL')}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4">
                    <span
                      className={`font-semibold ${
                        cat.balance >= 0 ? 'text-blue-600' : 'text-orange-600'
                      }`}
                    >
                      ${cat.balance.toLocaleString('es-CL')}
                    </span>
                  </td>
                  <td className="text-right py-3 px-4 text-gray-600">{cat.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Gastos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingDown size={24} className="text-red-600" />
            <h2 className="text-xl font-bold text-gray-900">Top 10 Gastos</h2>
          </div>
          <div className="space-y-2">
            {topExpenses.map((mov, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-red-50 rounded">
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 text-sm truncate">{mov.descripcion}</p>
                  <p className="text-xs text-gray-600">
                    {new Date(mov.fecha).toLocaleDateString('es-ES')}
                  </p>
                </div>
                <span className="text-red-600 font-bold ml-2 whitespace-nowrap">
                  ${mov.monto.toLocaleString('es-CL')}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Ingresos */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={24} className="text-green-600" />
            <h2 className="text-xl font-bold text-gray-900">Top 10 Ingresos</h2>
          </div>
          <div className="space-y-2">
            {topIncomes.map((mov, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-green-50 rounded">
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 text-sm truncate">{mov.descripcion}</p>
                  <p className="text-xs text-gray-600">
                    {new Date(mov.fecha).toLocaleDateString('es-ES')}
                  </p>
                </div>
                <span className="text-green-600 font-bold ml-2 whitespace-nowrap">
                  ${mov.monto.toLocaleString('es-CL')}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Distribución por Archivo */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Distribución por Archivo</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left font-semibold text-gray-900 py-3 px-4">Archivo</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Movimientos</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Ingresos</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Gastos</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {Array.from(
                new Map(
                  filteredMovements.map((m) => [
                    m.archivo_referencia,
                    {
                      count: filteredMovements.filter((x) => x.archivo_referencia === m.archivo_referencia)
                        .length,
                      ingresos: filteredMovements
                        .filter((x) => x.archivo_referencia === m.archivo_referencia && x.tipo === 'ingreso')
                        .reduce((sum, x) => sum + x.monto, 0),
                      gastos: filteredMovements
                        .filter((x) => x.archivo_referencia === m.archivo_referencia && x.tipo === 'gasto')
                        .reduce((sum, x) => sum + x.monto, 0),
                    },
                  ])
                ).values()
              ).map((file, idx) => {
                const fileName = Array.from(
                  new Map(
                    filteredMovements.map((m) => [
                      m.archivo_referencia,
                      {
                        count: filteredMovements.filter((x) => x.archivo_referencia === m.archivo_referencia)
                          .length,
                        ingresos: filteredMovements
                          .filter((x) => x.archivo_referencia === m.archivo_referencia && x.tipo === 'ingreso')
                          .reduce((sum, x) => sum + x.monto, 0),
                        gastos: filteredMovements
                          .filter((x) => x.archivo_referencia === m.archivo_referencia && x.tipo === 'gasto')
                          .reduce((sum, x) => sum + x.monto, 0),
                      },
                    ])
                  ).keys()
                )[idx];

                return (
                  <tr key={idx} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 font-medium text-gray-900 text-xs">{fileName}</td>
                    <td className="text-right py-3 px-4 text-gray-600">{file.count}</td>
                    <td className="text-right py-3 px-4">
                      <span className="text-green-600 font-semibold">
                        ${file.ingresos.toLocaleString('es-CL')}
                      </span>
                    </td>
                    <td className="text-right py-3 px-4">
                      <span className="text-red-600 font-semibold">
                        ${file.gastos.toLocaleString('es-CL')}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}