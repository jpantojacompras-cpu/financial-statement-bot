import React, { createContext, useContext, useState } from 'react';

interface DateFilterContextType {
  selectedYear: string;
  selectedMonth: string;
  setSelectedYear: (year: string) => void;
  setSelectedMonth: (month: string) => void;
}

const DateFilterContext = createContext<DateFilterContextType | undefined>(undefined);

export function DateFilterProvider({ children }: { children: React.ReactNode }) {
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [selectedMonth, setSelectedMonth] = useState<string>('');

  return (
    <DateFilterContext.Provider
      value={{
        selectedYear,
        selectedMonth,
        setSelectedYear,
        setSelectedMonth,
      }}
    >
      {children}
    </DateFilterContext.Provider>
  );
}

export function useDateFilter() {
  const context = useContext(DateFilterContext);
  if (!context) {
    throw new Error('useDateFilter debe usarse dentro de DateFilterProvider');
  }
  return context;
}