import React, { createContext, useContext, useState, ReactNode } from 'react';

interface DateFilterContextType {
  selectedYear: string;
  setSelectedYear: (year: string) => void;
  selectedMonth: string;
  setSelectedMonth: (month: string) => void;
}

const DateFilterContext = createContext<DateFilterContextType | undefined>(undefined);

export function DateFilterProvider({ children }: { children: ReactNode }) {
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedMonth, setSelectedMonth] = useState('');

  console.log('DateFilterProvider state:', { selectedYear, selectedMonth });

  return (
    <DateFilterContext.Provider
      value={{
        selectedYear,
        setSelectedYear,
        selectedMonth,
        setSelectedMonth,
      }}
    >
      {children}
    </DateFilterContext.Provider>
  );
}

export function useDateFilter(): DateFilterContextType {
  const context = useContext(DateFilterContext);
  if (!context) {
    throw new Error('useDateFilter debe usarse dentro de DateFilterProvider');
  }
  return context;
}