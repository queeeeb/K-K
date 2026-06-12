Attribute VB_Name = "GenerarPL"
Option Explicit

' =============================================
' K&K Consulting — P&L Generator
' Input:  Contpaqi "Movimientos Auxiliares por Segmento de Negocio"
' Output: CONSOLIDATED + BY SEGMENT sheets
' =============================================

Private Const MAX_ACCTS As Integer = 300
Private Const MAX_CAT   As Integer = 200

Private nAccts As Integer
Private acctNum(0 To 299) As String
Private acctNameES(0 To 299) As String
Private acctGrp(0 To 299) As String
Private acctAmts(0 To 299, 0 To 4) As Double

Private nCat As Integer
Private catLabel(0 To 199) As String
Private catGrp(0 To 199) As String

' =============================================
' MAIN
' =============================================

Public Sub GenerarPL()
    nAccts = 0
    Dim k As Integer, s As Integer
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

    Dim sPeriodo As String
    sPeriodo = Trim(CStr(wsIn.Cells(3, 1).Value))
    If sPeriodo = "" Then sPeriodo = Trim(CStr(wsIn.Cells(2, 1).Value))

    Call ParseInsumo(wsIn)
    wbIn.Close SaveChanges:=False

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
End Sub

' =============================================
' PARSER
' =============================================

Private Sub ParseInsumo(wsIn As Worksheet)
    Dim totalRows As Long
    totalRows = wsIn.Cells(wsIn.Rows.Count, 1).End(xlUp).Row

    Dim curIdx As Integer: curIdx = -1
    Dim curSeg As Integer: curSeg = -1

    Dim i As Long
    For i = 1 To totalRows
        Dim colA As String, colB As String, colE As String
        colA = Trim(CStr(wsIn.Cells(i, 1).Value))
        colB = Trim(CStr(wsIn.Cells(i, 2).Value))
        colE = Trim(CStr(wsIn.Cells(i, 5).Value))

        If Len(colA) >= 15 And Mid(colA, 5, 1) = "-" And Mid(colA, 9, 1) = "-" And Mid(colA, 13, 1) = "-" Then
            Dim grp As String: grp = GetGrp(colA)
            If grp <> "" Then
                curIdx = FindOrAdd(colA, colB, grp)
            Else
                curIdx = -1
            End If
            curSeg = -1

        ElseIf Left(colA, 9) = "Segmento:" Then
            Dim segRaw As String
            segRaw = Trim(Mid(colA, 10))
            Dim sp As Integer: sp = InStr(segRaw, " ")
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
        GetGrp = "4210"
    ElseIf Left(c, 4) = "4310" Then
        GetGrp = "4310"
    ElseIf Left(c, 4) = "4510" Then
        GetGrp = "4510"
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

Private Function FindOrAdd(num As String, nameES As String, grp As String) As Integer
    Dim k As Integer
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

Private Function GetSegIdx(seg As String) As Integer
    Select Case Trim(seg)
        Case "BO": GetSegIdx = 0
        Case "ING": GetSegIdx = 1
        Case "CONS OPS": GetSegIdx = 2
        Case "DIGITAL SOLUTIONS": GetSegIdx = 3
        Case Else: GetSegIdx = -1
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
            Dim cli As String
            cli = Trim(Mid(nameES, 12))
            EN = "  ACCRUED REVENUE " & cli
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
' CATALOG
' =============================================

Private Sub AddCat(lbl As String, grp As String)
    If nCat < MAX_CAT Then
        catLabel(nCat) = lbl: catGrp(nCat) = grp: nCat = nCat + 1
    End If
End Sub

