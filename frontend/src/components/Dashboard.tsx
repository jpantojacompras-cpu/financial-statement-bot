import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Percent } from 'lucide-react';
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

interface DashboardProps {
  movements: Movement[];
}

export default function Dashboard({ movements }: DashboardProps) {
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

  const stats = useMemo(() => {
    const totalIngresos = filteredMovements
      .filter((m) => m.tipo === 'ingreso')
      .reduce((sum, m) => sum + m.monto, 0);

    const totalGastos = filteredMovements
      .filter((m) => m.tipo === 'gasto')
      .reduce((sum, m) => sum + m.monto, 0);

    const balance = totalIngresos - totalGastos;
    const ratio = totalIngresos > 0 ? ((totalGastos / totalIngresos) * 100).toFixed(1) : '0';

    return {
      totalIngresos,
      totalGastos,
      balance,
      ratio: parseFloat(ratio),
      cantidad: filteredMovements.length,
    };
  }, [filteredMovements]);

  const topCategories = useMemo(() => {
    const categoryMap = new Map<string, number>();

    filteredMovements
      .filter((m) => m.tipo === 'gasto')
      .forEach((m) => {
        const category = m.categoria === 'Sin Categoría' ? m.descripcion.substring(0, 20) : m.categoria;
        categoryMap.set(category, (categoryMap.get(category) || 0) + m.monto);
      });

    return Array.from(categoryMap.entries())
      .map(([category, amount]) => ({ category, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);
  }, [filteredMovements]);

  // Evolución diaria - TODOS LOS DÍAS
  const dailyEvolution = useMemo(() => {
    const dailyMap = new Map<string, { ingresos: number; gastos: number }>();

    filteredMovements.forEach((mov) => {
      const date = mov.fecha;
      if (!dailyMap.has(date)) {
        dailyMap.set(date, { ingresos: 0, gastos: 0 });
      }

      const daily = dailyMap.get(date)!;
      if (mov.tipo === 'ingreso') {
        daily.ingresos += mov.monto;
      } else {
        daily.gastos += mov.monto;
      }
    });

    return Array.from(dailyMap.entries())
      .map(([date, values]) => ({
        date,
        ...values,
        balance: values.ingresos - values.gastos,
      }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [filteredMovements]);

  // Gráfico diario (últimos 30 días)
  const chartData = useMemo(() => {
    const last30Days = dailyEvolution.slice(-30);
    
    return {
      dates: last30Days.map((d) => {
        const date = new Date(d.date);
        return `${date.getDate()}/${date.getMonth() + 1}`;
      }),
      ingresos: last30Days.map((d) => d.ingresos),
      gastos: last30Days.map((d) => d.gastos),
      balance: last30Days.map((d) => d.balance),
    };
  }, [dailyEvolution]);

  const maxValue = useMemo(() => {
    const allValues = [...chartData.ingresos, ...chartData.gastos];
    return Math.max(...allValues, 1);
  }, [chartData]);

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

      {/* Cards de estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Ingresos */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Total Ingresos</p>
              <p className="text-2xl font-bold text-green-600">
                ${stats.totalIngresos.toLocaleString('es-CL')}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                {filteredMovements.filter((m) => m.tipo === 'ingreso').length} transacciones
              </p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <TrendingUp size={24} className="text-green-600" />
            </div>
          </div>
        </div>

        {/* Total Gastos */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Total Gastos</p>
              <p className="text-2xl font-bold text-red-600">
                ${stats.totalGastos.toLocaleString('es-CL')}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                {filteredMovements.filter((m) => m.tipo === 'gasto').length} transacciones
              </p>
            </div>
            <div className="bg-red-100 p-3 rounded-full">
              <TrendingDown size={24} className="text-red-600" />
            </div>
          </div>
        </div>

        {/* Balance */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Balance</p>
              <p
                className={`text-2xl font-bold ${
                  stats.balance >= 0 ? 'text-blue-600' : 'text-orange-600'
                }`}
              >
                ${stats.balance.toLocaleString('es-CL')}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                {stats.balance >= 0 ? '✅ Positivo' : '⚠️ Negativo'}
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <DollarSign size={24} className="text-blue-600" />
            </div>
          </div>
        </div>

        {/* Ratio Gasto/Ingreso */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-1">Ratio Gasto/Ingreso</p>
              <p className="text-2xl font-bold text-purple-600">{stats.ratio}%</p>
              <p className="text-xs text-gray-500 mt-2">
                {stats.ratio <= 50
                  ? '✅ Excelente'
                  : stats.ratio <= 80
                  ? '👍 Bueno'
                  : '⚠️ Alto'}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <Percent size={24} className="text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico Diario */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-6">
          📊 Gráfico Diario (Últimos 30 días)
        </h2>

        {chartData.dates.length === 0 ? (
          <p className="text-gray-600 text-center py-8">Sin datos para mostrar</p>
        ) : (
          <div className="overflow-x-auto pb-4">
            <div className="flex gap-2 min-w-min" style={{ height: '300px' }}>
              {chartData.dates.map((date, idx) => {
                const ingresoHeight = (chartData.ingresos[idx] / maxValue) * 100;
                const gastoHeight = (chartData.gastos[idx] / maxValue) * 100;

                return (
                  <div
                    key={idx}
                    className="flex flex-col items-center gap-2"
                    style={{ minWidth: '60px' }}
                  >
                    {/* Barra de ingresos */}
                    <div className="relative w-full flex items-end justify-center gap-1" style={{ height: '240px' }}>
                      <div
                        className="bg-green-500 rounded-t-sm transition-all hover:bg-green-600"
                        style={{
                          width: '16px',
                          height: `${ingresoHeight}%`,
                        }}
                        title={`Ingresos: $${chartData.ingresos[idx].toLocaleString('es-CL')}`}
                      />
                      <div
                        className="bg-red-500 rounded-t-sm transition-all hover:bg-red-600"
                        style={{
                          width: '16px',
                          height: `${gastoHeight}%`,
                        }}
                        title={`Gastos: $${chartData.gastos[idx].toLocaleString('es-CL')}`}
                      />
                    </div>
                    {/* Fecha */}
                    <span className="text-xs text-gray-600 text-center whitespace-nowrap">
                      {date}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Leyenda */}
        <div className="flex gap-6 mt-6 pt-6 border-t border-gray-200 justify-center">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-sm text-gray-700">Ingresos</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-sm text-gray-700">Gastos</span>
          </div>
        </div>
      </div>

      {/* Top Categorías */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Top 5 Categorías de Gasto</h2>
        <div className="space-y-3">
          {topCategories.length > 0 ? (
            topCategories.map((cat, idx) => {
              const percentage = (cat.amount / stats.totalGastos) * 100;
              return (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-gray-700">{cat.category}</span>
                    <span className="text-sm font-bold text-gray-900">
                      ${cat.amount.toLocaleString('es-CL')}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-500 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">{percentage.toFixed(1)}%</div>
                </div>
              );
            })
          ) : (
            <p className="text-gray-600">Sin gastos registrados</p>
          )}
        </div>
      </div>

      {/* Evolución Diaria - TODOS LOS DÍAS */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Evolución Diaria (Todos los días)
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left font-semibold text-gray-900 py-3 px-4">Fecha</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Ingresos</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Gastos</th>
                <th className="text-right font-semibold text-gray-900 py-3 px-4">Balance</th>
                <th className="text-center font-semibold text-gray-900 py-3 px-4">Movimientos</th>
              </tr>
            </thead>
            <tbody>
              {dailyEvolution.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-6 text-gray-600">
                    Sin datos para mostrar
                  </td>
                </tr>
              ) : (
                dailyEvolution.map((day, idx) => {
                  const movementCount = filteredMovements.filter((m) => m.fecha === day.date).length;
                  return (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">
                        {new Date(day.date).toLocaleDateString('es-ES', {
                          weekday: 'short',
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                        })}
                      </td>
                      <td className="text-right py-3 px-4">
                        <span className="text-green-600 font-semibold">
                          ${day.ingresos.toLocaleString('es-CL')}
                        </span>
                      </td>
                      <td className="text-right py-3 px-4">
                        <span className="text-red-600 font-semibold">
                          ${day.gastos.toLocaleString('es-CL')}
                        </span>
                      </td>
                      <td className="text-right py-3 px-4">
                        <span
                          className={`font-semibold ${
                            day.balance >= 0 ? 'text-blue-600' : 'text-orange-600'
                          }`}
                        >
                          ${day.balance.toLocaleString('es-CL')}
                        </span>
                      </td>
                      <td className="text-center py-3 px-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {movementCount}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {dailyEvolution.length > 0 && (
          <p className="text-xs text-gray-600 mt-4">
            Mostrando {dailyEvolution.length} días con movimientos
          </p>
        )}
      </div>
    </div>
  );
}