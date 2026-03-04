import React, { useState, useEffect } from 'react';
import { Movement } from '../types/Movement';
import { useFilteredMovements } from '../hooks/useFilteredMovements';
import KPICards from '../components/Dashboard/KPICards';
import CashFlowChart from '../components/Dashboard/CashFlowChart';
import CategoryBreakdown from '../components/Dashboard/CategoryBreakdown';
import CategorizeMovements from '../components/CategorizeMovements';

interface DashboardProps {
  movements: Movement[];
}

const Dashboard: React.FC<DashboardProps> = ({ movements: initialMovements }) => {
  const [movements, setMovements] = useState<Movement[]>([]);

  useEffect(() => {
    if (initialMovements && Array.isArray(initialMovements)) {
      setMovements(initialMovements);
    }
  }, [initialMovements]);

  const filteredMovements = useFilteredMovements(movements);

  const handleMovementsUpdate = (updatedMovements: Movement[]) => {
    console.log('📊 Dashboard: Movimientos actualizados');
    setMovements(updatedMovements);
  };

  if (movements.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-12 shadow-lg text-center">
        <p className="text-gray-500 text-lg">📭 No hay movimientos cargados</p>
      </div>
    );
  }

  if (filteredMovements.length === 0) {
    return (
      <div className="bg-white rounded-2xl p-12 shadow-lg text-center">
        <p className="text-gray-500 text-lg">📭 No hay movimientos para los filtros seleccionados</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <KPICards movements={filteredMovements} />
      <CashFlowChart movements={filteredMovements} />
      <CategoryBreakdown movements={filteredMovements} />

      <div className="mt-12 border-t-2 border-gray-200 pt-8">
        <CategorizeMovements 
          movements={movements}
          onMovementsUpdate={handleMovementsUpdate}
        />
      </div>
    </div>
  );
};

export default Dashboard;