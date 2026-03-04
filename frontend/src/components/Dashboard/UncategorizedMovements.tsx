import React, { useState, useEffect } from 'react';
import { AlertCircle, Edit2 } from 'lucide-react';
import { Movement } from '../../types/Movement';
import CategoryEditor from '../CategoryEditor';

interface UncategorizedMovementsProps {
  movements: Movement[];
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
  }).format(value);
};

export default function UncategorizedMovements({ movements }: UncategorizedMovementsProps) {
  const [allCategories, setAllCategories] = useState<{ [key: string]: string[] }>({});
  const [selectedMovement, setSelectedMovement] = useState<Movement | null>(null);
  const [showEditor, setShowEditor] = useState(false);

  // Cargar categorías del backend
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('http://localhost:8000/categories');
        const data = await response.json();
        if (data.status === 'success') {
          setAllCategories(data.categories);
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    fetchCategories();
  }, []);

  // ✅ Usar la misma lógica de isUncategorized que en CategorizeMovements
  const isUncategorized = (categoria: any): boolean => {
    if (!categoria) return true;
    const cat = String(categoria).trim().toLowerCase();
    return (
      cat === '' ||
      cat === 'sin categoría' ||
      cat === 'seleccionar...' ||
      cat === 'null' ||
      cat === 'undefined'
    );
  };

  const uncategorized = movements.filter(m => isUncategorized(m.categoria));

  if (uncategorized.length === 0) {
    return null;
  }

  const handleEditMovement = (movement: Movement) => {
    setSelectedMovement(movement);
    setShowEditor(true);
  };

  const handleSaveCategory = async (id: string | number, categoria: string, subcategoria: string) => {
    try {
      const response = await fetch('http://localhost:8000/movements/categorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movement_id: id,
          categoria,
          subcategoria,
          learn: true,
        }),
      });

      if (response.ok) {
        alert('✅ Movimiento categorizado y sistema aprendió el patrón');
        setShowEditor(false);
        setSelectedMovement(null);
      } else {
        alert('❌ Error al categorizar');
      }
    } catch (error) {
      console.error('Error saving category:', error);
      alert('❌ Error al categorizar');
    }
  };

  return (
    <>
      <div className="bg-white rounded-2xl p-8 shadow-lg border-l-4 border-orange-500 mb-8">
        <div className="flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              ⚠️ Movimientos Sin Categorizar ({uncategorized.length})
            </h3>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {uncategorized.map(movement => (
                <div
                  key={`${movement.id}-uncategorized`}
                  className="flex items-center justify-between bg-orange-50 p-3 rounded-lg hover:bg-orange-100 transition"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {movement.descripcion}
                    </p>
                    <p className="text-xs text-gray-500">{movement.fecha}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <p className={`font-semibold ${
                      movement.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {movement.tipo === 'ingreso' ? '+' : '-'}{formatCurrency(Math.abs(movement.monto))}
                    </p>
                    <button
                      onClick={() => handleEditMovement(movement)}
                      className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                      title="Categorizar movimiento"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {uncategorized.length > 0 && (
              <p className="text-xs text-orange-600 mt-4">
                💡 Haz clic en el icono de edición para categorizar estos movimientos
              </p>
            )}
          </div>
        </div>
      </div>

      {showEditor && selectedMovement && (
        <CategoryEditor
          movement={selectedMovement}
          allCategories={allCategories}
          onSave={handleSaveCategory}
          onClose={() => {
            setShowEditor(false);
            setSelectedMovement(null);
          }}
        />
      )}
    </>
  );
}