Private Sub InitCatalog()
    nCat = 0
    ' --- INCOMES (4110) ---
    AddCat "NATIONAL SALES", "4110"
    AddCat "P3 AUTOMOTIVE GMBH", "4110"
    AddCat "P3 USA INC", "4110"
    AddCat "P3 DIGITAL SERVICES GmbH", "4110"
    AddCat "NOMEA GMBH", "4110"
    AddCat "XTM CANADA", "4110"
    AddCat "AUTOELECTRIC AMERICA", "4110"
    AddCat "  ACCRUED REVENUE BMW", "4110"
    AddCat "  ACCRUED REVENUE P3 AUTOMOTIVE", "4110"
    AddCat "  ACCRUED REVENUE OTROS PROYECTOS", "4110"
    AddCat "  ACCRUED REVENUE FORD MOTOR COMPANY S.A. DE C.V.", "4110"
    AddCat "  ACCRUED REVENUE JOYSONQUIN", "4110"
    AddCat "  ACCRUED REVENUE P3 USA", "4110"
    AddCat "  ACCRUED REVENUE P3 DIGITAL SERVICIO GMBH", "4110"
    AddCat "  ACCRUED REVENUE SERVICIOS TURISTICOS EXCLUSIVOS", "4110"
    AddCat "  ACCRUED REVENUE SCOTIABANK INVERLAT", "4110"
    AddCat "  ACCRUED REVENUE YANFENG", "4110"
    AddCat "  ACCRUED REVENUE NEXANS", "4110"
    AddCat "  ACCRUED REVENUE SEPTIEMBRE 24", "4110"
    AddCat "  ACCRUED REVENUE HUASION MOTOR MEXICO", "4110"
    AddCat "  ACCRUED REVENUE GEB", "4110"
    AddCat "  ACCRUED REVENUE EQUIPO AUTOMOTRIZ AMERICAN", "4110"
    AddCat "  ACCRUED REVENUE AUTOLIV STEERING WHEELS MEXICO", "4110"
    AddCat "  ACCRUED REVENUE AUDI MEXICO", "4110"
    AddCat "  ACCRUED REVENUE GLORY", "4110"
    AddCat "  ACCRUED REVENUE GENTERA", "4110"
    AddCat "  ACCRUED REVENUE FOXCONN", "4110"
    AddCat "  ACCRUED REVENUE DHL LAST MILE DELIVERY", "4110"
    AddCat "  ACCRUED REVENUE SANDEN", "4110"
    AddCat "  ACCRUED REVENUE QBCo", "4110"
    AddCat "  ACCRUED REVENUE VOLKSWAGEN", "4110"
    ' --- EXPENSES ---
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
    AddCat "  PARKING", "6006"
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
    ' --- OTHER INCOMES (4OI = 4210+4310+4510) ---
    AddCat "  E.R. FLUCTUATION PROFIT", "4OI"
    AddCat "  OTHER INCOME", "4OI"
    AddCat "  INTEREST", "4OI"
    AddCat "  FINANCIAL PRODUCTS", "4OI"
    ' --- OTHER EXPENSES (6009) ---
    AddCat "  E.R. FLUCTUATION LOSS", "6009"
    ' --- ACCRUED TAXES (8000) ---
    AddCat "  INCOME TAX OF THE YEAR", "8000"
    AddCat "  PTU", "8000"
End Sub

Private Function LookupAmt(labelEN As String, grp As String, segIdx As Integer) As Double
    Dim k As Integer
    LookupAmt = 0
    For k = 0 To nAccts - 1
        Dim matches As Boolean
        If grp = "4OI" Then
            matches = (acctGrp(k) = "4210" Or acctGrp(k) = "4310" Or acctGrp(k) = "4510") _
                      And EN(acctNameES(k), acctGrp(k)) = labelEN
        Else
            matches = acctGrp(k) = grp And EN(acctNameES(k), grp) = labelEN
        End If
        If matches Then LookupAmt = LookupAmt + acctAmts(k, segIdx)
    Next k
End Function

' =============================================
' SHEET WRITER
' =============================================

