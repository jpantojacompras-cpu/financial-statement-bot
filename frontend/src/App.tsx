import React, { useState, useEffect } from 'react';
import { FileText, Loader } from 'lucide-react';
import { Movement } from './types/Movement';
import Sidebar from './components/Sidebar';
import FileUpload from './components/FileUpload';
import MovementsTable from './components/MovementsTable';
import Dashboard from './components/Dashboard';
import Analysis from './components/Analysis';
import FileManager from './components/FileManager';
import CategoryManagement from './components/CategoryManagement';
import CategorizeMovements from './components/CategorizeMovements';
import PatternExplorer from './components/PatternExplorer';
import DateFilter from './components/DateFilter';
import { DateFilterProvider } from './context/DateFilterContext';

function AppContent() {
  const [movements, setMovements] = useState<Movement[]>([]);
  const [currentPage, setCurrentPage] = useState<'upload' | 'movements' | 'dashboard' | 'analysis' | 'files' | 'categories' | 'categorize' | 'patterns'>('upload');
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('Cargando movimientos...');

  useEffect(() => {
    fetchMovements();
  }, []);

  const fetchMovements = async () => {
    try {
      setLoading(true);
      setProgress(10);
      setProgressMessage('Conectando al servidor...');

      const response = await fetch('http://localhost:8000/movements');
      
      if (!response.ok) {
        throw new Error('Error al cargar movimientos');
      }

      setProgress(50);
      setProgressMessage('Procesando datos...');

      const data = await response.json();
      if (data.status === 'success') {
        setMovements(data.movimientos || []);
        setProgress(90);
        setProgressMessage('Finalizando...');
      }
    } catch (error) {
      console.error('Error fetching movements:', error);
      setMovements([]);
    } finally {
      setProgress(100);
      setTimeout(() => {
        setLoading(false);
      }, 500);
    }
  };

  const handleMovementsLoaded = (newMovements: Movement[]) => {
    setMovements(newMovements);
  };

  const handleMovementsUpdate = () => {
    fetchMovements();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <Loader className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">FinBot</h2>
          <p className="text-gray-600 mb-4">{progressMessage}</p>
          <div className="w-64 bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-full transition-all duration-300"
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
          <p className="text-gray-500 mt-4 text-sm">{progress}%</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />

      <main className="flex-1 overflow-auto">
        {currentPage !== 'upload' && currentPage !== 'files' && currentPage !== 'categories' && currentPage !== 'patterns' && (
          <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
            <div className="flex items-center justify-between px-8 py-4">
              <h1 className="text-2xl font-bold text-gray-900">
                {currentPage === 'movements' && '📊 Tabla de Movimientos'}
                {currentPage === 'dashboard' && '📈 Dashboard'}
                {currentPage === 'analysis' && '🔍 Análisis'}
                {currentPage === 'categorize' && '🏷️ Categorizar Movimientos'}
              </h1>

              {movements.length > 0 && (
                <DateFilter movements={movements} />
              )}
            </div>
          </div>
        )}

        <div className={currentPage === 'categories' || currentPage === 'patterns' ? '' : 'p-8'}>
          {currentPage === 'upload' && (
            <FileUpload onMovementsLoaded={handleMovementsLoaded} />
          )}

          {currentPage === 'movements' && movements.length > 0 && (
            <MovementsTable movements={movements} />
          )}

          {currentPage === 'categorize' && movements.length > 0 && (
            <CategorizeMovements 
              movements={movements} 
              onMovementsUpdate={handleMovementsUpdate}
            />
          )}

          {currentPage === 'categories' && (
            <CategoryManagement onClose={() => setCurrentPage('movements')} />
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

          {currentPage === 'patterns' && (
            <PatternExplorer />
          )}

          {movements.length === 0 && currentPage !== 'upload' && currentPage !== 'files' && currentPage !== 'categories' && currentPage !== 'patterns' && (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No hay movimientos cargados</p>
              <p className="text-gray-400">Ve a "Cargar Archivos" para comenzar</p>
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