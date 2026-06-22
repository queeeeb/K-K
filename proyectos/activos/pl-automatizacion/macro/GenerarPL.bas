Attribute VB_Name = "GenerarPL"
Option Explicit

' =============================================
' K&K Consulting — P&L Generator
' Input:  Contpaqi "Movimientos Auxiliares por Segmento de Negocio"
' Output: CONSOLIDATED + BY SEGMENT sheets
' =============================================

Private Const MAX_ACCTS As Long = 300
Private Const MAX_CAT   As Long = 200

Private nAccts As Long
Private acctNum(0 To 299) As String
Private acctNameES(0 To 299) As String
Private acctGrp(0 To 299) As String
Private acctAmts(0 To 299, 0 To 4) As Double

Private nCat As Long
Private catLabel(0 To 199) As String
Private catGrp(0 To 199) As String

Private bInNatSales As Boolean

' =============================================
' MAIN
' =============================================

Public Sub GenerarPL()
    On Error GoTo ErrorHandler

    nAccts = 0
    Dim k As Long, s As Long
    For k = 0 To 299
        acctNum(k) = "": acctNameES(k) = "": acctGrp(k) = ""
        For s = 0 To 4: acctAmts(k, s) = 0: Next s
    Next k

    Dim fdlg As FileDialog
    Set fdlg = Application.FileDialog(msoFileDialogFilePicker)
    fdlg.Title = "Select Contpaqi Movimientos Auxiliares file"
    fdlg.Filters.Clear
    fdlg.Filters.Add "Excel", "*.xlsx;*.xls;*.xlsm"
    If fdlg.Show = False Then Exit Sub
    Dim sRuta As String
    sRuta = fdlg.SelectedItems(1)

    Application.ScreenUpdating = False
    Application.DisplayAlerts = False

    Dim wbIn As Workbook
    Set wbIn = Workbooks.Open(sRuta, ReadOnly:=True)
    Dim wsIn As Worksheet
    Set wsIn = wbIn.Sheets(1)

    If Trim(CStr(wsIn.Cells(1, 1).Value)) = "" Then
        Err.Raise vbObjectError + 1, , "El archivo seleccionado no tiene el formato esperado (Movimientos Auxiliares por Segmento de Negocio)."
    End If

    Dim sPeriodo As String
    sPeriodo = Trim(CStr(wsIn.Cells(3, 1).Value))
    If sPeriodo = "" Then sPeriodo = Trim(CStr(wsIn.Cells(2, 1).Value))

    Call ParseInsumo(wsIn)
    wbIn.Close SaveChanges:=False
    Set wbIn = Nothing

    Dim wbOut As Workbook
    Set wbOut = Workbooks.Add
    Do While wbOut.Sheets.Count > 1
        wbOut.Sheets(wbOut.Sheets.Count).Delete
    Loop

    wbOut.Sheets(1).Name = "CONSOLIDATED"
    Call EscribirHoja(wbOut.Sheets("CONSOLIDATED"), True, sPeriodo)

    wbOut.Sheets.Add After:=wbOut.Sheets(wbOut.Sheets.Count)
    wbOut.Sheets(wbOut.Sheets.Count).Name = "BY SEGMENT"
    Call EscribirHoja(wbOut.Sheets("BY SEGMENT"), False, sPeriodo)

    wbOut.Sheets("CONSOLIDATED").Activate

    Dim outPath As String
    outPath = Left(sRuta, InStrRev(sRuta, "\")) & "PL_" & Format(Now, "YYYYMMDD_HHMM") & ".xlsx"
    wbOut.SaveAs outPath, XlFileFormat.xlOpenXMLWorkbook

    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    MsgBox "P&L generated:" & vbCrLf & outPath, vbInformation, "K&K Consulting"
    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    If Not wbIn Is Nothing Then wbIn.Close SaveChanges:=False
    MsgBox "No se pudo generar el P&L:" & vbCrLf & Err.Description, vbExclamation, "K&K Consulting"
End Sub

' =============================================
' PARSER
' =============================================

Private Sub ParseInsumo(wsIn As Worksheet)
    Dim totalRows As Long
    totalRows = wsIn.Cells(wsIn.Rows.Count, 1).End(xlUp).Row

    Dim curIdx As Long: curIdx = -1
    Dim curSeg As Long: curSeg = -1
    bInNatSales = False

    Dim i As Long
    For i = 1 To totalRows
        Dim colA As String, colB As String, colE As String
        colA = Trim(CStr(wsIn.Cells(i, 1).Value))
        colB = Trim(CStr(wsIn.Cells(i, 2).Value))
        colE = Trim(CStr(wsIn.Cells(i, 5).Value))

        If Len(colA) >= 8 And Mid(colA, 5, 1) = "-" And IsNumeric(Left(colA, 4)) Then
            Dim grp As String: grp = GetGrp(colA)
            If grp <> "" Then
                Dim nameToStore As String: nameToStore = colB
                If colA = "6100-007-033-007" Then nameToStore = "ESTACIONAMIENTOS VIAJE"
                curIdx = FindOrAdd(colA, nameToStore, grp)
            Else
                curIdx = -1
            End If
            bInNatSales = (colA = "4110-001-001-000")
            curSeg = -1

        ElseIf bInNatSales And curSeg >= 0 And colB = "Diario" Then
            Dim colD As String: colD = Trim(CStr(wsIn.Cells(i, 4).Value))
            If colD <> "" And IsNumeric(wsIn.Cells(i, 7).Value) Then
                Dim nsAmt As Double: nsAmt = CDbl(wsIn.Cells(i, 7).Value)
                Dim nsLabel As String: nsLabel = ENNatSales(colD)
                Dim nsIdx As Long: nsIdx = FindOrAdd("NS-" & nsLabel, nsLabel, "4110NS")
                If nsIdx >= 0 Then
                    acctAmts(nsIdx, curSeg) = acctAmts(nsIdx, curSeg) + nsAmt
                    acctAmts(nsIdx, 4) = acctAmts(nsIdx, 4) + nsAmt
                End If
            End If

        ElseIf Left(colA, 9) = "Segmento:" Then
            Dim segRaw As String
            segRaw = Trim(Mid(colA, 10))
            Dim sp As Long: sp = InStr(segRaw, " ")
            If sp > 0 Then segRaw = Trim(Mid(segRaw, sp + 1))
            curSeg = GetSegIdx(segRaw)

        ElseIf Left(colE, 10) = "Total Seg." Then
            If curIdx >= 0 And curSeg >= 0 Then
                Dim cargos As Double, abonos As Double, val As Double
                cargos = 0: abonos = 0
                If IsNumeric(wsIn.Cells(i, 6).Value) Then cargos = CDbl(wsIn.Cells(i, 6).Value)
                If IsNumeric(wsIn.Cells(i, 7).Value) Then abonos = CDbl(wsIn.Cells(i, 7).Value)
                If Left(acctGrp(curIdx), 1) = "4" Then
                    val = abonos - cargos
                Else
                    val = cargos - abonos
                End If
                acctAmts(curIdx, curSeg) = acctAmts(curIdx, curSeg) + val
                acctAmts(curIdx, 4) = acctAmts(curIdx, 4) + val
            End If
            curSeg = -1
        End If
    Next i
End Sub

Private Function GetGrp(c As String) As String
    If Left(c, 4) = "4110" Then
        GetGrp = "4110"
    ElseIf Left(c, 4) = "4210" Then
        GetGrp = IIf(Right(c, 12) = "-000-000-000", "", "4210")
    ElseIf Left(c, 4) = "4310" Then
        GetGrp = IIf(Right(c, 12) = "-000-000-000", "", "4310")
    ElseIf Left(c, 4) = "4510" Then
        GetGrp = IIf(Right(c, 12) = "-000-000-000", "", "4510")
    ElseIf Left(c, 8) = "6100-001" Then
        GetGrp = "6001"
    ElseIf Left(c, 8) = "6100-002" Then
        GetGrp = "6002"
    ElseIf Left(c, 8) = "6100-004" Then
        GetGrp = "6004"
    ElseIf Left(c, 8) = "6100-005" Then
        GetGrp = "6005"
    ElseIf Left(c, 8) = "6100-006" Then
        GetGrp = "6006"
    ElseIf Left(c, 8) = "6100-007" Then
        GetGrp = "6007"
    ElseIf Left(c, 8) = "6100-008" Then
        GetGrp = "6008"
    ElseIf Left(c, 8) = "6100-009" Then
        GetGrp = "6009"
    ElseIf Left(c, 11) = "0000-000-80" Or Left(c, 4) = "8000" Then
        GetGrp = "8000"
    Else
        GetGrp = ""
    End If
End Function

Private Function FindOrAdd(num As String, nameES As String, grp As String) As Long
    Dim k As Long
    For k = 0 To nAccts - 1
        If acctNum(k) = num Then FindOrAdd = k: Exit Function
    Next k
    If nAccts < MAX_ACCTS Then
        acctNum(nAccts) = num
        acctNameES(nAccts) = nameES
        acctGrp(nAccts) = grp
        FindOrAdd = nAccts
        nAccts = nAccts + 1
    Else
        FindOrAdd = -1
    End If
End Function

Private Function GetSegIdx(seg As String) As Long
    Select Case Trim(seg)
        Case "BO": GetSegIdx = 0
        Case "CONS OPS": GetSegIdx = 1
        Case "ING": GetSegIdx = 2
        Case "DIGITAL SOLUTIONS": GetSegIdx = 3
        Case Else: GetSegIdx = -1
    End Select
End Function

Private Function ENNatSales(raw As String) As String
    Select Case UCase(Trim(raw))
        Case "AUTOELECTRIC OF AMERICA, INC", "AUTOELECTRIC OF AMERICA": ENNatSales = "AUTOELECTRIC"
        Case "VOLKSWAGEN DE MEXICO", "VOLKSWAGEN DE MEXICO, S.A. DE C.V.": ENNatSales = "VOLKSWAGEN"
        Case "YANFENG SEATING MEXICO", "YANFENG SEATING MEXICO, S.A. DE C.V.": ENNatSales = "OTHER CLIENTS"
        Case "EQUIPO AUTOMOTRIZ AMERICANA", "EQUIPO AUTOMOTRIZ AMERICAN": ENNatSales = "OTHER CLIENTS"
        Case "SERVICIOS TURISTICOS EXCLUSIVOS": ENNatSales = "SERVICIOS TURISTICOS EXCLUSIVOS, S.A. DE C.V."
        Case "SCOTIABANK INVERLAT", "SCOTIABANK": ENNatSales = "SCOTIA BANK"
        Case "AIRBUS HELICOPTERS MEXICO", "AIRBUS HELICOPTERS": ENNatSales = "AIRBUS HELICOPTERS MEXICO QUERETARO"
        Case "SMX SERVICES & CONSULTING", "SMX SERVICES AND CONSULTING": ENNatSales = "SMX SERVICES & CONSULTING"
        Case Else: ENNatSales = UCase(Trim(raw))
    End Select
End Function

' =============================================
' TRANSLATION ES -> EN
' =============================================

Private Function EN(nameES As String, grp As String) As String
    Dim n As String: n = UCase(Trim(nameES))

    If grp = "4110" Then
        If n = "VENTAS NACIONALES" Then
            EN = "NATIONAL SALES"
        ElseIf Left(n, 10) = "PROVISIONE" Then
            Dim raw As String: raw = UCase(Trim(Mid(nameES, 12)))
            Select Case raw
                Case "BMW":                          EN = "  ACCRUED REVENUE BMW"
                Case "P3 AUTOMOTIVE":                EN = "  ACCRUED REVENUE P3 AUTOMOTIVE"
                Case "MAGNA SLP":                    EN = "  ACCRUED REVENUE MAGNA SLP"
                Case "FORD MOTOR COMPANY S.A. DE C.V.": EN = "  ACCRUED REVENUE FORD"
                Case "NEW TRANSPORT APPLICATION":    EN = "  ACCRUED REVENUE NEW TRANSPORT APPLICATION"
                Case "P3 USA":                       EN = "  ACCRUED REVENUE P3 USA"
                Case "SERVICIOS TURISTICOS EXCLUSIVOS": EN = "  ACCRUED SERVICIOS TURISTICOS EXCLUSIVOS"
                Case "SCOTIABANK INVERLAT":          EN = "  ACCRUED REVENUE SCOTIA BANK"
                Case "LINDE + WIEMANN":              EN = "  ACCRUED REVENUE LINDE + WIEMANN"
                Case "YANFENG":                      EN = "  ACCRUED REVENUE YANGFENG"
                Case "ELANCO":                       EN = "  ACCRUED REVENUE ELANCO"
                Case "P3 KOREA":                     EN = "  ACCRUED REVENUE P3 KOREA"
                Case "GENTHERM DE MEXICO":           EN = "  ACCRUED REVENUE GENTHERM DE MEXICO"
                Case "FAURECIA":                     EN = "  ACCRUED REVENUE FAURECIA"
                Case "AIRBUS":                       EN = "  ACCRUED REVENUE AIRBUS"
                Case "DAIKIN":                       EN = "  ACCRUED REVENUE DAIKIN"
                Case "VOLKSWAGEN":                   EN = "  ACCRUED REVENUE VOLKSWAGEN"
                Case "TEKLAS":                       EN = "  ACCRUED REVENUE TEKLAS"
                Case "PLASTIC OMNIUM":               EN = "  ACCRUED REVENUE PLASTIC OMNIUM"
                Case "AUTOELECTRIC":                 EN = "  ACCRUED REVENUE AUTOELECTRIC"
                Case "P3 DIGITAL SERVICIO GMBH":    EN = "  ACCRUED REVENUE P3 DIGITAL SERVICE GMBH"
                Case Else:                           EN = "  ACCRUED REVENUE OTHERS PROJECTS"
            End Select
        Else
            EN = nameES
        End If
        Exit Function
    End If

    If InStr(n, "CAPACITACI") > 0 Then EN = "  TRAINING": Exit Function

    Select Case n
        ' Other Incomes
        Case "UTILIDAD CAMBIARIA": EN = "  E.R. FLUCTUATION PROFIT"
        Case "OTROS INGRESOS": EN = "  OTHER INCOME"
        Case "INTERESES A FAVOR": EN = "  INTEREST"
        Case "PRODUCTOS FINANCIEROS": EN = "  FINANCIAL PRODUCTS"
        ' Salaries 6001
        Case "SUELDOS Y SALARIOS": EN = "  GENERAL DEP"
        Case "VACACIONES": EN = "  VACATIONS"
        Case "PRIMA VACACIONAL": EN = "  VACATIONS PREMIUM"
        Case "AGUINALDO": EN = "  CHRISTMAS BONUS"
        Case "INDEMNIZACION": EN = "  INDEMNITY"
        Case "PREMIOS DE ASISTENCIA": EN = "  ASSITANCY BONUS"
        Case "PREMIOS DE PUNTUALIDAD": EN = "  PUNCTUALITY BONUS"
        Case "BONO PRODUCTIVIDAD": EN = "  PRODUCTIVITY BONUS"
        Case "GRATIFICACION ESPECIAL": EN = "  SPECIAL GRATIFICATION"
        Case "PRIMA DE ANTIGUEDAD": EN = "  SENIORITY PREMIUM"
        ' Social benefits 6002
        Case "VALES PARA DESPENSA": EN = "  FOOD COUPONS"
        ' Security contributions 6004
        Case "I.M.S.S.": EN = "  SOCIAL SECURITY CONTRIBUTIONS"
        Case "R.C.V.": EN = "  INSURANCE RETIR., DISMISS. AND OLD"
        Case "5% INFONAVIT": EN = "  5% CONTRIB. WORKER'S HOUSING FUND"
        ' Payroll tax 6005
        Case "IMPUESTOS SOBRE NOMINA": EN = "  PAYROLL TAX"
        ' Fixed expenses 6006
        Case "TELEFONO": EN = "  TELEPHONE"
        Case "COMBUSTIBLES Y LUBRICANTES": EN = "  FUEL AND LUBRICANTS"
        Case "COMISIONES EDENRED": EN = "  COMMISSION ON FOOD COUPONS"
        Case "ARTICULO DE LIMPIEZA": EN = "  ARTICLE CLEANING"
        Case "ARTICULOS DE OFICINA Y PAPELERIA": EN = "  STATIONERY"
        Case "DESPENSA DE OFICINA": EN = "  OFFICE PANTRY"
        Case "ARRENDAMIENTO DE INMUEBLE PERSONAS MORALES": EN = "  LEASING REAL ESTATE TO INDIVIDUAL"
        Case "ARRENDAMIENTO DE INMUEBLE PERSONAS FISICAS": EN = "  LEASE OF PROPERTY PF"
        Case "ARRENDAMIENTO DE EQUIPO COMPUTO": EN = "  LEASING COMPUTER EQUIPMENT"
        Case "ARRENDAMIENTO DE EQUIPO DE TRANSPORTE": EN = "  LEASING TRANSPORT. EQUIPMENT"
        Case "DEPRECIACION EQUIPO OFICINA": EN = "  DEPRECIATION OFFICE EQUIPMENT"
        Case "DEPRECIACION EQUIPO DE COMPUTO": EN = "  DEPRECIATION COMPUTER EQUIPMENT"
        Case "ACTIVOS MENORES": EN = "  MINOR ASSETS"
        Case "DEPRECIACION MEJORAS DE EDIFICIOS": EN = "  DEPRECIATION BUILDING IMPROVEMENTS"
        ' Variable expenses 6007
        Case "MANTENIMIENTO OFICINAS": EN = "  MAINTENANCE OFFICE"
        Case "SOFTWARE DE COMPUTO": EN = "  COMPUTER SOFTWARE"
        Case "ESTACIONAMIENTOS": EN = "  PARKING"
        Case "ESTACIONAMIENTOS VIAJE": EN = "  OTHER TRAVEL EXPENSES"
        Case "MENSAJERIA": EN = "  COURIER"
        Case "SEGUROS Y FIANZAS": EN = "  INSURANCE AND BONDS"
        Case "CUOTAS Y SUSCRIPCIONES": EN = "  FEES AND SUBSCRIPTIONS"
        Case "UNIFORMES": EN = "  UNIFORMS"
        Case "NUBE/SOFTWARE": EN = "  CLOUD/SOFTWARE"
        Case "DOMINIO": EN = "  DOMAIN"
        Case "SERVICIOS POR ASESORIA": EN = "  ADVISORY SERVICES"
        Case "HONORARIOS PERSONAS MORALES": EN = "  FEES PAID TO CORPORATIONS"
        Case "SERVICIOS PROFESIONALES": EN = "  FEES PAID INDIVIDUALS ONE"
        Case "NO DEDUCIBLES": EN = "  NON-DEDUCTIBLE"
        Case "HOSPEDAJE": EN = "  LODGING"
        Case "ALIMENTACION": EN = "  MEALS"
        Case "TRANSPORTE": EN = "  TRANSPORTATION"
        Case "USO O GOCE TEMPORAL DE AUTOMOVIL": EN = "  TEMPORARY USE OR ENJOYMENT OF AUTOMOBILE"
        Case "CASETAS": EN = "  HIGHWAY QUOTAS"
        Case "BOLETOS DE AVION": EN = "  AIRPLANE TICKETS"
        Case "GASTOS VIAJE EN GENERAL": EN = "  GENERAL TRAVEL EXPENSES"
        Case "OTROS GASTOS DE VIAJE": EN = "  OTHER TRAVEL EXPENSES"
        Case "IMPUESTO SOBRE HOSPEDAJE": EN = "  HOTEL TAX"
        Case "OTROS GASTOS": EN = "  OTHER EXPENSES"
        Case "HERRAMIENTAS": EN = "  TOOLS"
        Case "HARDWARE": EN = "  HARDWARE"
        Case "SERVICIOS P3 AUTOMOTIVE GMBH": EN = "  P3 AUTOMOTIVE GMBH"
        Case "P3 GLOBAL GMBH SERVICES": EN = "  P3 GLOBAL GMBH SERVICES"
        Case "SERVICIOS P3 USA, INC.": EN = "  P3 SERVICES USA"
        Case "P3 SERVICES DIGITAL GMBH": EN = "  P3 SERVICES DIGITAL"
        ' Financial expenses 6008
        Case "COMISIONES BANCARIAS": EN = "  BANK COMMISIONS"
        Case "INTERESES A CARGO": EN = "  INTEREST EXPENSE"
        ' Other expenses 6009
        Case "PERDIDA CAMBIARIA": EN = "  E.R. FLUCTUATION LOSS"
        ' Taxes 8000
        Case "I.S.R. DEL EJERCICIO": EN = "  INCOME TAX OF THE YEAR"
        Case "P.T.U.": EN = "  PTU"
        Case Else: EN = "  " & nameES
    End Select
End Function

' =============================================
' CATALOG (expenses + other sections only; 4110 is dynamic)
' =============================================

Private Sub AddCat(lbl As String, grp As String)
    If nCat < MAX_CAT Then
        catLabel(nCat) = lbl: catGrp(nCat) = grp: nCat = nCat + 1
    End If
End Sub

Private Sub InitCatalog()
    nCat = 0
    ' National Sales — fixed catalog (order matches reference)
    AddCat "    FORD MOTOR COMPANY", "4110NSC"
    AddCat "    BMW SLP", "4110NSC"
    AddCat "    CF MOTO", "4110NSC"
    AddCat "    FRAENKISCHE", "4110NSC"
    AddCat "    CONSORCIO INDUSTRIAL MEXICANO DE AUTOPARTES", "4110NSC"
    AddCat "    KIEKERT DE MEXICO", "4110NSC"
    AddCat "    LEAR CORPORATION", "4110NSC"
    AddCat "    BORGWARNER", "4110NSC"
    AddCat "    YANGFENG", "4110NSC"
    AddCat "    PEASA", "4110NSC"
    AddCat "    PISA", "4110NSC"
    AddCat "    DRIV DE MEXICO", "4110NSC"
    AddCat "    DIVERSE", "4110NSC"
    AddCat "    MOLINA GAULAND & ZEITGEIST", "4110NSC"
    AddCat "    AUTOELECTRIC", "4110NSC"
    AddCat "    TW DISTRIBUIDORES INDUSTRIALES", "4110NSC"
    AddCat "    LINDE + WIEMANN", "4110NSC"
    AddCat "    AKKY ONLINE SOLUTIONS", "4110NSC"
    AddCat "    CONSORCIO CONSULTOR LAR", "4110NSC"
    AddCat "    QEV TECHNOLOGIES SL", "4110NSC"
    AddCat "    ELANCO", "4110NSC"
    AddCat "    ELEKTROKONTAKT", "4110NSC"
    AddCat "    SERVICIOS TURISTICOS EXCLUSIVOS, S.A. DE C.V.", "4110NSC"
    AddCat "    DHL LAST MILE DELIVERY", "4110NSC"
    AddCat "    NEW TRANSPORT APPLICATIONS", "4110NSC"
    AddCat "    FEHRER", "4110NSC"
    AddCat "    TEKLAS", "4110NSC"
    AddCat "    FAURECIA", "4110NSC"
    AddCat "    INSTITUTO NACIONAL DE CIENCIAS MEDICAS", "4110NSC"
    AddCat "    DAIKIN", "4110NSC"
    AddCat "    SAN LUIS METAL FORMING", "4110NSC"
    AddCat "    VOLKSWAGEN", "4110NSC"
    AddCat "    EQUIPO AUTOMOTRIZ AMERICANA", "4110NSC"
    AddCat "    AIRBUS HELICOPTERS MEXICO QUERETARO", "4110NSC"
    AddCat "    TB SEWTECH DE MEXICO", "4110NSC"
    AddCat "    DIGIT AUTOMOTIVE", "4110NSC"
    AddCat "    SCOTIA BANK", "4110NSC"
    AddCat "    PLASTIC OMNIUM", "4110NSC"
    AddCat "    PLASTIC TEC", "4110NSC"
    AddCat "    KNIPPING", "4110NSC"
    AddCat "    EUROTRANCIATURA DE MEXICO", "4110NSC"
    AddCat "    BMC DE MEXICO", "4110NSC"
    AddCat "    SMX SERVICES & CONSULTING", "4110NSC"
    AddCat "    NOMEA GMBH", "4110NSC"
    AddCat "    P3 KOREA", "4110NSC"
    AddCat "    OTHER CLIENTS", "4110NSC"
    ' 6001 Salaries
    AddCat "  GENERAL DEP", "6001"
    AddCat "  VACATIONS", "6001"
    AddCat "  VACATIONS PREMIUM", "6001"
    AddCat "  CHRISTMAS BONUS", "6001"
    AddCat "  INDEMNITY", "6001"
    AddCat "  ASSITANCY BONUS", "6001"
    AddCat "  PUNCTUALITY BONUS", "6001"
    AddCat "  PRODUCTIVITY BONUS", "6001"
    AddCat "  SPECIAL GRATIFICATION", "6001"
    AddCat "  SENIORITY PREMIUM", "6001"
    ' 6002 Social benefits
    AddCat "  FOOD COUPONS", "6002"
    ' 6004 Security contributions
    AddCat "  SOCIAL SECURITY CONTRIBUTIONS", "6004"
    AddCat "  INSURANCE RETIR., DISMISS. AND OLD", "6004"
    AddCat "  5% CONTRIB. WORKER'S HOUSING FUND", "6004"
    ' 6005 Payroll tax
    AddCat "  PAYROLL TAX", "6005"
    ' 6006 Fixed expenses
    AddCat "  TELEPHONE", "6006"
    AddCat "  FUEL AND LUBRICANTS", "6006"
    AddCat "  COMMISSION ON FOOD COUPONS", "6006"
    AddCat "  ARTICLE CLEANING", "6006"
    AddCat "  STATIONERY", "6006"
    AddCat "  OFFICE PANTRY", "6006"
    AddCat "  LEASING REAL ESTATE TO INDIVIDUAL", "6006"
    AddCat "  LEASE OF PROPERTY PF", "6006"
    AddCat "  LEASING COMPUTER EQUIPMENT", "6006"
    AddCat "  LEASING TRANSPORT. EQUIPMENT", "6006"
    AddCat "  DEPRECIATION OFFICE EQUIPMENT", "6006"
    AddCat "  DEPRECIATION COMPUTER EQUIPMENT", "6006"
    AddCat "  MINOR ASSETS", "6006"
    AddCat "  DEPRECIATION BUILDING IMPROVEMENTS", "6006"
    ' 6007 Variable expenses
    AddCat "  MAINTENANCE OFFICE", "6007"
    AddCat "  COMPUTER SOFTWARE", "6007"
    AddCat "  PARKING", "6007"
    AddCat "  COURIER", "6007"
    AddCat "  INSURANCE AND BONDS", "6007"
    AddCat "  FEES AND SUBSCRIPTIONS", "6007"
    AddCat "  UNIFORMS", "6007"
    AddCat "  CLOUD/SOFTWARE", "6007"
    AddCat "  DOMAIN", "6007"
    AddCat "  ADVISORY SERVICES", "6007"
    AddCat "  FEES PAID TO CORPORATIONS", "6007"
    AddCat "  FEES PAID INDIVIDUALS ONE", "6007"
    AddCat "  NON-DEDUCTIBLE", "6007"
    AddCat "  LODGING", "6007"
    AddCat "  MEALS", "6007"
    AddCat "  TRANSPORTATION", "6007"
    AddCat "  TEMPORARY USE OR ENJOYMENT OF AUTOMOBILE", "6007"
    AddCat "  HIGHWAY QUOTAS", "6007"
    AddCat "  AIRPLANE TICKETS", "6007"
    AddCat "  GENERAL TRAVEL EXPENSES", "6007"
    AddCat "  OTHER TRAVEL EXPENSES", "6007"
    AddCat "  HOTEL TAX", "6007"
    AddCat "  OTHER EXPENSES", "6007"
    AddCat "  TOOLS", "6007"
    AddCat "  HARDWARE", "6007"
    AddCat "  TRAINING", "6007"
    AddCat "  P3 AUTOMOTIVE GMBH", "6007"
    AddCat "  P3 GLOBAL GMBH SERVICES", "6007"
    AddCat "  P3 SERVICES USA", "6007"
    AddCat "  P3 SERVICES DIGITAL", "6007"
    ' 6008 Financial expenses
    AddCat "  BANK COMMISIONS", "6008"
    AddCat "  INTEREST EXPENSE", "6008"
    ' Other Incomes (4OI = 4210+4310+4510)
    AddCat "  E.R. FLUCTUATION PROFIT", "4OI"
    AddCat "  OTHER INCOME", "4OI"
    AddCat "  INTEREST", "4OI"
    AddCat "  FINANCIAL PRODUCTS", "4OI"
    ' Other Expenses (6009)
    AddCat "  E.R. FLUCTUATION LOSS", "6009"
    ' Accrued Taxes (8000)
    AddCat "  INCOME TAX OF THE YEAR", "8000"
    AddCat "  PTU", "8000"
    ' Accrued Revenue — fixed catalog matching reference (4OAR)
    AddCat "  ACCRUED REVENUE P3 USA", "4OAR"
    AddCat "  ACCRUED REVENUE P3 AUTOMOTIVE", "4OAR"
    AddCat "  ACCRUED REVENUE P3 KOREA", "4OAR"
    AddCat "  ACCRUED REVENUE FORD", "4OAR"
    AddCat "  ACCRUED REVENUE MAGNA SLP", "4OAR"
    AddCat "  ACCRUED REVENUE P3 DIGITAL SERVICE GMBH", "4OAR"
    AddCat "  ACCRUED REVENUE BMW", "4OAR"
    AddCat "  ACCRUED REVENUE LEAR", "4OAR"
    AddCat "  ACCRUED REVENUE TEKLAS", "4OAR"
    AddCat "  ACCRUED REVENUE NEW TRANSPORT APPLICATION", "4OAR"
    AddCat "  ACCRUED REVENUE YANGFENG", "4OAR"
    AddCat "  ACCRUED INSTITUTO NACIONAL DE SCIENCIAS MEDICAS", "4OAR"
    AddCat "  ACCRUED SERVICIOS TURISTICOS EXCLUSIVOS", "4OAR"
    AddCat "  ACCRUED REVENUE AIRBUS", "4OAR"
    AddCat "  ACCRUED REVENUE DAIKIN", "4OAR"
    AddCat "  ACCRUED REVENUE VOLKSWAGEN", "4OAR"
    AddCat "  ACCRUED REVENUE AUTOELECTRIC", "4OAR"
    AddCat "  ACCRUED REVENUE CIENCIAS MEDICAS", "4OAR"
    AddCat "  ACCRUED REVENUE ELANCO", "4OAR"
    AddCat "  ACCRUED REVENUE LINDE + WIEMANN", "4OAR"
    AddCat "  ACCRUED REVENUE FRAENKISCHE", "4OAR"
    AddCat "  ACCRUED REVENUE SCOTIA BANK", "4OAR"
    AddCat "  ACCRUED REVENUE PLASTIC OMNIUM", "4OAR"
    AddCat "  ACCRUED REVENUE FAURECIA", "4OAR"
    AddCat "  ACCRUED REVENUE GENTHERM DE MEXICO", "4OAR"
    AddCat "  ACCRUED REVENUE OTHERS PROJECTS", "4OAR"
End Sub

Private Function LookupAmt(labelEN As String, grp As String, segIdx As Long) As Double
    Dim k As Long
    LookupAmt = 0
    For k = 0 To nAccts - 1
        Dim matches As Boolean
        If grp = "4OI" Then
            matches = (acctGrp(k) = "4210" Or acctGrp(k) = "4310" Or acctGrp(k) = "4510") _
                      And EN(acctNameES(k), acctGrp(k)) = labelEN
        ElseIf grp = "4OAR" Then
            matches = acctGrp(k) = "4110" And EN(acctNameES(k), "4110") = labelEN
        ElseIf grp = "4110NSC" Then
            If Trim(labelEN) = "OTHER CLIENTS" Then
                Dim isKnown As Boolean: isKnown = False
                Dim ci As Long
                For ci = 0 To nCat - 1
                    If catGrp(ci) = "4110NSC" And Trim(catLabel(ci)) <> "OTHER CLIENTS" Then
                        If Trim(catLabel(ci)) = acctNameES(k) Then isKnown = True: Exit For
                    End If
                Next ci
                matches = acctGrp(k) = "4110NS" And Not isKnown
            Else
                matches = acctGrp(k) = "4110NS" And acctNameES(k) = Trim(labelEN)
            End If
        Else
            matches = acctGrp(k) = grp And EN(acctNameES(k), grp) = labelEN
        End If
        If matches Then LookupAmt = LookupAmt + acctAmts(k, segIdx)
    Next k
End Function

' =============================================
' SHEET WRITER
' BY SEGMENT columns: A=DESC, B=BO, C=%BO, D=CONSUL OP, E=%CONS,
'                     F=ENGINEERING, G=%ENG, H=DS, I=%DS, J=TOTAL, K=%TOTAL
' Segment index: s=0 BO, s=1 ING, s=2 CONS OPS, s=3 DS, s=4 TOTAL
' Column mapping: amtCol = 2 + s*2, pctCol = 3 + s*2
' =============================================

Private Sub EscribirHoja(ws As Worksheet, isConsolidado As Boolean, periodo As String)
    Call InitCatalog()

    Dim r As Long: r = 1
    Dim nCols As Long: nCols = IIf(isConsolidado, 3, 11)
    Dim c As Long, s As Long, k As Long

    Dim C_HEADER As Long:   C_HEADER = RGB(128, 0, 0)
    Dim C_WHITE As Long:    C_WHITE = RGB(255, 255, 255)
    Dim C_SUBTOTAL As Long: C_SUBTOTAL = RGB(153, 204, 255)

    ws.Cells.Font.Name = "Arial"
    ws.Cells.Font.Size = 9

    ' Header
    ws.Cells(r, 1).Value = "P-TRES GROUP, S.A.P.I. DE C.V."
    ws.Cells(r, 1).Font.Bold = True: ws.Cells(r, 1).Font.Size = 12
    r = r + 1
    ws.Cells(r, 1).Value = "Profit and Loss Statement" & IIf(isConsolidado, " — ", " by Segment — ") & periodo
    ws.Cells(r, 1).Font.Bold = True: ws.Cells(r, 1).Font.Size = 12
    r = r + 2

    ' Column headers
    ws.Cells(r, 1).Value = "DESCRIPTION"
    If isConsolidado Then
        ws.Cells(r, 2).Value = "TOTAL"
        ws.Cells(r, 3).Value = "%"
    Else
        ws.Cells(r, 2).Value = "BACK OFFICE"
        ws.Cells(r, 3).Value = "%"
        ws.Cells(r, 4).Value = "CONSUL OP"
        ws.Cells(r, 5).Value = "%"
        ws.Cells(r, 6).Value = "ENGINEERING"
        ws.Cells(r, 7).Value = "%"
        ws.Cells(r, 8).Value = "DIGITAL SOLUTIONS"
        ws.Cells(r, 9).Value = "%"
        ws.Cells(r, 10).Value = "TOTAL"
        ws.Cells(r, 11).Value = "%"
    End If
    With ws.Range(ws.Cells(r, 1), ws.Cells(r + 1, nCols))
        .Font.Bold = True
        .Interior.Color = C_HEADER
        .Font.Color = C_WHITE
        .HorizontalAlignment = xlCenter
        .VerticalAlignment = xlCenter
        .WrapText = True
    End With
    Dim hc As Long
    For hc = 1 To nCols
        ws.Range(ws.Cells(r, hc), ws.Cells(r + 1, hc)).Merge
    Next hc
    ws.Rows(r).RowHeight = 24
    ws.Rows(r + 1).RowHeight = 18
    r = r + 2

    ' Base incomes per segment (% denominator)
    ' Exclude 4110-001-001-000 (lump sum replaced by 4110NS individual clients)
    Dim baseIncSeg(0 To 4) As Double
    For k = 0 To nAccts - 1
        If (acctGrp(k) = "4110" And acctNum(k) <> "4110-001-001-000") Or acctGrp(k) = "4110NS" Then
            For s = 0 To 4: baseIncSeg(s) = baseIncSeg(s) + acctAmts(k, s): Next s
        End If
    Next k

    ' ---- INCOMES (4110) — dynamic ----
    ws.Cells(r, 1).Value = "Incomes"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1

    Dim totInc(0 To 4) As Double

    ' NATIONAL SALES — header only (no amounts), then fixed catalog with dynamic amounts
    ws.Cells(r, 1).Value = "  NATIONAL SALES"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    For c = 0 To nCat - 1
        If catGrp(c) = "4110NSC" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totInc, baseIncSeg)
            r = r + 1
        End If
    Next c

    ' Direct international clients (4110-002-XXX, non-zero)
    For k = 0 To nAccts - 1
        If acctGrp(k) = "4110" And Left(acctNum(k), 8) = "4110-002" And acctAmts(k, 4) <> 0 Then
            Call WriteParsedRow(ws, r, EN(acctNameES(k), "4110"), k, isConsolidado, totInc, baseIncSeg)
            r = r + 1
        End If
    Next k

    ' ACCRUED REVENUE — fixed catalog matching reference
    For c = 0 To nCat - 1
        If catGrp(c) = "4OAR" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totInc, baseIncSeg)
            r = r + 1
        End If
    Next c

    Call WriteSumRow(ws, r, "Incomes Total", totInc, isConsolidado, C_SUBTOTAL, baseIncSeg)
    r = r + 1
    If isConsolidado Then Call WritePctRow(ws, r, "% of the Total Incomes", totInc(4), totInc(4))
    r = r + 2

    ' ---- EXPENSES (6001-6008) ----
    ws.Cells(r, 1).Value = "Expenses"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1

    Dim totExp(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "6001" Or catGrp(c) = "6002" Or catGrp(c) = "6004" Or _
           catGrp(c) = "6005" Or catGrp(c) = "6006" Or catGrp(c) = "6007" Or _
           catGrp(c) = "6008" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totExp, baseIncSeg)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Expenses Total", totExp, isConsolidado, C_SUBTOTAL, baseIncSeg)
    r = r + 1
    If isConsolidado Then Call WritePctRow(ws, r, "% of the Total Expenses", totExp(4), totInc(4))
    r = r + 2

    ' ---- OPERATING PROFIT ----
    Dim totOp(0 To 4) As Double
    For s = 0 To 4: totOp(s) = totInc(s) - totExp(s): Next s
    ws.Cells(r, 1).Value = "OPERATING PROFIT (OR LOSS) BEFORE ALLOCATIONS"
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols)): .Font.Bold = True: End With
    Call WriteAmts(ws, r, totOp, isConsolidado, baseIncSeg)
    r = r + 2

    ' ---- ALLOCATION BO & GMBH SERVICES ----
    ' Entire BO Expenses Total is redistributed to CONS OPS/ING/DS by income share,
    ' shown as two lines (GMBH SERVICES + the rest) to match the reference layout.
    Dim totOpFinal(0 To 4) As Double
    For s = 0 To 4: totOpFinal(s) = totOp(s): Next s

    If Not isConsolidado Then
        Dim allocBase As Double
        allocBase = totInc(1) + totInc(2) + totInc(3)
        Dim gmbhBO As Double
        gmbhBO = LookupAmt("  P3 GLOBAL GMBH SERVICES", "6007", 0)
        Dim allocPool As Double
        allocPool = totExp(0) - gmbhBO

        ws.Cells(r, 1).Value = "ALLOCATION BO & GMBH SERVICES"
        ws.Cells(r, 1).Font.Bold = True
        r = r + 1

        Dim totAlloc(0 To 4) As Double, totGmbh(0 To 4) As Double
        Dim ss As Long, pct As Double
        For ss = 1 To 3
            pct = SafePct(totInc(ss), allocBase)
            totGmbh(ss) = gmbhBO * pct
            totAlloc(ss) = allocPool * pct
        Next ss
        totGmbh(0) = -gmbhBO
        totAlloc(0) = -allocPool

        ws.Cells(r, 1).Value = "P3 GLOBAL GMBH SERVICES"
        With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols)): .Interior.Color = C_SUBTOTAL: End With
        Call WriteAmts(ws, r, totGmbh, isConsolidado, baseIncSeg)
        r = r + 1

        ws.Cells(r, 1).Value = "  ALLOCATION OF BACK OFFICE - EXPENSES"
        With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols)): .Interior.Color = C_SUBTOTAL: End With
        Call WriteAmts(ws, r, totAlloc, isConsolidado, baseIncSeg)
        r = r + 2

        For s = 0 To 3: totOpFinal(s) = totOpFinal(s) - totGmbh(s) - totAlloc(s): Next s

        ws.Cells(r, 1).Value = "OPERATING PROFIT (OR LOSS) - After Allocation"
        With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
            .Font.Bold = True
            .Interior.Color = C_HEADER
            .Font.Color = C_WHITE
        End With
        Call WriteAmts(ws, r, totOpFinal, isConsolidado, baseIncSeg)
        r = r + 2
    End If

    ' ---- OTHER INCOMES (4210, 4310, 4510) ----
    ws.Cells(r, 1).Value = "Other Incomes"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    Dim totOtherInc(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "4OI" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totOtherInc, baseIncSeg)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Other Incomes Total", totOtherInc, isConsolidado, C_SUBTOTAL, baseIncSeg)
    r = r + 2

    ' ---- OTHER EXPENSES (6009) ----
    ws.Cells(r, 1).Value = "Other Expenses"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    Dim totOtherExp(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "6009" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totOtherExp, baseIncSeg)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Other Expenses Total", totOtherExp, isConsolidado, C_SUBTOTAL, baseIncSeg)
    r = r + 2

    ' ---- ACCRUED TAXES (8000) ----
    ws.Cells(r, 1).Value = "Accrued Taxes"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    Dim totTax(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "8000" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totTax, baseIncSeg)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Accrued Taxes Total", totTax, isConsolidado, C_SUBTOTAL, baseIncSeg)
    r = r + 2

    ' ---- NET PROFIT ----
    Dim totNet(0 To 4) As Double
    For s = 0 To 4
        totNet(s) = totOpFinal(s) + totOtherInc(s) - totOtherExp(s) - totTax(s)
    Next s
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
        .Font.Bold = True
        .Interior.Color = C_HEADER
        .Font.Color = C_WHITE
    End With
    ws.Cells(r, 1).Value = "NET PROFIT (OR LOSS)"
    Call WriteAmts(ws, r, totNet, isConsolidado, baseIncSeg)

    ' Column widths
    ws.Columns("A").ColumnWidth = 52
    If isConsolidado Then
        ws.Columns("B:C").AutoFit
    Else
        ws.Columns("B:K").AutoFit
    End If
