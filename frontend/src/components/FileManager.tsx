import React, { useState, useEffect } from 'react';
import { Trash2, Eye, EyeOff, RefreshCw, Trash } from 'lucide-react';

interface UploadedFile {
  hash: string;
  nombre: string;
  fecha_carga: string;
  movimientos: number;
  activo: boolean;
  institucion?: string;
  tipo_producto?: string;
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

  const deleteAllFiles = async () => {
    if (files.length === 0) {
      alert('No hay archivos para eliminar');
      return;
    }

    if (confirm(`¿Eliminar TODOS los ${files.length} archivos? Esta acción no se puede deshacer.`)) {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/uploaded-files', {
          method: 'DELETE'
        });
        
        if (response.ok) {
          setFiles([]);
          alert('Todos los archivos han sido eliminados');
          fetchFiles();
        } else {
          alert('Error al eliminar archivos');
        }
      } catch (error) {
        console.error('Error deleting all files:', error);
        alert('Error al eliminar archivos');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header con botones de actualización y eliminar todos */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Gestión de Archivos
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Total: {files.length} archivos | Activos: {files.filter(f => f.activo).length} | Inactivos: {files.filter(f => !f.activo).length}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchFiles}
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            Actualizar
          </button>
          <button
            onClick={deleteAllFiles}
            disabled={loading || files.length === 0}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
          >
            <Trash size={18} />
            Eliminar Todos
          </button>
        </div>
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
                Institución
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                Tipo de Producto
              </th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">
                Confianza
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
                <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                  No hay archivos cargados
                </td>
              </tr>
            ) : (
              files.map(file => (
                <tr key={file.hash} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="truncate max-w-sm" title={file.nombre}>
                      {file.nombre}
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Hash: {file.hash.substring(0, 16)}...</p>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                      {file.movimientos}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {file.institucion || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {file.tipo_producto || '—'}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className="text-sm font-semibold text-green-600">100%</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(file.fecha_carga).toLocaleDateString('es-CL', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {file.activo ? (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-green-600">
                        <span className="w-2 h-2 bg-green-600 rounded-full"></span>
                        Activo
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-gray-500">
                        <span className="w-2 h-2 bg-gray-500 rounded-full"></span>
                        Inactivo
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center gap-3">
                      <button
                        onClick={() => toggleFileActive(file.hash, file.activo)}
                        title={file.activo ? 'Ocultar' : 'Mostrar'}
                        className="text-gray-600 hover:text-gray-900 transition-colors"
                      >
                        {file.activo ? (
                          <Eye size={18} />
                        ) : (
                          <EyeOff size={18} />
                        )}
                      </button>
                      <button
                        onClick={() => deleteFile(file.hash)}
                        title="Eliminar"
                        className="text-red-600 hover:text-red-900 transition-colors"
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
    </div>
  );
}