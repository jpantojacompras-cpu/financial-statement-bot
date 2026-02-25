import React, { useMemo } from 'react';
import { Calendar } from 'lucide-react';
import { useDateFilter } from '../context/DateFilterContext';

interface Movement {
  fecha: string;
}

interface DateFilterProps {
  movements: Movement[];
}

export default function DateFilter({ movements }: DateFilterProps) {
  const { selectedYear, setSelectedYear, selectedMonth, setSelectedMonth } = useDateFilter();

  console.log('DateFilter - Current state:', { selectedYear, selectedMonth });

  const years = useMemo(() => {
    const yearSet = new Set(movements.map(m => m.fecha.substring(0, 4)));
    return Array.from(yearSet).sort().reverse();
  }, [movements]);

  const months = useMemo(() => {
    if (!selectedYear) return [];
    const monthSet = new Set(
      movements
        .filter(m => m.fecha.startsWith(selectedYear))
        .map(m => m.fecha.substring(0, 7))
    );
    return Array.from(monthSet).sort().reverse();
  }, [movements, selectedYear]);

  const monthNames: { [key: string]: string } = {
    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre',
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const year = e.target.value;
    console.log('🔄 Year changed to:', year);
    setSelectedYear(year);
    setSelectedMonth('');
  };

  const handleMonthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const month = e.target.value;
    console.log('🔄 Month changed to:', month);
    setSelectedMonth(month);
  };

  return (
    <div className="flex items-center gap-3">
      <Calendar size={20} className="text-gray-600" />
      
      <select
        value={selectedYear}
        onChange={handleYearChange}
        className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-900 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
      >
        <option value="">Todos los años</option>
        {years.map(year => (
          <option key={year} value={year}>
            {year}
          </option>
        ))}
      </select>

      {selectedYear && (
        <select
          value={selectedMonth}
          onChange={handleMonthChange}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-900 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
        >
          <option value="">Todos los meses</option>
          {months.map(month => {
            const [year, monthNum] = month.split('-');
            return (
              <option key={month} value={month}>
                {monthNames[monthNum]} {year}
              </option>
            );
          })}
        </select>
      )}
    </div>
  );
}