# Automatización P&L

Macro VBA que genera el Estado de Resultados mensual a partir del export de Contpaqi "Movimientos Auxiliares por Segmento de Negocio".

## Insumo
Archivo Excel exportado de Contpaqi con cuentas y saldos por segmento de negocio.

## Output
Archivo Excel con dos hojas:
- **CONSOLIDADO**: rubros del P&L con monto total y % sobre ingresos
- **POR SEGMENTO**: mismos rubros desglosados por unidad de negocio

## Uso
1. Abrir Excel y habilitar macros
2. Ejecutar `GenerarPL` (importar `macro/GenerarPL.bas` o usar el `.xlsm`)
3. Seleccionar el archivo de Contpaqi en el FileDialog
4. El P&L se genera automáticamente en la misma carpeta del insumo

## Mapeo de cuentas

| Cuenta | Rubro |
|--------|-------|
| 4110-xxx | VENTAS |
| 4210-xxx | UTILIDAD CAMBIARIA |
| 4310-xxx | OTROS INGRESOS |
| 4510-xxx | PRODUCTOS FINANCIEROS |
| 6100-001-xxx | SUELDOS |
| 6100-002-xxx | PREVISIÓN SOCIAL |
| 6100-004-xxx | CONTRIBUCIONES DE SEGURIDAD SOCIAL |
| 6100-005-xxx | IMPUESTO SOBRE NÓMINAS |
| 6100-006-xxx | GASTOS FIJOS |
| 6100-007-xxx | GASTOS VARIABLES |
| 6100-008-xxx | GASTOS FINANCIEROS |
| 6100-009-xxx | PÉRDIDA CAMBIARIA |
| 0000-000-800 / 8000-xxx | APLICACIÓN AL RESULTADO DEL EJERCICIO |
