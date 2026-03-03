import React, { useState, useRef } from 'react';
import { Upload, CheckCircle, AlertCircle, XCircle, Plus, X } from 'lucide-react';

interface Movement {
  id: number;
  fecha: string;
  descripcion: string;
  monto: number;
  tipo: 'ingreso' | 'gasto';
  archivo_referencia: string;
  categoria: string;
  subcategoria: string;
}

interface FileUploadProps {
  onMovementsLoaded: (movements: Movement[]) => void;
}

interface UploadResult {
  file: string;
  status: 'success' | 'error' | 'duplicate' | 'warning';
  message: string;
  movements?: number;
}

export default function FileUpload({ onMovementsLoaded }: FileUploadProps) {
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<'single' | 'batch'>('single');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [results, setResults] = useState<UploadResult[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const batchInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILES = 10;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setUploadProgress(0);
    setResults([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.status === 200 && data.status === 'success') {
        setResults([
          {
            file: file.name,
            status: 'success',
            message: `${data.movements_count} movimientos extraídos`,
            movements: data.movements_count,
          },
        ]);
        onMovementsLoaded(data.movements);
      } else if (response.status === 409) {
        setResults([
          {
            file: file.name,
            status: 'duplicate',
            message: 'Archivo duplicado',
          },
        ]);
      } else {
        setResults([
          {
            file: file.name,
            status: 'error',
            message: data.message,
          },
        ]);
      }
    } catch (error) {
      setResults([
        {
          file: file.name,
          status: 'error',
          message: 'Error de conexión',
        },
      ]);
    } finally {
      setLoading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleBatchFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    if (files.length > MAX_FILES) {
      alert(`Máximo ${MAX_FILES} archivos por carga`);
      return;
    }

    setSelectedFiles(Array.from(files));
  };

  const handleBatchUpload = async () => {
    if (selectedFiles.length === 0) return;

    setLoading(true);
    setUploadProgress(0);
    setResults([]);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await fetch('http://localhost:8000/upload-batch', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.status === 'completed') {
        setResults(data.resultados);
      }
    } catch (error) {
      setResults([
        {
          file: 'Carga masiva',
          status: 'error',
          message: 'Error de conexión',
        },
      ]);
    } finally {
      setLoading(false);
      setSelectedFiles([]);
      if (batchInputRef.current) {
        batchInputRef.current.value = '';
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="text-green-600" size={20} />;
      case 'duplicate':
        return <AlertCircle className="text-yellow-600" size={20} />;
      case 'error':
        return <XCircle className="text-red-600" size={20} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-50 border-green-300';
      case 'duplicate':
        return 'bg-yellow-50 border-yellow-300';
      case 'error':
        return 'bg-red-50 border-red-300';
      default:
        return 'bg-gray-50 border-gray-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Selector de modo */}
      <div className="flex gap-4">
        <button
          onClick={() => setMode('single')}
          className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
            mode === 'single'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
          }`}
        >
          📄 Carga Individual
        </button>
        <button
          onClick={() => setMode('batch')}
          className={`px-6 py-2 rounded-lg font-semibold transition-colors ${
            mode === 'batch'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
          }`}
        >
          📦 Carga Masiva (hasta {MAX_FILES})
        </button>
      </div>

      {/* CARGA INDIVIDUAL */}
      {mode === 'single' && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">📤 Cargar Archivo Individual</h2>

          <div className="border-2 border-dashed border-purple-300 rounded-lg p-12 text-center hover:border-purple-500 transition-colors bg-purple-50">
            <Upload className="mx-auto mb-4 text-purple-600" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Arrastra tu archivo aquí</h3>
            <p className="text-gray-600 mb-4">PDF, XLSX (BICE, CMR, Santander, etc.)</p>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.xlsx,.xls"
              onChange={handleFileChange}
              disabled={loading}
              className="hidden"
            />

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
            >
              {loading ? 'Procesando...' : 'Seleccionar Archivo'}
            </button>
          </div>

          {loading && (
            <div className="mt-6">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-center text-gray-600 mt-2">Extrayendo datos...</p>
            </div>
          )}

          {results.length > 0 && (
            <div className="mt-6 space-y-3">
              {results.map((result, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border flex items-start gap-3 ${getStatusColor(result.status)}`}
                >
                  {getStatusIcon(result.status)}
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{result.file}</p>
                    <p className="text-sm text-gray-700">{result.message}</p>
                    {result.movements && (
                      <p className="text-sm font-semibold text-gray-900 mt-1">
                        ✅ {result.movements} movimientos extraídos
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CARGA MASIVA */}
      {mode === 'batch' && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            📦 Carga Masiva (máximo {MAX_FILES} archivos)
          </h2>

          {/* Selector de archivos */}
          <div className="border-2 border-dashed border-blue-300 rounded-lg p-12 text-center hover:border-blue-500 transition-colors bg-blue-50 mb-6">
            <Plus className="mx-auto mb-4 text-blue-600" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Selecciona hasta {MAX_FILES} archivos
            </h3>
            <p className="text-gray-600 mb-4">Se procesarán en paralelo</p>

            <input
              ref={batchInputRef}
              type="file"
              accept=".pdf,.xlsx,.xls"
              multiple
              onChange={handleBatchFileSelect}
              disabled={loading}
              className="hidden"
            />

            <button
              onClick={() => batchInputRef.current?.click()}
              disabled={loading || selectedFiles.length >= MAX_FILES}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
            >
              {loading ? 'Procesando...' : 'Seleccionar Archivos'}
            </button>
          </div>

          {/* Lista de archivos seleccionados */}
          {selectedFiles.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">
                Archivos seleccionados: {selectedFiles.length}/{MAX_FILES}
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {selectedFiles.map((file, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-gray-100 p-3 rounded">
                    <span className="text-gray-700">{file.name}</span>
                    <button
                      onClick={() => {
                        setSelectedFiles(selectedFiles.filter((_, i) => i !== idx));
                      }}
                      className="text-red-600 hover:text-red-900"
                    >
                      <X size={18} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Botón de carga */}
          {selectedFiles.length > 0 && (
            <button
              onClick={handleBatchUpload}
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-3 rounded-lg font-semibold transition-colors mb-6"
            >
              {loading ? '⏳ Cargando...' : `🚀 Cargar ${selectedFiles.length} archivo(s)`}
            </button>
          )}

          {loading && (
            <div className="mt-6">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-center text-gray-600 mt-2">Procesando archivos...</p>
            </div>
          )}

          {/* Resultados */}
          {results.length > 0 && (
            <div className="mt-6">
              <h3 className="font-semibold text-gray-900 mb-3">Resultados:</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {results.map((result, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded border flex items-start gap-3 ${getStatusColor(result.status)}`}
                  >
                    {getStatusIcon(result.status)}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 break-words">{result.file}</p>
                      <p className="text-sm text-gray-700">{result.message}</p>
                      {result.movements && (
                        <p className="text-sm font-semibold text-gray-900">
                          ✅ {result.movements} movimientos
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}