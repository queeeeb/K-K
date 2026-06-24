VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ThisWorkbook"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Private Sub Workbook_Open()
    Dim ws As Worksheet
    Set ws = Sheets(1)

    Dim btn As Variant
    On Error Resume Next
    Set btn = ws.Buttons("btnGenerarPL")
    On Error GoTo 0

    If btn Is Nothing Then
        Set btn = ws.Buttons.Add(ws.Range("B2").Left, ws.Range("B2").Top, 150, 32)
        btn.OnAction = "GenerarPL"
        btn.Caption = "Generar P&L"
        btn.Name = "btnGenerarPL"
    End If
End Sub