End Sub

' =============================================
' HELPERS
' =============================================

Private Sub WriteParsedRow(ws As Worksheet, r As Long, labelEN As String, k As Long, _
                            isConsolidado As Boolean, ByRef tot() As Double, ByRef baseIncSeg() As Double)
    ws.Cells(r, 1).Value = labelEN
    Dim s As Long, amt As Double, ac As Long, pc As Long
    If isConsolidado Then
        amt = acctAmts(k, 4)
        If amt = 0 Then
            ws.Cells(r, 2).Value = "-"
            ws.Cells(r, 3).Value = "-"
        Else
            ws.Cells(r, 2).Value = amt
            ws.Cells(r, 2).NumberFormat = "#,##0.00"
            ws.Cells(r, 3).Value = SafePct(amt, baseIncSeg(4))
            ws.Cells(r, 3).NumberFormat = "0.00%"
        End If
        tot(4) = tot(4) + amt
    Else
        For s = 0 To 4
            amt = acctAmts(k, s)
            ac = 2 + s * 2
            pc = 3 + s * 2
            If amt = 0 Then
                ws.Cells(r, ac).Value = "-"
                ws.Cells(r, pc).Value = "-"
            Else
                ws.Cells(r, ac).Value = amt
                ws.Cells(r, ac).NumberFormat = "#,##0.00"
                ws.Cells(r, pc).Value = SafePct(amt, baseIncSeg(s))
                ws.Cells(r, pc).NumberFormat = "0.00%"
            End If
            tot(s) = tot(s) + amt
        Next s
    End If
