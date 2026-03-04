import React, { useState } from 'react';
import { X, Brain, Check } from 'lucide-react';
import { Movement } from '../types/Movement';

interface LearningFeedbackProps {
  movement: Movement;
  categories: { [key: string]: string[] };
  onClose: () => void;
  onSaved: (movement: Movement, categoria: string, subcategoria: string) => void;
}

export default function LearningFeedback({
  movement,
  categories,
  onClose,
  onSaved,
}: LearningFeedbackProps) {
  const [selectedCat, setSelectedCat] = useState(movement.categoria || '');
  const [selectedSub, setSelectedSub] = useState(movement.subcategoria || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const subcategories =
    selectedCat && categories[selectedCat] ? categories[selectedCat] : [];

  const handleSave = async () => {
    if (!selectedCat) return;
    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/movements/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          movement_id: String(movement.id),
          descripcion: movement.descripcion,
          categoria: selectedCat,
          subcategoria: selectedSub,
          monto: movement.monto,
          banco: movement.institucion,
          fecha: movement.fecha,
        }),
      });
      if (response.ok) {
        setSaved(true);
        onSaved(movement, selectedCat, selectedSub);
        setTimeout(onClose, 1200);
      }
    } catch (err) {
      console.error('Error saving correction:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-800">Corregir categoría</h2>
          <button onClick={onClose} className="ml-auto text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Movement info */}
        <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm text-gray-700">
          <p className="font-medium">{movement.descripcion}</p>
          <p className="text-gray-500 mt-1">
            {movement.fecha} · ${movement.monto?.toLocaleString('es-CL')}
          </p>
        </div>

        {/* Category picker */}
        <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
        <select
          value={selectedCat}
          onChange={(e) => {
            setSelectedCat(e.target.value);
            setSelectedSub('');
          }}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="">-- Seleccionar --</option>
          {Object.keys(categories).map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>

        {subcategories.length > 0 && (
          <>
            <label className="block text-sm font-medium text-gray-700 mb-1">Subcategoría</label>
            <select
              value={selectedSub}
              onChange={(e) => setSelectedSub(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              <option value="">-- Seleccionar --</option>
              {subcategories.map((sub) => (
                <option key={sub} value={sub}>
                  {sub}
                </option>
              ))}
            </select>
          </>
        )}

        {/* AI note */}
        {movement.confianza !== undefined && (
          <p className="text-xs text-gray-400 mb-4">
            Confianza actual de la IA: <strong>{Math.round(movement.confianza)}%</strong>.
            Esta corrección entrenará al sistema.
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 text-gray-700 rounded-lg px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={!selectedCat || saving || saved}
            className="flex-1 bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saved ? (
              <>
                <Check className="w-4 h-4" /> Guardado
              </>
            ) : saving ? (
              'Guardando...'
            ) : (
              <>
                <Brain className="w-4 h-4" /> Guardar y entrenar IA
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
