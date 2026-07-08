from pipelines.pl.interpret import clasificar_estructura


def test_clasifica_por_numero_y_excluye_lump_e_ignoradas():
    cuentas = [
        {"numero": "4110-001-001-000", "nombre": "VENTAS NACIONALES",
         "segmentos": {"ING": {"cargos": 0, "abonos": 999}}},  # lump: se excluye
        {"numero": "6100-008-001-000", "nombre": "COMISIONES BANCARIAS",
         "segmentos": {"ING": {"cargos": 30, "abonos": 0}}},  # 6008 -> EXPENSES
        {"numero": "2110-001-000-000", "nombre": "PROVEEDORES",
         "segmentos": {"ING": {"cargos": 5, "abonos": 0}}},  # balance: se ignora
    ]
    res = clasificar_estructura(cuentas, ventas_nacionales=[])
    numeros = {c["numero"]: c for c in res["cuentas"]}
    assert "4110-001-001-000" not in numeros
    assert "2110-001-000-000" not in numeros
    assert numeros["6100-008-001-000"]["rubro"] == "EXPENSES"


def test_ventas_nacionales_se_convierten_en_cuentas_incomes():
    res = clasificar_estructura(
        cuentas=[],
        ventas_nacionales=[
            {"cliente": "FORD MOTOR COMPANY", "segmento": "ING", "monto": 1500.0},
        ],
    )
    ns = res["cuentas"][0]
    assert ns["rubro"] == "INCOMES"
    assert ns["numero"].startswith("4")
    assert ns["segmentos"]["ING"] == {"cargos": 0, "abonos": 1500.0}
