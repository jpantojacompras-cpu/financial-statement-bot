import '../styles/DataTable.css'

// Función auxiliar para formatear números
const formatCurrency = (value) => {
  if (value === null || value === undefined || isNaN(value)) return '$0'
  const number = Math.round(parseFloat(value))
  return '$' + number.toLocaleString('es-CL')
}

export default function DataTable({ movements }) {
  if (movements.length === 0) {
    return (
      <div className="data-table empty">
        <p>📭 No hay movimientos cargados aún.</p>
        <p>Ve a la sección "Cargar Archivos" para comenzar.</p>
      </div>
    )
  }

  // Calcular totales correctamente
  const totalIngresos = movements
    .filter(m => m.tipo === 'ingreso')
    .reduce((sum, m) => sum + (m.monto || 0), 0)

  const totalGastos = movements
    .filter(m => m.tipo === 'gasto')
    .reduce((sum, m) => sum + (m.monto || 0), 0)

  // SALDO = Ingresos - Gastos (no suma)
  const saldo = totalIngresos - totalGastos

  return (
    <div className="data-table">
      <h2>📋 Tabla de Movimientos ({movements.length})</h2>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Descripción</th>
              <th>Monto</th>
              <th>Tipo</th>
              <th>Categoría</th>
              <th>Subcategoría</th>
            </tr>
          </thead>
          <tbody>
            {movements.map((mov, idx) => (
              <tr key={idx} className={mov.tipo === 'ingreso' ? 'ingreso' : 'gasto'}>
                <td>{mov.fecha || '-'}</td>
                <td>{mov.descripcion || '-'}</td>
                <td className={mov.tipo === 'ingreso' ? 'positive' : 'negative'}>
                  {formatCurrency(mov.monto)}
                </td>
                <td>
                  {mov.tipo === 'ingreso' ? '📈 Ingreso' : '📉 Gasto'}
                </td>
                <td>{mov.categoria || 'Sin Categoría'}</td>
                <td>{mov.subcategoria || 'Sin Subcategoría'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-summary">
        <div className="summary-item">
          <span>Total Ingresos:</span>
          <span className="positive">
            {formatCurrency(totalIngresos)}
          </span>
        </div>
        <div className="summary-item">
          <span>Total Gastos:</span>
          <span className="negative">
            {formatCurrency(totalGastos)}
          </span>
        </div>
        <div className="summary-item">
          <span>Saldo:</span>
          <span className={saldo >= 0 ? 'positive' : 'negative'}>
            {formatCurrency(saldo)}
          </span>
        </div>
      </div>
    </div>
  )
}