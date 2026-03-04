import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Movement } from '../types/Movement';

interface CategoryEditorProps {
  movement: Movement;
  allCategories: { [key: string]: string[] };
  onSave: (id: string | number, categoria: string, subcategoria: string) => void;
  onClose: () => void;
}

export default function CategoryEditor({
  movement,
  allCategories,
  onSave,
  onClose,
}: CategoryEditorProps) {
  const [selectedCategory, setSelectedCategory] = useState(movement.categoria || '');
  const [selectedSubcategory, setSelectedSubcategory] = useState(movement.subcategoria || '');
  const [loading, setLoading] = useState(false);

  const categories = Object.keys(allCategories).sort();
  const subcategories = selectedCategory ? (allCategories[selectedCategory] || []) : [];

  const handleSave = async () => {
    if (!selectedCategory || !selectedSubcategory) {
      alert('Por favor selecciona categoría y subcategoría');
      return;
    }

    setLoading(true);
    try {
      await onSave(movement.id, selectedCategory, selectedSubcategory);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Categorizar Movimiento</h2>
          <button
            onClick={onClose}
            disabled={loading}
            className="p-1 hover:bg-gray-100 rounded-lg transition disabled:opacity-50"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Movimiento Info */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <p className="text-sm text-gray-600 mb-1">Descripción:</p>
          <p className="font-semibold text-gray-900 mb-3">{movement.descripcion}</p>
          <p className="text-sm text-gray-600 mb-1">Monto:</p>
          <p className={`font-semibold ${
            movement.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'
          }`}>
            {movement.tipo === 'ingreso' ? '+' : '-'}${Math.abs(movement.monto).toLocaleString('es-CL')}
          </p>
        </div>

        {/* Categoría Selector */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-900 mb-2">
            Categoría
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setSelectedSubcategory('');
            }}
            disabled={loading}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          >
            <option value="">Seleccionar categoría...</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Subcategoría Selector */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-gray-900 mb-2">
            Subcategoría
          </label>
          <select
            value={selectedSubcategory}
            onChange={(e) => setSelectedSubcategory(e.target.value)}
            disabled={!selectedCategory || loading}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:bg-gray-100"
          >
            <option value="">Seleccionar subcategoría...</option>
            {subcategories.map(subcat => (
              <option key={subcat} value={subcat}>
                {subcat}
              </option>
            ))}
          </select>
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50 font-semibold"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={loading || !selectedCategory || !selectedSubcategory}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold"
          >
            {loading ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
}