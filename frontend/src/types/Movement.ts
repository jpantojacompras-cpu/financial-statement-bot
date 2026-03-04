export interface Movement {
  id: string | number;
  fecha: string;
  descripcion: string;
  monto: number;
  tipo: 'ingreso' | 'gasto';
  archivo_referencia: string;
  categoria: string;
  subcategoria: string;
  confianza?: number;
  institucion?: string;
  tipo_producto?: string;
}