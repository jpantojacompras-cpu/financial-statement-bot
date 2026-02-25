import React, { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';

interface CategoryManagerProps {
  categories: Record<string, string[]>;
  setCategories: (categories: Record<string, string[]>) => void;
}

export default function CategoryManager({
  categories,
  setCategories,
}: CategoryManagerProps) {
  const [newCategory, setNewCategory] = useState('');
  const [newSubcategory, setNewSubcategory] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const handleAddCategory = () => {
    if (newCategory.trim()) {
      setCategories({
        ...categories,
        [newCategory]: ['Sin Subcategoría'],
      });
      setNewCategory('');
    }
  };

  const handleAddSubcategory = () => {
    if (selectedCategory && newSubcategory.trim()) {
      setCategories({
        ...categories,
        [selectedCategory]: [
          ...categories[selectedCategory],
          newSubcategory,
        ],
      });
      setNewSubcategory('');
    }
  };

  const handleDeleteCategory = (category: string) => {
    const newCats = { ...categories };
    delete newCats[category];
    setCategories(newCats);
  };

  const handleDeleteSubcategory = (category: string, subcategory: string) => {
    setCategories({
      ...categories,
      [category]: categories[category].filter((s) => s !== subcategory),
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">⚙️ Gestión de Categorías</h2>

        {/* Add Category */}
        <div className="mb-8 p-4 bg-purple-50 rounded-lg">
          <h3 className="font-semibold mb-4">Agregar Nueva Categoría</h3>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Nombre de categoría..."
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-600"
            />
            <button
              onClick={handleAddCategory}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold"
            >
              <Plus size={20} />
              Agregar
            </button>
          </div>
        </div>

        {/* Categories List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Object.entries(categories).map(([category, subcategories]) => (
            <div
              key={category}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-semibold text-gray-900">{category}</h4>
                <button
                  onClick={() => handleDeleteCategory(category)}
                  className="text-red-600 hover:text-red-900"
                >
                  <Trash2 size={18} />
                </button>
              </div>

              <div className="space-y-2 mb-4">
                {subcategories.map((sub) => (
                  <div
                    key={sub}
                    className="flex items-center justify-between bg-gray-100 px-3 py-2 rounded"
                  >
                    <span className="text-sm text-gray-700">{sub}</span>
                    {sub !== 'Sin Subcategoría' && (
                      <button
                        onClick={() => handleDeleteSubcategory(category, sub)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {category !== 'Sin Categoría' && (
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Nueva subcategoría..."
                    value={
                      selectedCategory === category ? newSubcategory : ''
                    }
                    onChange={(e) => {
                      setSelectedCategory(category);
                      setNewSubcategory(e.target.value);
                    }}
                    className="flex-1 px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-purple-600"
                  />
                  <button
                    onClick={handleAddSubcategory}
                    disabled={selectedCategory !== category}
                    className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-3 py-1 rounded text-sm"
                  >
                    <Plus size={16} />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}