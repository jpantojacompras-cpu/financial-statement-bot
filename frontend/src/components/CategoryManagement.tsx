import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, X } from 'lucide-react';
import { api } from '../services/api';

interface CategoryManagementProps {
  onClose: () => void;
}

export default function CategoryManagement({ onClose }: CategoryManagementProps) {
  const [categories, setCategories] = useState<{ [key: string]: string[] }>({});
  const [newCategory, setNewCategory] = useState('');
  const [newSubcategory, setNewSubcategory] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Cargar categorías
  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const data = await api.get<{ status: string; categories: { [key: string]: string[] } }>('/categories');
      if (data.status === 'success') {
        setCategories(data.categories);
      }
    } catch (error) {
      console.error('Error fetching categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCategory = async () => {
    if (!newCategory.trim() || categories[newCategory]) {
      alert('⚠️ Categoría vacía o ya existe');
      return;
    }

    setSaving(true);
    try {
      const result = await api.post<{ status: string; message?: string }>('/categories/add', { categoria: newCategory });

      if (result.status === 'success') {
        alert('✅ Categoría agregada');
        setNewCategory('');
        setSelectedCategory(newCategory);
        await fetchCategories();
      } else {
        alert('❌ ' + result.message);
      }
    } catch (error) {
      console.error('Error adding category:', error);
      alert('❌ Error al agregar categoría');
    } finally {
      setSaving(false);
    }
  };

  const handleAddSubcategory = async () => {
    if (!selectedCategory || !newSubcategory.trim()) {
      alert('⚠️ Selecciona categoría y escribe subcategoría');
      return;
    }

    setSaving(true);
    try {
      const result = await api.post<{ status: string; message?: string }>('/categories/add-subcategory', {
        categoria: selectedCategory,
        subcategoria: newSubcategory,
      });

      if (result.status === 'success') {
        alert('✅ Subcategoría agregada');
        setNewSubcategory('');
        await fetchCategories();
      } else {
        alert('❌ ' + result.message);
      }
    } catch (error) {
      console.error('Error adding subcategory:', error);
      alert('❌ Error al agregar subcategoría');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCategory = async (category: string) => {
    if (!window.confirm(`¿Eliminar categoría "${category}"?`)) return;

    setSaving(true);
    try {
      const result = await api.post<{ status: string; message?: string }>('/categories/delete', { categoria: category });

      if (result.status === 'success') {
        alert('✅ Categoría eliminada');
        if (selectedCategory === category) setSelectedCategory(null);
        await fetchCategories();
      } else {
        alert('❌ ' + result.message);
      }
    } catch (error) {
      console.error('Error deleting category:', error);
      alert('❌ Error al eliminar categoría');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSubcategory = async (category: string, subcategory: string) => {
    if (subcategory === 'Sin Subcategoría') {
      alert('⚠️ No se puede eliminar "Sin Subcategoría"');
      return;
    }

    if (!window.confirm(`¿Eliminar subcategoría "${subcategory}"?`)) return;

    setSaving(true);
    try {
      const result = await api.post<{ status: string; message?: string }>('/categories/delete-subcategory', {
        categoria: category,
        subcategoria: subcategory,
      });

      if (result.status === 'success') {
        alert('✅ Subcategoría eliminada');
        await fetchCategories();
      } else {
        alert('❌ ' + result.message);
      }
    } catch (error) {
      console.error('Error deleting subcategory:', error);
      alert('❌ Error al eliminar subcategoría');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-500">Cargando categorías...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-900">📂 Gestor de Categorías</h1>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Panel Izquierdo: Agregar Categoría */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl p-6 shadow-lg sticky top-8">
              <h2 className="text-lg font-bold text-gray-900 mb-4">➕ Nueva Categoría</h2>
              
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Nombre de categoría"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  disabled={saving}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddCategory()}
                />
                <button
                  onClick={handleAddCategory}
                  disabled={saving}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg flex items-center justify-center gap-2 transition"
                >
                  <Plus className="w-5 h-5" />
                  {saving ? 'Guardando...' : 'Agregar Categoría'}
                </button>
              </div>

              {/* Agregar Subcategoría */}
              {selectedCategory && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-sm font-bold text-gray-900 mb-3">
                    Nueva Subcategoría en <span className="text-blue-600">{selectedCategory}</span>
                  </h3>
                  
                  <div className="space-y-3">
                    <input
                      type="text"
                      placeholder="Nombre de subcategoría"
                      value={newSubcategory}
                      onChange={(e) => setNewSubcategory(e.target.value)}
                      disabled={saving}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSubcategory()}
                    />
                    <button
                      onClick={handleAddSubcategory}
                      disabled={saving}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg flex items-center justify-center gap-2 transition"
                    >
                      <Plus className="w-5 h-5" />
                      {saving ? 'Guardando...' : 'Agregar Subcategoría'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Panel Derecho: Lista de Categorías */}
          <div className="lg:col-span-2">
            <div className="space-y-4">
              {Object.entries(categories).map(([category, subcategories]) => (
                <div
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`bg-white rounded-2xl p-6 shadow-lg cursor-pointer transition border-l-4 ${
                    selectedCategory === category
                      ? 'border-blue-500 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:shadow-xl'
                  }`}
                >
                  {/* Header Categoría */}
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-900">{category}</h3>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteCategory(category);
                      }}
                      disabled={saving}
                      className="p-2 text-red-600 hover:bg-red-50 disabled:opacity-50 rounded-lg transition"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Subcategorías */}
                  <div className="space-y-2">
                    {subcategories.map((subcat) => (
                      <div
                        key={subcat}
                        className="flex items-center justify-between bg-gray-100 px-4 py-2 rounded-lg hover:bg-gray-200 transition"
                      >
                        <span className="text-sm font-medium text-gray-700">
                          🏷️ {subcat}
                        </span>
                        {subcat !== 'Sin Subcategoría' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSubcategory(category, subcat);
                            }}
                            disabled={saving}
                            className="p-1 text-red-600 hover:bg-red-100 disabled:opacity-50 rounded transition"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}