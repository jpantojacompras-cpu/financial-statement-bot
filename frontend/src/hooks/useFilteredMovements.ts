import { useMemo } from 'react';
import { useDateFilter } from '../context/DateFilterContext';

interface Movement {
  id: string | number;
  fecha: string;
  descripcion: string;
  monto: number;
  tipo: 'ingreso' | 'gasto';
  archivo_referencia: string;
  categoria: string;
  subcategoria: string;
}

export function useFilteredMovements(movements: Movement[] | undefined) {
  const { selectedYear, selectedMonth, selectedType } = useDateFilter();

  return useMemo(() => {
    // ✅ Validar que movements sea un array
    if (!Array.isArray(movements)) {
      return [];
    }

    return movements.filter((movement) => {
      // Validar que movement tenga las propiedades requeridas
      if (!movement || !movement.fecha) {
        return false;
      }

      // Filtrar por año
      if (selectedYear && selectedYear !== 'Todos') {
        const movementYear = movement.fecha.substring(0, 4);
        if (movementYear !== selectedYear) {
          return false;
        }
      }

      // Filtrar por mes
      if (selectedMonth && selectedMonth !== 'Todos') {
        const movementMonth = movement.fecha.substring(5, 7);
        if (movementMonth !== selectedMonth) {
          return false;
        }
      }

      // Filtrar por tipo
      if (selectedType && selectedType !== 'Todos') {
        if (movement.tipo !== selectedType) {
          return false;
        }
      }

      return true;
    });
  }, [movements, selectedYear, selectedMonth, selectedType]);
}