End Sub

Private Sub WriteCatRow(ws As Worksheet, r As Long, labelEN As String, grp As String, _
                        isConsolidado As Boolean, ByRef tot() As Double, ByRef baseIncSeg() As Double)
    ws.Cells(r, 1).Value = labelEN
    Dim s As Long, amt As Double, ac As Long, pc As Long
    If isConsolidado Then
        amt = LookupAmt(labelEN, grp, 4)
        If amt = 0 Then
            ws.Cells(r, 2).Value = "-"
            ws.Cells(r, 3).Value = "-"
        Else
            ws.Cells(r, 2).Value = amt
            ws.Cells(r, 2).NumberFormat = "#,##0.00"
            ws.Cells(r, 3).Value = SafePct(amt, baseIncSeg(4))
            ws.Cells(r, 3).NumberFormat = "0.00%"
        End If
        tot(4) = tot(4) + amt
    Else
        For s = 0 To 4
            amt = LookupAmt(labelEN, grp, s)
            ac = 2 + s * 2
            pc = 3 + s * 2
            If amt = 0 Then
                ws.Cells(r, ac).Value = "-"
                ws.Cells(r, pc).Value = "-"
            Else
                ws.Cells(r, ac).Value = amt
                ws.Cells(r, ac).NumberFormat = "#,##0.00"
                ws.Cells(r, pc).Value = SafePct(amt, baseIncSeg(s))
                ws.Cells(r, pc).NumberFormat = "0.00%"
            End If
            tot(s) = tot(s) + amt
        Next s
    End If
