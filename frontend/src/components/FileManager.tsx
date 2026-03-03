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
  ultimo_mes?: string;
}

interface FileManagerProps {
  onFilesChanged?: () => void;
}

export default function FileManager({ onFilesChanged }: FileManagerProps) {
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
        if (onFilesChanged) {
          onFilesChanged();
        }
      }
    } catch (error) {
      console.error('Error toggling file:', error);
    }
  };

  // ✅ NUEVO: Mostrar todos los archivos
  const showAllFiles = async () => {
    try {
      setLoading(true);
      // Activar todos los archivos inactivos
      const inactiveFiles = files.filter(f => !f.activo);
      
      for (const file of inactiveFiles) {
        await fetch(`http://localhost:8000/uploaded-files/${file.hash}/activate`, { 
          method: 'POST' 
        });
      }
      
      fetchFiles();
      if (onFilesChanged) {
        onFilesChanged();
      }
    } catch (error) {
      console.error('Error showing all files:', error);
    } finally {
      setLoading(false);
    }
  };

  // ✅ NUEVO: Ocultar todos los archivos
  const hideAllFiles = async () => {
    try {
      setLoading(true);
      // Desactivar todos los archivos activos
      const activeFilesArray = files.filter(f => f.activo);
      
      for (const file of activeFilesArray) {
        await fetch(`http://localhost:8000/uploaded-files/${file.hash}/deactivate`, { 
          method: 'POST' 
        });
      }
      
      fetchFiles();
      if (onFilesChanged) {
        onFilesChanged();
      }
    } catch (error) {
      console.error('Error hiding all files:', error);
    } finally {
      setLoading(false);
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
          if (onFilesChanged) {
            onFilesChanged();
          }
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
          if (onFilesChanged) {
            onFilesChanged();
          }
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

  const formatMes = (mes: string) => {
    if (!mes || mes === 'N/A') return 'N/A';
    
    const [year, month] = mes.split('-');
    const monthNames: Record<string, string> = {
      '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
      '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
      '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
    };
    
    return `${monthNames[month] || month} ${year}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            Gestión de Archivos
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Total: {files.length} archivos | Activos: {files.filter(f => f.activo).length} | Inactivos: {files.filter(f => !f.activo).length}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={fetchFiles}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            <RefreshCw size={18} />
            Actualizar
          </button>
          {/* ✅ NUEVO: Mostrar Todos */}
          <button
            onClick={showAllFiles}
            disabled={loading || files.every(f => f.activo)}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
            title="Mostrar todos los archivos"
          >
            <Eye size={18} />
            Mostrar Todos
          </button>
          {/* ✅ NUEVO: Ocultar Todos */}
          <button
            onClick={hideAllFiles}
            disabled={loading || files.every(f => !f.activo)}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
            title="Ocultar todos los archivos"
          >
            <EyeOff size={18} />
            Ocultar Todos
          </button>
          <button
            onClick={deleteAllFiles}
            className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            <Trash size={18} />
            Eliminar Todos
          </button>
        </div>
      </div>

      {/* Tabla */}
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
                Entidad Bancaria
              </th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                Mes de Corte
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
            {files.map((file) => (
              <tr key={file.hash} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                  {file.nombre}
                </td>
                <td className="px-6 py-4 text-sm text-center text-gray-600">
                  {file.movimientos}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {new Date(file.fecha_carga).toLocaleDateString('es-CL')}
                </td>
                <td className="px-6 py-4 text-sm text-center text-gray-600 font-medium">
                  {file.institucion || 'Desconocida'}
                </td>
                <td className="px-6 py-4 text-sm text-center text-gray-600">
                  {formatMes(file.ultimo_mes || 'N/A')}
                </td>
                <td className="px-6 py-4 text-center">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    file.activo
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {file.activo ? '✓ Activo' : '✗ Inactivo'}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => toggleFileActive(file.hash, file.activo)}
                      className="p-2 hover:bg-gray-100 rounded transition-colors"
                      title={file.activo ? 'Ocultar archivo' : 'Mostrar archivo'}
                    >
                      {file.activo ? (
                        <Eye size={18} className="text-blue-500" />
                      ) : (
                        <EyeOff size={18} className="text-gray-400" />
                      )}
                    </button>
                    <button
                      onClick={() => deleteFile(file.hash)}
                      className="p-2 hover:bg-gray-100 rounded transition-colors"
                      title="Eliminar archivo"
                    >
                      <Trash2 size={18} className="text-red-500" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {files.length === 0 && (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-600">No hay archivos cargados</p>
        </div>
      )}
    </div>
  );
}