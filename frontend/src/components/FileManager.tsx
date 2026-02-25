import React, { useState, useEffect } from 'react';
import { Trash2, Eye, EyeOff, RefreshCw } from 'lucide-react';

interface UploadedFile {
  hash: string;
  nombre: string;
  fecha_carga: string;
  movimientos: number;
  activo: boolean;
}

export default function FileManager() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchFiles();
    const interval = setInterval(fetchFiles, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/uploaded-files');
      const data = await response.json();
      if (data.status === 'success') {
        setFiles(data.archivos || []);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFileActive = async (hash: string, currentActive: boolean) => {
    try {
      const endpoint = currentActive
        ? `http://localhost:8000/uploaded-files/${hash}/deactivate`
        : `http://localhost:8000/uploaded-files/${hash}/activate`;

      const response = await fetch(endpoint, { method: 'POST' });
      if (response.ok) {
        fetchFiles();
      }
    } catch (error) {
      console.error('Error toggling file:', error);
    }
  };

  const deleteFile = async (hash: string) => {
    if (confirm('¿Eliminar archivo?')) {
      try {
        const response = await fetch(
          `http://localhost:8000/uploaded-files/${hash}`,
          { method: 'DELETE' }
        );
        if (response.ok) {
          fetchFiles();
        }
      } catch (error) {
        console.error('Error deleting file:', error);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header con botón de actualización */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Archivos Cargados
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Total: {files.length} archivos | Activos: {files.filter(f => f.activo).length}
          </p>
        </div>
        <button
          onClick={fetchFiles}
          disabled={loading}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      {/* Tabla de archivos */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                Nombre del Archivo
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                Movimientos
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                Fecha de Carga
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                Estado
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {files.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center">
                  <p className="text-gray-600 font-medium">
                    Sin archivos cargados
                  </p>
                  <p className="text-gray-500 text-sm mt-1">
                    Carga un archivo desde la sección "Cargar"
                  </p>
                </td>
              </tr>
            ) : (
              files.map((file) => (
                <tr key={file.hash} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-semibold text-gray-900">
                        {file.nombre}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Hash: {file.hash.substring(0, 12)}...
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-blue-100 text-blue-800">
                      {file.movimientos}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(file.fecha_carga).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {file.activo ? (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
                        ✅ Activo
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-gray-100 text-gray-800">
                        ⏸️ Inactivo
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() =>
                          toggleFileActive(file.hash, file.activo)
                        }
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title={file.activo ? 'Desactivar' : 'Activar'}
                      >
                        {file.activo ? (
                          <Eye size={18} />
                        ) : (
                          <EyeOff size={18} />
                        )}
                      </button>
                      <button
                        onClick={() => deleteFile(file.hash)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Eliminar"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Estadísticas */}
      {files.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Total de Archivos</p>
            <p className="text-3xl font-bold text-gray-900">{files.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Archivos Activos</p>
            <p className="text-3xl font-bold text-green-600">
              {files.filter(f => f.activo).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Total de Movimientos</p>
            <p className="text-3xl font-bold text-blue-600">
              {files.reduce((sum, f) => sum + f.movimientos, 0).toLocaleString('es-CL')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}