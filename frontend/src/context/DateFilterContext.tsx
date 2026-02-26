import React, { createContext, useState, ReactNode, useContext } from 'react';

interface DateFilterContextType {
  selectedYear: string | null;
  selectedMonth: string | null;
  activeType: string;
  setSelectedYear: (year: string | null) => void;
  setSelectedMonth: (month: string | null) => void;
  setActiveType: (type: string) => void;
}

export const DateFilterContext = createContext<DateFilterContextType | undefined>(undefined);

export function DateFilterProvider({ children }: { children: ReactNode }) {
  const [selectedYear, setSelectedYear] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<string>('all');

  return (
    <DateFilterContext.Provider 
      value={{ 
        selectedYear, 
        selectedMonth, 
        activeType, 
        setSelectedYear, 
        setSelectedMonth, 
        setActiveType 
      }}
    >
      {children}
    </DateFilterContext.Provider>
  );
}

// Hook personalizado para usar el contexto
export function useDateFilter() {
  const context = useContext(DateFilterContext);
  
  if (!context) {
    throw new Error('useDateFilter debe usarse dentro de DateFilterProvider');
  }
  
  return context;
}