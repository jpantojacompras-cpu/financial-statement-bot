import React, { useEffect, useState } from 'react';
import { Brain, TrendingUp, Trash2, RefreshCw } from 'lucide-react';

interface PatternEntry {
  pattern: string;
  categoria: string;
  subcategoria: string;
  veces_visto: number;
  confianza: number;
  last_updated: string;
}

interface LearningStats {
  patterns_learned: number;
  confidence_avg: number;
  top_patterns: PatternEntry[];
  recent_learning: { descripcion: string; categoria: string; timestamp: string }[];
  total_corrections: number;
}

export default function PatternExplorer() {
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingPattern, setDeletingPattern] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/learning-stats');
      const data = await res.json();
      if (data.status === 'success') {
        setStats(data);
      }
    } catch (err) {
      console.error('Error fetching learning stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleForgetPattern = async (pattern: string) => {
    if (!confirm(`¿Olvidar el patrón "${pattern}"?`)) return;
    setDeletingPattern(pattern);
    try {
      await fetch(`http://localhost:8000/api/patterns/${encodeURIComponent(pattern)}`, {
        method: 'DELETE',
      });
      await fetchStats();
    } catch (err) {
      console.error('Error deleting pattern:', err);
    } finally {
      setDeletingPattern(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Brain className="w-12 h-12 mx-auto mb-3 animate-pulse text-blue-400" />
        <p>Cargando estadísticas de aprendizaje…</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No se pudieron cargar las estadísticas.</p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Brain className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Explorador de Patrones IA</h1>
            <p className="text-gray-500 text-sm">Patrones que el sistema ha aprendido de tus correcciones</p>
          </div>
        </div>
        <button
          onClick={fetchStats}
          className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 text-sm font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-gray-500 text-sm">Patrones aprendidos</p>
          <p className="text-3xl font-bold text-blue-600 mt-1">{stats.patterns_learned}</p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-gray-500 text-sm">Confianza promedio</p>
          <p className="text-3xl font-bold text-green-600 mt-1">
            {(stats.confidence_avg * 100).toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-gray-500 text-sm">Correcciones totales</p>
          <p className="text-3xl font-bold text-purple-600 mt-1">{stats.total_corrections}</p>
        </div>
      </div>

      {/* Top patterns table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <div className="px-6 py-4 border-b flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-gray-500" />
          <h2 className="font-semibold text-gray-800">Top patrones aprendidos</h2>
        </div>
        {stats.top_patterns.length === 0 ? (
          <p className="p-6 text-gray-400 text-sm">
            Aún no hay patrones aprendidos. Usa el flujo de categorización para entrenar la IA.
          </p>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-6 py-3 text-left">Patrón</th>
                <th className="px-6 py-3 text-left">Categoría</th>
                <th className="px-6 py-3 text-left">Subcategoría</th>
                <th className="px-6 py-3 text-center">Veces visto</th>
                <th className="px-6 py-3 text-center">Confianza</th>
                <th className="px-6 py-3 text-center">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y text-sm">
              {stats.top_patterns.map((p) => {
                const conf = Math.round(p.confianza * 100);
                const barColor =
                  conf >= 80
                    ? 'bg-green-500'
                    : conf >= 50
                    ? 'bg-yellow-400'
                    : 'bg-red-400';
                return (
                  <tr key={p.pattern} className="hover:bg-gray-50">
                    <td className="px-6 py-3 font-mono text-gray-700">{p.pattern}</td>
                    <td className="px-6 py-3 text-gray-700">{p.categoria}</td>
                    <td className="px-6 py-3 text-gray-500">{p.subcategoria}</td>
                    <td className="px-6 py-3 text-center text-gray-700">{p.veces_visto}</td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2 justify-center">
                        <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className={`${barColor} h-full`} style={{ width: `${conf}%` }} />
                        </div>
                        <span className="text-xs text-gray-500">{conf}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-3 text-center">
                      <button
                        onClick={() => handleForgetPattern(p.pattern)}
                        disabled={deletingPattern === p.pattern}
                        className="text-red-400 hover:text-red-600 disabled:opacity-40"
                        title="Olvidar patrón"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Recent corrections */}
      {stats.recent_learning.length > 0 && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold text-gray-800">Correcciones recientes</h2>
          </div>
          <ul className="divide-y text-sm">
            {stats.recent_learning.slice(-10).reverse().map((entry, idx) => (
              <li key={idx} className="px-6 py-3 flex items-center justify-between">
                <span className="text-gray-700 font-medium">{entry.descripcion}</span>
                <span className="text-gray-500">→</span>
                <span className="text-blue-600">{entry.categoria}</span>
                <span className="text-gray-400 text-xs ml-auto">
                  {new Date(entry.timestamp).toLocaleDateString('es-CL')}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
