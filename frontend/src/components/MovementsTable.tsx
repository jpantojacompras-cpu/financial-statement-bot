import React, { useMemo } from 'react';
import { useContext } from 'react';
import { DateFilterContext } from '../context/DateFilterContext';

interface MovementRow {
  id: string;
  patente: string;
  date: string;
  final: number;
  activeType: string;
}

export const MovementsTable: React.FC = () => {
  const { selectedYear, selectedMonth, activeType } = useContext(DateFilterContext);

  // Mock data - Replace with actual data
  const mockData: MovementRow[] = [
    { id: '1', patente: 'ABC123', date: '2024-01-15', final: 100, activeType: 'all' },
    { id: '2', patente: 'DEF456', date: '2024-02-20', final: 250, activeType: 'all' },
    // ... more rows
  ];

  const filteredData = useMemo(() => {
    console.log('📊 MovementsTable filtros:', {
      selectedYear,
      selectedMonth,
      totalMovements: mockData.length,
    });

    let filtered = mockData;

    // Filter by year
    if (selectedYear) {
      filtered = filtered.filter((item) => item.date.startsWith(selectedYear));
      console.log('📅 Después de filtrar por fecha:', filtered.length);
    }

    // Filter by type
    if (activeType !== 'all') {
      filtered = filtered.filter((item) => item.activeType === activeType);
      console.log('💰 Después de filtrar por tipo:', filtered.length);
    }

    return filtered;
  }, [selectedYear, selectedMonth, activeType]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-4 py-2 text-left">Patente</th>
            <th className="px-4 py-2 text-left">Fecha</th>
            <th className="px-4 py-2 text-right">Final</th>
          </tr>
        </thead>
        <tbody>
          {filteredData.map((movement) => (
            // CAMBIO IMPORTANTE: Usa el id único del movimiento, no el índice
            <tr key={movement.id} className="border-b hover:bg-gray-50">
              <td className="px-4 py-2">{movement.patente}</td>
              <td className="px-4 py-2">{movement.date}</td>
              <td className="px-4 py-2 text-right">{movement.final}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};