Private Sub EscribirHoja(ws As Worksheet, isConsolidado As Boolean, periodo As String)
    Call InitCatalog()

    Dim r As Integer: r = 1
    Dim nCols As Integer: nCols = IIf(isConsolidado, 3, 6)
    Dim c As Integer, s As Integer, k As Integer

    Dim C_HEADER As Long: C_HEADER = RGB(30, 60, 100)
    Dim C_WHITE As Long: C_WHITE = RGB(255, 255, 255)
    Dim C_INC As Long: C_INC = RGB(198, 224, 180)
    Dim C_EXP As Long: C_EXP = RGB(255, 199, 206)
    Dim C_OP As Long: C_OP = RGB(255, 235, 156)
    Dim C_NET As Long: C_NET = RGB(169, 208, 142)

    ' Header
    ws.Cells(r, 1).Value = "P-TRES GROUP, S.A.P.I. DE C.V."
    ws.Cells(r, 1).Font.Bold = True: ws.Cells(r, 1).Font.Size = 13
    r = r + 1
    ws.Cells(r, 1).Value = "Profit and Loss Statement" & IIf(isConsolidado, " — ", " by Segment — ") & periodo
    r = r + 2

    ' Column headers
    ws.Cells(r, 1).Value = "DESCRIPTION"
    If isConsolidado Then
        ws.Cells(r, 2).Value = "TOTAL"
        ws.Cells(r, 3).Value = "%"
    Else
        ws.Cells(r, 2).Value = "BACK OFFICE"
        ws.Cells(r, 3).Value = "CONSUL OP"
        ws.Cells(r, 4).Value = "ENGINEERING"
        ws.Cells(r, 5).Value = "DIGITAL SOLUTIONS"
        ws.Cells(r, 6).Value = "TOTAL"
    End If
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
        .Font.Bold = True
        .Interior.Color = C_HEADER
        .Font.Color = C_WHITE
        .HorizontalAlignment = xlCenter
    End With
    r = r + 1

    ' Pre-calculate baseInc (sum of all 4110 parsed accounts)
    Dim baseInc As Double: baseInc = 0
    For k = 0 To nAccts - 1
        If acctGrp(k) = "4110" Then baseInc = baseInc + acctAmts(k, 4)
    Next k

    ' ---- INCOMES (4110) ----
    ws.Cells(r, 1).Value = "Incomes"
    ws.Cells(r, 1).Font.Bold = True
    ws.Cells(r, 1).Font.Color = RGB(0, 100, 0)
    r = r + 1

    Dim totInc(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "4110" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totInc, baseInc)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Incomes Total", totInc, isConsolidado, C_INC, baseInc)
    r = r + 1
    If isConsolidado Then Call WritePctRow(ws, r, "% of the Total Incomes", totInc(4), totInc(4))
    r = r + 2

    ' ---- EXPENSES (6001-6008) ----
    ws.Cells(r, 1).Value = "Expenses"
    ws.Cells(r, 1).Font.Bold = True
    ws.Cells(r, 1).Font.Color = RGB(150, 0, 0)
    r = r + 1

    Dim totExp(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "6001" Or catGrp(c) = "6002" Or catGrp(c) = "6004" Or _
           catGrp(c) = "6005" Or catGrp(c) = "6006" Or catGrp(c) = "6007" Or _
           catGrp(c) = "6008" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totExp, baseInc)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Expenses Total", totExp, isConsolidado, C_EXP, baseInc)
    r = r + 1
    If isConsolidado Then Call WritePctRow(ws, r, "% of the Total Expenses", totExp(4), totInc(4))
    r = r + 2

    ' ---- OPERATING PROFIT ----
    Dim totOp(0 To 4) As Double
    For s = 0 To 4: totOp(s) = totInc(s) - totExp(s): Next s
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
        .Font.Bold = True
        .Interior.Color = C_OP
    End With
    ws.Cells(r, 1).Value = "OPERATING PROFIT (OR LOSS) BEFORE ALLOCATIONS"
    Call WriteAmts(ws, r, totOp, isConsolidado, baseInc)
    r = r + 2

    ' ---- OTHER INCOMES (4210, 4310, 4510) ----
    ws.Cells(r, 1).Value = "Other Incomes"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    Dim totOtherInc(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "4OI" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totOtherInc, baseInc)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Other Incomes Total", totOtherInc, isConsolidado, C_INC, baseInc)
    r = r + 2

    ' ---- OTHER EXPENSES (6009) ----
    ws.Cells(r, 1).Value = "Other Expenses"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    Dim totOtherExp(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "6009" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totOtherExp, baseInc)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Other Expenses Total", totOtherExp, isConsolidado, C_EXP, baseInc)
    r = r + 2

    ' ---- ACCRUED TAXES (8000) ----
    ws.Cells(r, 1).Value = "Accrued Taxes"
    ws.Cells(r, 1).Font.Bold = True
    r = r + 1
    Dim totTax(0 To 4) As Double
    For c = 0 To nCat - 1
        If catGrp(c) = "8000" Then
            Call WriteCatRow(ws, r, catLabel(c), catGrp(c), isConsolidado, totTax, baseInc)
            r = r + 1
        End If
    Next c
    Call WriteSumRow(ws, r, "Accrued Taxes Total", totTax, isConsolidado, C_EXP, baseInc)
    r = r + 2

    ' ---- NET PROFIT ----
    Dim totNet(0 To 4) As Double
    For s = 0 To 4
        totNet(s) = totOp(s) + totOtherInc(s) - totOtherExp(s) - totTax(s)
    Next s
    Dim netColor As Long
    netColor = IIf(totNet(4) >= 0, C_NET, RGB(255, 100, 100))
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
        .Font.Bold = True
        .Font.Size = 12
        .Interior.Color = netColor
    End With
    ws.Cells(r, 1).Value = "NET PROFIT (OR LOSS)"
    Call WriteAmts(ws, r, totNet, isConsolidado, baseInc)

    ' Column widths
    ws.Columns("A").ColumnWidth = 52
    If isConsolidado Then
        ws.Columns("B:C").AutoFit
    Else
        ws.Columns("B:F").AutoFit
    End If
