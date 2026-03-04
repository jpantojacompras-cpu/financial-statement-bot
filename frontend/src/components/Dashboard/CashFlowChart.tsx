import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Movement } from '../../types/Movement';

interface CashFlowChartProps {
  movements: Movement[];
}

const getCashFlowByMonth = (movements: Movement[]) => {
  const monthData: { [key: string]: { ingresos: number; gastos: number } } = {};

  movements.forEach(m => {
    const date = new Date(m.fecha);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    
    if (!monthData[monthKey]) {
      monthData[monthKey] = { ingresos: 0, gastos: 0 };
    }

    if (m.tipo === 'ingreso') {
      monthData[monthKey].ingresos += m.monto;
    } else {
      monthData[monthKey].gastos += m.monto;
    }
  });

  return Object.entries(monthData)
    .sort()
    .map(([month, data]) => ({
      mes: month,
      Ingresos: data.ingresos,
      Gastos: data.gastos,
      Saldo: data.ingresos - data.gastos,
    }));
};

const CustomTooltip = (props: any) => {
  const { active, payload } = props;
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-900">{payload[0].payload.mes}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }} className="font-medium">
            {entry.name}: ${new Intl.NumberFormat('es-CL').format(entry.value)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function CashFlowChart({ movements }: CashFlowChartProps) {
  const data = getCashFlowByMonth(movements);

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-8 shadow-lg text-center">
        <p className="text-gray-500">No hay datos para mostrar</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-8 shadow-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">💰 Flujo de Caja por Mes</h2>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="mes" 
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <YAxis 
            tick={{ fill: '#6b7280', fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          <Bar dataKey="Ingresos" fill="#10b981" radius={[12, 12, 0, 0]} />
          <Bar dataKey="Gastos" fill="#ef4444" radius={[12, 12, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}