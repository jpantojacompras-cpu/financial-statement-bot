import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts';

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

interface AnalyticsProps {
  movements: Movement[];
  categories: Record<string, string[]>;
}

export default function Analytics({ movements }: AnalyticsProps) {
  const categoryAnalysis = useMemo(() => {
    const data: Record<
      string,
      { gastos: number; ingresos: number; movimientos: number }
    > = {};

    movements.forEach((m) => {
      const cat = m.categoria === 'Sin Categoría' ? 'Otros' : m.categoria;
      if (!data[cat]) {
        data[cat] = { gastos: 0, ingresos: 0, movimientos: 0 };
      }

      if (m.tipo === 'ingreso') {
        data[cat].ingresos += m.monto;
      } else {
        data[cat].gastos += m.monto;
      }
      data[cat].movimientos += 1;
    });

    return Object.entries(data)
      .map(([name, value]) => ({
        nombre: name,
        ...value,
      }))
      .sort((a, b) => b.gastos - a.gastos);
  }, [movements]);

  const dailyStats = useMemo(() => {
    const data: Record<string, { ingreso: number; gasto: number }> = {};

    movements.forEach((m) => {
      if (!data[m.fecha]) {
        data[m.fecha] = { ingreso: 0, gasto: 0 };
      }

      if (m.tipo === 'ingreso') {
        data[m.fecha].ingreso += m.monto;
      } else {
        data[m.fecha].gasto += m.monto;
      }
    });

    return Object.entries(data)
      .sort()
      .slice(-30)
      .map(([fecha, value]) => ({
        fecha,
        ...value,
      }));
  }, [movements]);

  return (
    <div className="space-y-6">
      {/* Category Analysis */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          🎯 Análisis por Categoría
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold">Categoría</th>
                <th className="px-6 py-3 text-right text-sm font-semibold">Gastos</th>
                <th className="px-6 py-3 text-right text-sm font-semibold">Ingresos</th>
                <th className="px-6 py-3 text-right text-sm font-semibold">Movimientos</th>
                <th className="px-6 py-3 text-right text-sm font-semibold">Promedio</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {categoryAnalysis.map((cat) => (
                <tr key={cat.nombre}>
                  <td className="px-6 py-4 font-semibold">{cat.nombre}</td>
                  <td className="px-6 py-4 text-right text-red-600">
                    ${cat.gastos.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right text-green-600">
                    ${cat.ingresos.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right">{cat.movimientos}</td>
                  <td className="px-6 py-4 text-right">
                    ${((cat.gastos + cat.ingresos) / cat.movimientos).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Daily Trend */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          📉 Últimos 30 días
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dailyStats}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="fecha" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="ingreso" fill="#10B981" />
            <Bar dataKey="gasto" fill="#EF4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}