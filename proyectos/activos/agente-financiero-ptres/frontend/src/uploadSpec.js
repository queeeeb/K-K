// Espejo de core/uploads.py UPLOAD_SPEC: qué archivos pide cada pipeline.
export const UPLOAD_SPEC = {
  summary: {
    base: 'Libro base (Summary_provision .xlsm)',
    facturacion: 'Detalle de Facturación',
    ds: 'Provisiones DS',
    engineering: 'Provisiones ES / Engineering',
    consulting: 'Overview Consulting',
  },
  pl: {
    movimientos: 'Movimientos Auxiliares por Segmento',
  },
}

export function slotsDe(pipeline) {
  return UPLOAD_SPEC[pipeline] ?? {}
}
