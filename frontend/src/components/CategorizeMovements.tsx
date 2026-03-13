import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Save, Check, AlertCircle, Search, X, CheckCircle2 } from 'lucide-react';
import { Movement } from '../types/Movement';
import SimilarMovementsModal from './SimilarMovementsModal';
import CompactLoadingOverlay from './CompactLoadingOverlay';
import Toast from './Toast';

interface CategorizeMovementsProps {
  movements: Movement[];
  onMovementsUpdate?: (movements: Movement[]) => void;
}

interface ToastMessage {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
  }).format(value);
};

export default function CategorizeMovements({
  movements,
  onMovementsUpdate,
}: CategorizeMovementsProps) {
  const [categories, setCategories] = useState<{ [key: string]: string[] }>({});
  const [filter, setFilter] = useState<'uncategorized' | 'categorized' | 'all'>('uncategorized');
  const [searchQuery, setSearchQuery] = useState('');
  const [saving, setSaving] = useState(false);
  const [savingMessage, setSavingMessage] = useState('Buscando similares...');
  const [changes, setChanges] = useState<{
    [key: string]: { categoria: string; subcategoria: string };
  }>({});
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Modal de similares
  const [showSimilarModal, setShowSimilarModal] = useState(false);
  const [similarData, setSimilarData] = useState<any>(null);
  const [pendingChange, setPendingChange] = useState<{
    movId: string | number;
    categoria: string;
    subcategoria: string;
  } | null>(null);

  // Función para agregar notificaciones
  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  React.useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('http://localhost:8000/categories');
        const data = await response.json();
        if (data.status === 'success') {
          setCategories(data.categories);
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    fetchCategories();
  }, []);

  // ✅ AGREGAR: Debug de IDs de movimientos
  useEffect(() => {
    console.log('📊 MOVIMIENTOS RECIBIDOS EN COMPONENTE:');
    console.log('Total:', movements.length);
    console.log('Primeros 3 movimientos:');
    movements.slice(0, 3).forEach((mov, idx) => {
      console.log(`  [${idx}] ID: "${mov.id}" (tipo: ${typeof mov.id}), Desc: ${mov.descripcion}`);
    });
    
    // ✅ VERIFICAR IDs ÚNICOS
    const ids = movements.map(m => String(m.id));
    const uniqueIds = new Set(ids);
    console.log(`Movimientos totales: ${ids.length}, IDs únicos: ${uniqueIds.size}`);
    
    if (ids.length !== uniqueIds.size) {
      console.error('❌ HAY IDs DUPLICADOS!');
      const duplicados = ids.filter((id, idx) => ids.indexOf(id) !== idx);
      console.error('IDs duplicados:', [...new Set(duplicados)]);
    } else {
      console.log('✅ Todos los IDs son únicos');
    }
  }, [movements]);

  // ✅ Función auxiliar para verificar si está sin categorizar
  const isUncategorized = (categoria: any): boolean => {
    if (!categoria) return true;
    const cat = String(categoria).trim().toLowerCase();
    return (
      cat === '' ||
      cat === 'sin categoría' ||
      cat === 'sin categoria' ||
      cat === 'uncategorized' ||      
      cat === 'seleccionar...' ||
      cat === 'Seleccionar...' ||
      cat === 'Seleccionar' ||
      cat === 'null' ||
      cat === 'undefined'
    );
  };

  // ✅ Filtrar movimientos por tab - MEJORADO
  const filteredByTab = useMemo(() => {
    if (filter === 'uncategorized') {
      return movements.filter(m => {
        const movIdStr = String(m.id);
        const hasChanges = !!changes[movIdStr];
        const isUncatNow = isUncategorized(m.categoria);
        
        if (hasChanges) {
          return true;
        }
        return isUncatNow;
      });
    } else if (filter === 'categorized') {
      return movements.filter(m => !isUncategorized(m.categoria));
    } else {
      return movements;
    }
  }, [movements, filter, changes]);

  // 🔍 DEBUG DEL FILTRO
  useEffect(() => {
    console.log('🔍 FILTRO ACTUAL:', filter);
    console.log('📊 Movimientos totales:', movements.length);
    console.log('✅ Sin categorizar:', movements.filter(m => isUncategorized(m.categoria)).length);
    console.log('✅ Categorizados:', movements.filter(m => !isUncategorized(m.categoria)).length);
    console.log('📋 Mostrados por filtro:', filteredByTab.length);
    console.log('Primeros 3 en filteredByTab:', filteredByTab.slice(0, 3).map(m => ({id: m.id, cat: m.categoria})));
  }, [filteredByTab, filter, movements]);

  // ✅ Filtrar por búsqueda
  const displayMovements = useMemo(() => {
    if (!searchQuery.trim()) return filteredByTab;
    
    const query = searchQuery.toLowerCase();
    return filteredByTab.filter(m => 
      m.descripcion.toLowerCase().includes(query) ||
      m.fecha.includes(query) ||
      (m.categoria && m.categoria.toLowerCase().includes(query)) ||
      (m.subcategoria && m.subcategoria.toLowerCase().includes(query))
    );
  }, [filteredByTab, searchQuery]);

  // ✅ Contar sin categorizar y categorizados correctamente
  const uncategorizedCount = movements.filter(m => isUncategorized(m.categoria)).length;
  const categorizedCount = movements.filter(m => !isUncategorized(m.categoria)).length;

  const handleChangeCategory = useCallback((movId: string | number, categoria: string) => {
    setChanges(prev => ({
      ...prev,
      [String(movId)]: {
        categoria,
        subcategoria: '',
      },
    }));
  }, []);

  const handleChangeSubcategory = useCallback((movId: string | number, subcategoria: string) => {
    setChanges(prev => ({
      ...prev,
      [String(movId)]: {
        ...(prev[String(movId)] || { categoria: '', subcategoria: '' }),
        subcategoria,
      },
    }));
  }, []);

  // Guardar directamente sin buscar similares
  const handleSaveDirectly = useCallback(async (movId: string | number) => {
    try {
      const movIdStr = String(movId);
      const changeData = changes[movIdStr];

      if (!changeData) {
        showToast('⚠️ No hay cambios para guardar', 'info');
        return;
      }

      const movement = movements.find(m => String(m.id) === movIdStr);
      if (!movement) {
        showToast('❌ Movimiento no encontrado', 'error');
        return;
      }

      const updates = [{
        movement_id: movIdStr,
        descripcion: movement.descripcion,
        categoria: changeData.categoria,
        subcategoria: changeData.subcategoria,
      }];

      console.log('📤 Guardando directamente:', updates);

      const response = await fetch('http://localhost:8000/movements/batch-categorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movements: updates,
          learn: false,
        }),
      });

      const result = await response.json();
      console.log('✅ Respuesta del servidor:', result);

      if (result.status === 'success') {
        const updatedMovements = movements.map(mov => {
          if (String(mov.id) === movIdStr) {
            return {
              ...mov,
              categoria: changeData.categoria,
              subcategoria: changeData.subcategoria,
            };
          }
          return mov;
        });

        setChanges(prev => {
          const newChanges = { ...prev };
          delete newChanges[movIdStr];
          return newChanges;
        });

        if (onMovementsUpdate) {
          onMovementsUpdate(updatedMovements);
        }

        showToast('✅ Movimiento guardado correctamente', 'success');
      } else {
        showToast(`❌ Error: ${result.message}`, 'error');
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('❌ Error al guardar', 'error');
    }
  }, [changes, movements, onMovementsUpdate, showToast]);

  // Buscar similares
  const handleSaveAll = useCallback(async () => {
    const changeCount = Object.keys(changes).length;
    if (changeCount === 0) {
      showToast('⚠️ No hay cambios para guardar', 'info');
      return;
    }

    setSaving(true);
    setSavingMessage('Buscando similares...');

    try {
      const firstChange = Object.entries(changes)[0];
      const [movIdStr, data] = firstChange;
      const movement = movements.find(m => String(m.id) === movIdStr);

      if (!movement) {
        showToast('❌ Movimiento no encontrado', 'error');
        setSaving(false);
        return;
      }

      console.log('🔍 Buscando similares para:', movement.descripcion);

      const response = await fetch('http://localhost:8000/movements/find-similar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movement_id: movement.id,
          descripcion: movement.descripcion,
          categoria: data.categoria,
          subcategoria: data.subcategoria,
        }),
      });

      const result = await response.json();

      if (result.status === 'success') {
        setSimilarData(result);
        setPendingChange({ movId: movement.id, ...data });
        setShowSimilarModal(true);
        setSaving(false);
      } else {
        showToast(`❌ Error: ${result.message}`, 'error');
        setSaving(false);
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('❌ Error al buscar similares', 'error');
      setSaving(false);
    }
  }, [changes, movements, showToast]);

  // Confirmar y guardar similares
  const handleConfirmSimilars = useCallback(async (selectedIds: (string | number)[]) => {
    try {
      setSaving(true);
      setSavingMessage('Guardando cambios...');

      if (!pendingChange) return;

      const allIds = [pendingChange.movId, ...selectedIds];

      const updates = allIds.map(id => {
        const movement = movements.find(m => String(m.id) === String(id));
        
        return {
          movement_id: String(id),
          descripcion: movement?.descripcion || '',
          categoria: pendingChange.categoria,
          subcategoria: pendingChange.subcategoria,
        };
      });

      const response = await fetch('http://localhost:8000/movements/batch-categorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movements: updates,
          learn: true,
        }),
      });

      const result = await response.json();

      if (result.status === 'success') {
        const updatedMovements = movements.map(mov => {
          const shouldUpdate = allIds.some(id => String(id) === String(mov.id));
          if (shouldUpdate) {
            return {
              ...mov,
              categoria: pendingChange.categoria,
              subcategoria: pendingChange.subcategoria,
            };
          }
          return mov;
        });

        setChanges({});
        setShowSimilarModal(false);
        setSimilarData(null);
        setPendingChange(null);
        setSaving(false);
        setSearchQuery('');

        if (onMovementsUpdate) {
          onMovementsUpdate(updatedMovements);
        }

        showToast(`✅ ${result.updated_count} movimiento(s) guardado(s)`, 'success');
      } else {
        showToast(`❌ Error: ${result.message}`, 'error');
        setSaving(false);
      }
    } catch (error) {
      console.error('Error:', error);
      showToast('❌ Error al guardar', 'error');
      setSaving(false);
    }
  }, [pendingChange, movements, onMovementsUpdate, showToast]);

  return (
    <>
      {saving && <CompactLoadingOverlay message={savingMessage} />}

      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          onClose={() => removeToast(toast.id)}
        />
      ))}

      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">🏷️ Categorizar Movimientos</h2>
            <button
              onClick={handleSaveAll}
              disabled={Object.keys(changes).length === 0 || saving}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2 px-6 rounded-lg flex items-center gap-2 transition disabled:cursor-not-allowed"
              title="Busca movimientos similares para aplicar cambios en lote"
            >
              <Save className="w-5 h-5" />
              {saving ? 'Procesando...' : `Guardar con similares (${Object.keys(changes).length})`}
            </button>
          </div>

          {/* Filtros */}
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setFilter('uncategorized')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'uncategorized'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <AlertCircle className="w-4 h-4 inline mr-2" />
              Sin Categorizar ({uncategorizedCount})
            </button>
            <button
              onClick={() => setFilter('categorized')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'categorized'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Check className="w-4 h-4 inline mr-2" />
              Categorizados ({categorizedCount})
            </button>
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todos ({movements.length})
            </button>
          </div>

          {/* Buscador */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por descripción, fecha, categoría..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* Tabla */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100 border-b-2 border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-900">Fecha</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-900">Descripción</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-900">Monto</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-900">Banco</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-900">Categoría</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-900">Subcategoría</th>
                  <th className="px-6 py-4 text-center text-sm font-bold text-gray-900">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {displayMovements.map((movement) => {
                  const movIdStr = String(movement.id);
                  const isChanged = !!changes[movIdStr];
                  const categoria = changes[movIdStr]?.categoria || movement.categoria || '';
                  const subcategoria = changes[movIdStr]?.subcategoria || movement.subcategoria || '';
                  const subcategories = categoria ? categories[categoria] || [] : [];

                  return (
                    <tr
                      key={movIdStr}
                      className={`border-b transition ${isChanged ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                    >
                      <td className="px-6 py-4 text-sm text-gray-900">{movement.fecha}</td>
                      <td className="px-6 py-4 text-sm text-gray-900 font-medium">{movement.descripcion}</td>
                      <td
                        className={`px-6 py-4 text-sm font-semibold ${
                          movement.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {movement.tipo === 'ingreso' ? '+' : '-'}
                        {formatCurrency(Math.abs(movement.monto))}
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-700">
                        {movement.banco && movement.tipo_cuenta
                          ? `${movement.banco}-${movement.tipo_cuenta}`
                          : movement.banco || '-'}
                      </td>

                      <td className="px-6 py-4">
                        <select
                          value={categoria}
                          onChange={(e) => handleChangeCategory(movement.id, e.target.value)}
                          disabled={saving}
                          className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed ${
                            isChanged ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                          }`}
                        >
                          <option value="">Seleccionar...</option>
                          {Object.keys(categories).map(cat => (
                            <option key={cat} value={cat}>
                              {cat}
                            </option>
                          ))}
                        </select>
                      </td>

                      <td className="px-6 py-4">
                        <select
                          value={subcategoria}
                          onChange={(e) => handleChangeSubcategory(movement.id, e.target.value)}
                          disabled={!categoria || saving}
                          className={`w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:bg-gray-100 disabled:cursor-not-allowed ${
                            isChanged ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                          }`}
                        >
                          <option value="">Seleccionar...</option>
                          {subcategories.map(subcat => (
                            <option key={subcat} value={subcat}>
                              {subcat}
                            </option>
                          ))}
                        </select>
                      </td>

                      <td className="px-6 py-4 text-center flex items-center justify-center gap-2">
                        {isChanged ? (
                          <>
                            <button
                              onClick={() => handleSaveDirectly(movement.id)}
                              disabled={saving}
                              className="p-2 bg-green-100 hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition"
                              title="Guardar sin buscar similares"
                            >
                              <CheckCircle2 className="w-5 h-5 text-green-600" />
                            </button>
                            <Check className="w-5 h-5 text-blue-600" />
                          </>
                        ) : isUncategorized(categoria) ? (
                          <AlertCircle className="w-5 h-5 text-orange-600" />
                        ) : (
                          <Check className="w-5 h-5 text-green-600" />
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {displayMovements.length === 0 && (
            <div className="text-center py-12">
              <Check className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg font-medium">
                {searchQuery
                  ? `❌ No se encontraron resultados para "${searchQuery}"`
                  : `✅ ${filter === 'uncategorized' ? 'Todos categorizados' : filter === 'categorized' ? 'Sin movimientos sin categorizar' : 'Sin movimientos'}`}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Modal de Similares */}
      {showSimilarModal && similarData && (
        <>
          {saving && <CompactLoadingOverlay message={savingMessage} />}
          <SimilarMovementsModal
            original={similarData.original}
            similares={similarData.similares}
            onConfirm={handleConfirmSimilars}
            onCancel={() => {
              setShowSimilarModal(false);
              setSimilarData(null);
              setPendingChange(null);
            }}
            loading={saving}
          />
        </>
      )}
    </>
  );
}