End Sub

Private Sub WriteSumRow(ws As Worksheet, r As Long, label As String, _
                         tot() As Double, isConsolidado As Boolean, color As Long, baseIncSeg() As Double)
    Dim nCols As Long: nCols = IIf(isConsolidado, 3, 11)
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
        .Font.Bold = True
        .Interior.Color = color
    End With
    ws.Cells(r, 1).Value = label
    Dim s As Long, ac As Long, pc As Long
    If isConsolidado Then
        ws.Cells(r, 2).Value = tot(4)
        ws.Cells(r, 2).NumberFormat = "#,##0.00"
        ws.Cells(r, 3).Value = SafePct(tot(4), baseIncSeg(4))
        ws.Cells(r, 3).NumberFormat = "0.00%"
    Else
        For s = 0 To 4
            ac = 2 + s * 2
            pc = 3 + s * 2
            ws.Cells(r, ac).Value = tot(s)
            ws.Cells(r, ac).NumberFormat = "#,##0.00"
            ws.Cells(r, pc).Value = SafePct(tot(s), baseIncSeg(s))
            ws.Cells(r, pc).NumberFormat = "0.00%"
        Next s
    End If
End Sub

Private Sub WriteAmts(ws As Worksheet, r As Long, vals() As Double, _
                       isConsolidado As Boolean, baseIncSeg() As Double)
    Dim s As Long, ac As Long, pc As Long
    If isConsolidado Then
        ws.Cells(r, 2).Value = vals(4)
        ws.Cells(r, 2).NumberFormat = "#,##0.00"
        ws.Cells(r, 3).Value = SafePct(vals(4), baseIncSeg(4))
        ws.Cells(r, 3).NumberFormat = "0.00%"
    Else
        For s = 0 To 4
            ac = 2 + s * 2
            pc = 3 + s * 2
            ws.Cells(r, ac).Value = vals(s)
            ws.Cells(r, ac).NumberFormat = "#,##0.00"
            ws.Cells(r, pc).Value = SafePct(vals(s), baseIncSeg(s))
            ws.Cells(r, pc).NumberFormat = "0.00%"
        Next s
    End If
End Sub

Private Sub WritePctRow(ws As Worksheet, r As Long, label As String, _
                         amt As Double, baseInc As Double)
    ws.Cells(r, 1).Value = label
    ws.Cells(r, 1).Font.Italic = True
    ws.Cells(r, 2).Value = SafePct(amt, baseInc)
    ws.Cells(r, 2).NumberFormat = "0.00%"
End Sub

Private Function SafePct(amt As Double, base As Double) As Double
    If base = 0 Then
        SafePct = 0
    Else
        SafePct = amt / base
    End If
End Function
