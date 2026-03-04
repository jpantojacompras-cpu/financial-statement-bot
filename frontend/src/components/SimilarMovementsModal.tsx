import React, { useState } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';
import CompactLoadingOverlay from './CompactLoadingOverlay';

interface SimilarMovement {
  id: string | number;
  descripcion: string;
  fecha: string;
  monto: number;
  categoria_actual: string;
  subcategoria_actual: string;
  similitud: number;
}

interface SimilarMovementsModalProps {
  original: {
    id: string | number;
    descripcion: string;
    categoria: string;
    subcategoria: string;
  };
  similares: SimilarMovement[];
  onConfirm: (selectedIds: (string | number)[]) => void;
  onCancel: () => void;
  loading?: boolean;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
  }).format(value);
};

export default function SimilarMovementsModal({
  original,
  similares,
  onConfirm,
  onCancel,
  loading = false,
}: SimilarMovementsModalProps) {
  // Usar índices como key en lugar de IDs
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  const handleToggle = (idx: number) => {
    setSelectedIndices(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(idx)) {
        newSelected.delete(idx);
      } else {
        newSelected.add(idx);
      }
      console.log(`Toggle índice ${idx}, total seleccionados: ${newSelected.size}`);
      return newSelected;
    });
  };

  const handleSelectAll = () => {
    if (selectedIndices.size === similares.length) {
      setSelectedIndices(new Set());
    } else {
      const allIndices = new Set(similares.map((_, idx) => idx));
      setSelectedIndices(allIndices);
      console.log(`Seleccionar todos: ${allIndices.size}`);
    }
  };

  const handleConfirm = () => {
    // Convertir índices de vuelta a IDs
    const selectedIds = Array.from(selectedIndices).map(idx => similares[idx].id);
    console.log(`Confirmando con ${selectedIds.length} IDs:`, selectedIds);
    onConfirm(selectedIds);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      {loading && <CompactLoadingOverlay message="Guardando cambios..." />}

      <div className={`bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto transition-opacity ${loading ? 'opacity-50' : 'opacity-100'}`}>
        
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 text-white sticky top-0 z-40">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <AlertCircle className="w-6 h-6" />
                Movimientos Similares
              </h2>
              <p className="text-blue-100 text-sm mt-1">
                Se encontraron {similares.length} movimientos con descripción similar
              </p>
            </div>
            <button
              onClick={onCancel}
              disabled={loading}
              className="p-2 hover:bg-blue-500 rounded-lg transition disabled:opacity-50"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Contenido */}
        <div className="p-6">
          
          {/* Movimiento Original */}
          <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4 mb-6">
            <h3 className="font-bold text-green-900 mb-2">✅ Movimiento Original</h3>
            <p className="text-sm text-gray-700 mb-2">
              <strong>Descripción:</strong> {original.descripcion}
            </p>
            <p className="text-sm text-gray-700">
              <strong>Nueva Categorización:</strong> {original.categoria} → {original.subcategoria}
            </p>
          </div>

          {similares.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No se encontraron movimientos similares</p>
            </div>
          ) : (
            <>
              {/* Controles */}
              <div className="flex items-center gap-4 mb-4 pb-4 border-b">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedIndices.size === similares.length && similares.length > 0}
                    onChange={handleSelectAll}
                    disabled={loading}
                    className="w-5 h-5 cursor-pointer disabled:opacity-50"
                  />
                  <span className="font-medium text-gray-700">
                    {selectedIndices.size === similares.length && similares.length > 0
                      ? 'Deseleccionar todos'
                      : 'Seleccionar todos'}
                  </span>
                </label>
                <span className="text-gray-500 text-sm ml-auto">
                  {selectedIndices.size} de {similares.length} seleccionados
                </span>
              </div>

              {/* Tabla */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100 border-b sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left w-12">
                        <input
                          type="checkbox"
                          checked={selectedIndices.size === similares.length && similares.length > 0}
                          onChange={handleSelectAll}
                          disabled={loading}
                          className="w-4 h-4 cursor-pointer disabled:opacity-50"
                        />
                      </th>
                      <th className="px-4 py-3 text-left">Similitud</th>
                      <th className="px-4 py-3 text-left">Fecha</th>
                      <th className="px-4 py-3 text-left">Descripción</th>
                      <th className="px-4 py-3 text-right">Monto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {similares.map((mov, idx) => {
                      const isChecked = selectedIndices.has(idx);
                      return (
                        <tr
                          key={`row-${idx}`}
                          className={`border-b transition ${isChecked ? 'bg-blue-100' : 'hover:bg-gray-50'}`}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => handleToggle(idx)}
                              disabled={loading}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    mov.similitud >= 90
                                      ? 'bg-green-500'
                                      : mov.similitud >= 80
                                      ? 'bg-yellow-500'
                                      : 'bg-orange-500'
                                  }`}
                                  style={{ width: `${mov.similitud}%` }}
                                />
                              </div>
                              <span className="font-semibold text-xs w-12">{mov.similitud}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-gray-600">{mov.fecha}</td>
                          <td className="px-4 py-3 font-medium">{mov.descripcion}</td>
                          <td className="px-4 py-3 font-semibold text-red-600 text-right">
                            {formatCurrency(Math.abs(mov.monto))}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 border-t p-6 flex items-center justify-end gap-3 sticky bottom-0 z-40">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 font-semibold hover:bg-gray-100 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading || selectedIndices.size === 0}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold rounded-lg flex items-center gap-2 transition disabled:cursor-not-allowed"
          >
            {loading ? 'Guardando...' : `Aplicar a ${selectedIndices.size}`}
            {!loading && <Check className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}