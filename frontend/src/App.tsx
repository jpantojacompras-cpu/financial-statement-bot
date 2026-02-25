import React, { useState, useEffect } from 'react';
import { FileText } from 'lucide-react';
import Sidebar from './components/Sidebar';
import FileUpload from './components/FileUpload';
import MovementsTable from './components/MovementsTable';
import Dashboard from './components/Dashboard';
import Analysis from './components/Analysis';
import FileManager from './components/FileManager';
import DateFilter from './components/DateFilter';
import { DateFilterProvider } from './context/DateFilterContext';

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

function AppContent() {
  const [movements, setMovements] = useState<Movement[]>([]);
  const [currentPage, setCurrentPage] = useState<'upload' | 'movements' | 'dashboard' | 'analysis' | 'files'>('upload');

  useEffect(() => {
    fetchMovements();
  }, []);

  const fetchMovements = async () => {
    try {
      const response = await fetch('http://localhost:8000/movements');
      const data = await response.json();
      if (data.status === 'success') {
        setMovements(data.movimientos || []);
      }
    } catch (error) {
      console.error('Error fetching movements:', error);
    }
  };

  const handleMovementsLoaded = (newMovements: Movement[]) => {
    setMovements(newMovements);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />

      <main className="flex-1 overflow-auto">
        {/* Header con filtro de fecha */}
        <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
          <div className="flex items-center justify-between px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900">
              {currentPage === 'upload' && '📤 Cargar Archivos'}
              {currentPage === 'movements' && '📊 Tabla de Movimientos'}
              {currentPage === 'dashboard' && '📈 Dashboard'}
              {currentPage === 'analysis' && '🔍 Análisis'}
              {currentPage === 'files' && '📁 Gestión de Archivos'}
            </h1>

            {currentPage !== 'upload' && currentPage !== 'files' && movements.length > 0 && (
              <DateFilter movements={movements} />
            )}
          </div>
        </div>

        {/* Contenido principal */}
        <div className="p-8">
          {currentPage === 'upload' && (
            <FileUpload onMovementsLoaded={handleMovementsLoaded} />
          )}

          {currentPage === 'movements' && movements.length > 0 && (
            <MovementsTable movements={movements} />
          )}

          {currentPage === 'dashboard' && movements.length > 0 && (
            <Dashboard movements={movements} />
          )}

          {currentPage === 'analysis' && movements.length > 0 && (
            <Analysis movements={movements} />
          )}

          {currentPage === 'files' && (
            <FileManager />
          )}

          {movements.length === 0 && currentPage !== 'upload' && currentPage !== 'files' && (
            <div className="text-center py-12">
              <FileText className="mx-auto text-gray-400 mb-4" size={48} />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Sin movimientos
              </h3>
              <p className="text-gray-600">
                Carga archivos para ver los movimientos
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <DateFilterProvider>
      <AppContent />
    </DateFilterProvider>
  );
}