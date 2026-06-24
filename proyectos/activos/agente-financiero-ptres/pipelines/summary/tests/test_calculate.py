from pipelines.summary.calculate import extraer_codigo, reconciliar


def test_extraer_codigo_limpio():
    assert extraer_codigo("26gmx7000.002", formato="limpio") == "26gmx7000.002"


def test_extraer_codigo_guion():
    assert extraer_codigo("26gmx3000.001-Cliente Uno- Proyecto Uno", formato="guion") == "26gmx3000.001"


def test_extraer_codigo_multilinea():
    assert extraer_codigo("26gmx3000.001\nCliente Uno\nProyecto Uno", formato="multilinea") == "26gmx3000.001"


def test_reconciliar_cancela_proyecto_facturado():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = [{"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Pagado"}]

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_nuevas=[])

    assert len(resultado["canceladas"]) == 1
    assert resultado["canceladas"][0]["proyecto"] == "26gmx3000.001"
    assert resultado["activas"] == []


def test_reconciliar_factura_cancelada_no_cuenta():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = [{"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Cancelado"}]

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_nuevas=[])

    assert resultado["activas"][0]["proyecto"] == "26gmx3000.001"
    assert resultado["canceladas"] == []


def test_reconciliar_detecta_provision_nueva():
    resultado = reconciliar(
        provisiones_mes_anterior=[],
        facturas_mes=[],
        provisiones_nuevas=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
    )

    assert resultado["nuevas"][0]["proyecto"] == "26gmx2000.005"
