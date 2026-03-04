import React, { useMemo, useState } from 'react';
import { AlertCircle, Check, X } from 'lucide-react';
import CompactLoadingOverlay from './CompactLoadingOverlay';

interface SimilarMovement {
  id: string | number;
  descripcion: string;
  fecha: string;
  monto: number;
  categoria_actual: string;
  subcategoria_actual: string;
  similitud: number;
  tipo_similitud: string;
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

const normalizarCategoria = (cat: string | null | undefined): string => {
  if (!cat || cat.trim() === '' || cat.toLowerCase() === 'sin categoría') {
    return '';
  }
  return cat.trim();
};

const normalizarSubcategoria = (subcat: string | null | undefined): string => {
  if (!subcat || subcat.trim() === '' || subcat.toLowerCase() === 'sin subcategoría') {
    return '';
  }
  return subcat.trim();
};

export default function SimilarMovementsModal({
  original,
  similares,
  onConfirm,
  onCancel,
  loading = false,
}: SimilarMovementsModalProps) {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  const newCategoria = normalizarCategoria(original.categoria);
  const newSubcategoria = normalizarSubcategoria(original.subcategoria);

  const filteredSimilares = useMemo(() => {
    return similares.filter((mov) => {
      const actualCategoria = normalizarCategoria(mov.categoria_actual);
      const actualSubcategoria = normalizarSubcategoria(mov.subcategoria_actual);

      const estaSinCategorizar = actualCategoria === '' && actualSubcategoria === '';
      const categoriaEsDiferente = actualCategoria !== newCategoria;
      const subcategoriaEsDiferente = actualSubcategoria !== newSubcategoria;

      return estaSinCategorizar || categoriaEsDiferente || subcategoriaEsDiferente;
    });
  }, [similares, newCategoria, newSubcategoria]);

  const filteredCount = similares.length - filteredSimilares.length;

  const handleToggle = (idx: number) => {
    setSelectedIndices(prev => {
      const newSelected = new Set(prev);
      if (newSelected.has(idx)) {
        newSelected.delete(idx);
      } else {
        newSelected.add(idx);
      }
      return newSelected;
    });
  };

  const handleSelectAll = () => {
    if (selectedIndices.size === filteredSimilares.length) {
      setSelectedIndices(new Set());
    } else {
      const allIndices = new Set(filteredSimilares.map((_, idx) => idx));
      setSelectedIndices(allIndices);
    }
  };

  const handleConfirm = () => {
    const selectedIds = Array.from(selectedIndices).map(idx => filteredSimilares[idx].id);
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
                {filteredSimilares.length === 0 ? (
                  <>
                    ✅ Todos los similares ya tienen esta categorización
                    {filteredCount > 0 && (
                      <span className="ml-2 bg-green-500 px-2 py-1 rounded text-xs">
                        ({filteredCount} movimientos)
                      </span>
                    )}
                  </>
                ) : (
                  <>
                    {filteredSimilares.length} movimiento(s) necesitan actualizar categorización
                    {filteredCount > 0 && (
                      <span className="ml-2 bg-blue-500 px-2 py-1 rounded text-xs">
                        ({filteredCount} ya con esta categoría - no mostrados)
                      </span>
                    )}
                  </>
                )}
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
            <div className="flex items-center gap-2 mb-3">
              <Check className="w-5 h-5 text-green-600" />
              <h3 className="font-bold text-green-900">Movimiento Original</h3>
            </div>
            <p className="text-sm mb-2 text-gray-700">
              <span className="font-semibold">Descripción:</span> {original.descripcion}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-semibold">Nueva Categorización:</span>{' '}
              <span className="text-green-700 font-bold">
                {newCategoria || 'Sin Categoría'} → {newSubcategoria || 'Sin Subcategoría'}
              </span>
            </p>
          </div>

          {filteredSimilares.length === 0 ? (
            <div className="text-center py-12 bg-green-50 rounded-lg">
              <Check className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <p className="text-gray-600 font-semibold">
                ✅ Perfecto, todos los similares ya tienen esta categorización
              </p>
              {filteredCount > 0 && (
                <p className="text-sm text-gray-500 mt-2">
                  {filteredCount} movimiento(s) similares ya están categorizados como:{' '}
                  <strong>{newCategoria || 'Sin Categoría'} / {newSubcategoria || 'Sin Subcategoría'}</strong>
                </p>
              )}
            </div>
          ) : (
            <>
              {/* Checkbox Seleccionar Todos */}
              <div className="flex items-center gap-4 mb-4 pb-4 border-b">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedIndices.size === filteredSimilares.length && filteredSimilares.length > 0}
                    onChange={handleSelectAll}
                    disabled={loading}
                    className="w-4 h-4 cursor-pointer"
                  />
                  <span className="font-semibold text-gray-700">Seleccionar todos</span>
                </label>
                <span className="text-sm text-gray-500">
                  {selectedIndices.size} de {filteredSimilares.length} seleccionados
                </span>
              </div>

              {/* Tabla de Similares */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-100 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold w-12">
                        <input
                          type="checkbox"
                          checked={selectedIndices.size === filteredSimilares.length && filteredSimilares.length > 0}
                          onChange={handleSelectAll}
                          disabled={loading}
                          className="w-4 h-4"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Similitud</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Fecha</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Descripción</th>
                      <th className="px-4 py-3 text-right text-sm font-semibold">Monto</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold">Categoría Actual</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredSimilares.map((mov, idx) => {
                      const isSelected = selectedIndices.has(idx);
                      const actualCat = normalizarCategoria(mov.categoria_actual);
                      const actualSubcat = normalizarSubcategoria(mov.subcategoria_actual);
                      const estaSinCategoria = actualCat === '' && actualSubcat === '';
                      
                      return (
                        <tr
                          key={`${mov.id}-${idx}`}
                          className={`transition ${isSelected ? 'bg-blue-50' : estaSinCategoria ? 'hover:bg-gray-50' : 'bg-yellow-50 hover:bg-yellow-100'}`}
                        >
                          <td className="px-4 py-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggle(idx)}
                              disabled={loading}
                              className="w-4 h-4 cursor-pointer"
                            />
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-2 h-2 rounded-full ${
                                  mov.similitud === 100 ? 'bg-green-500' : 'bg-yellow-500'
                                }`}
                              />
                              <span className="font-semibold">{mov.similitud}%</span>
                              <span className="text-xs text-gray-500">
                                ({mov.tipo_similitud})
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-700">{mov.fecha}</td>
                          <td className="px-4 py-3 text-sm text-gray-700 font-medium">
                            {mov.descripcion}
                          </td>
                          <td className="px-4 py-3 text-sm font-semibold text-red-600 text-right">
                            {formatCurrency(Math.abs(mov.monto))}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {estaSinCategoria ? (
                              <span className="text-gray-400 italic text-xs">Sin categoría</span>
                            ) : (
                              <div className="text-xs space-y-1">
                                <div className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                                  {actualCat || 'Sin Categoría'}
                                </div>
                                <div className="text-gray-600">
                                  {actualSubcat || 'Sin Subcategoría'}
                                </div>
                              </div>
                            )}
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
        <div className="bg-gray-50 p-6 border-t flex justify-end gap-3 sticky bottom-0">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition disabled:opacity-50"
          >
            Cancelar
          </button>
          {filteredSimilares.length > 0 && (
            <button
              onClick={handleConfirm}
              disabled={loading || selectedIndices.size === 0}
              className="px-6 py-2 rounded-lg bg-green-600 text-white font-semibold hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Check className="w-5 h-5" />
              Aplicar a {selectedIndices.size}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}