End Sub

' =============================================
' HELPERS
' =============================================

Private Sub WriteCatRow(ws As Worksheet, r As Integer, labelEN As String, grp As String, _
                        isConsolidado As Boolean, ByRef tot() As Double, baseInc As Double)
    ws.Cells(r, 1).Value = labelEN
    Dim s As Integer, amt As Double
    If isConsolidado Then
        amt = LookupAmt(labelEN, grp, 4)
        If amt = 0 Then
            ws.Cells(r, 2).Value = "-"
            ws.Cells(r, 3).Value = "-"
        Else
            ws.Cells(r, 2).Value = amt
            ws.Cells(r, 2).NumberFormat = "#,##0.00"
            ws.Cells(r, 3).Value = IIf(baseInc = 0, 0, amt / baseInc)
            ws.Cells(r, 3).NumberFormat = "0.00%"
        End If
        tot(4) = tot(4) + amt
    Else
        For s = 0 To 4
            amt = LookupAmt(labelEN, grp, s)
            If amt = 0 Then
                ws.Cells(r, s + 2).Value = "-"
            Else
                ws.Cells(r, s + 2).Value = amt
                ws.Cells(r, s + 2).NumberFormat = "#,##0.00"
            End If
            tot(s) = tot(s) + amt
        Next s
    End If
End Sub

Private Sub WriteSumRow(ws As Worksheet, r As Integer, label As String, _
                         tot() As Double, isConsolidado As Boolean, color As Long, baseInc As Double)
    Dim nCols As Integer: nCols = IIf(isConsolidado, 3, 6)
    With ws.Range(ws.Cells(r, 1), ws.Cells(r, nCols))
        .Font.Bold = True
        .Interior.Color = color
    End With
    ws.Cells(r, 1).Value = label
    Dim s As Integer
    If isConsolidado Then
        ws.Cells(r, 2).Value = tot(4)
        ws.Cells(r, 2).NumberFormat = "#,##0.00"
        ws.Cells(r, 3).Value = IIf(baseInc = 0, 0, tot(4) / baseInc)
        ws.Cells(r, 3).NumberFormat = "0.00%"
    Else
        For s = 0 To 4
            ws.Cells(r, s + 2).Value = tot(s)
            ws.Cells(r, s + 2).NumberFormat = "#,##0.00"
        Next s
    End If
End Sub

Private Sub WriteAmts(ws As Worksheet, r As Integer, vals() As Double, _
                       isConsolidado As Boolean, baseInc As Double)
    Dim s As Integer
    If isConsolidado Then
        ws.Cells(r, 2).Value = vals(4)
        ws.Cells(r, 2).NumberFormat = "#,##0.00"
        ws.Cells(r, 3).Value = IIf(baseInc = 0, 0, vals(4) / baseInc)
        ws.Cells(r, 3).NumberFormat = "0.00%"
    Else
        For s = 0 To 4
            ws.Cells(r, s + 2).Value = vals(s)
            ws.Cells(r, s + 2).NumberFormat = "#,##0.00"
        Next s
    End If
End Sub

Private Sub WritePctRow(ws As Worksheet, r As Integer, label As String, _
                         amt As Double, baseInc As Double)
    ws.Cells(r, 1).Value = label
    ws.Cells(r, 1).Font.Italic = True
    ws.Cells(r, 2).Value = IIf(baseInc = 0, 0, amt / baseInc)
    ws.Cells(r, 2).NumberFormat = "0.00%"
End Sub
