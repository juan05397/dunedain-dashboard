import win32com.client
import os

def get_color(r, g, b):
    # win32com RGB color calculation: B * 65536 + G * 256 + R
    return b * 65536 + g * 256 + r

def apply_borders(range_obj):
    # win32com borders: 7 (left), 8 (right), 9 (top), 10 (bottom)
    for border_idx in [7, 8, 9, 10]:
        border = range_obj.Borders(border_idx)
        border.LineStyle = 1 # xlContinuous = 1
        border.Weight = 2 # xlThin = 2
        border.Color = get_color(203, 213, 224) # soft gray-blue border

def style_range(ws, range_str, bg_color=None, font_name="Segoe UI", font_size=11, font_color=None, bold=False, italic=False, align_h=None, align_v=None, number_format=None, wrap_text=False):
    r = ws.Range(range_str)
    if bg_color is not None:
        r.Interior.Color = bg_color
    if font_name is not None:
        r.Font.Name = font_name
    if font_size is not None:
        r.Font.Size = font_size
    if font_color is not None:
        r.Font.Color = font_color
    r.Font.Bold = bold
    r.Font.Italic = italic
    if align_h is not None:
        r.HorizontalAlignment = align_h
    if align_v is not None:
        r.VerticalAlignment = align_v
    if number_format is not None:
        r.NumberFormat = number_format
    if wrap_text:
        r.WrapText = True

def main():
    # ------------------ DATA FOR ALL 5 GROUPS ------------------
    g1_data = [
        [1, "Mañana", "Café", "Cappuccino", 10, 3.00, "Pago Móvil"],
        [2, "Mañana", "Repostería", "Donas", 15, 2.00, "Efectivo"],
        [3, "Tarde", "Bebidas Frías", "Té Frío", 12, 2.50, "Punto/Tarjeta"],
        [4, "Mañana", "Café", "Espresso", 20, 1.50, "Efectivo"],
        [5, "Tarde", "Repostería", "Torta de Chocolate", 8, 4.00, "Pago Móvil"],
        [6, "Mañana", "Bebidas Frías", "Jugo Natural", 10, 3.00, "Punto/Tarjeta"],
        [7, "Tarde", "Café", "Cappuccino", 15, 3.00, "Pago Móvil"],
        [8, "Tarde", "Repostería", "Donas", 25, 2.00, "Efectivo"],
        [9, "Mañana", "Café", "Espresso", 14, 1.50, "Punto/Tarjeta"],
        [10, "Tarde", "Bebidas Frías", "Té Frío", 20, 2.50, "Pago Móvil"]
    ]

    g2_data = [
        [1, "Mañana", "Café", "Cappuccino", 15, 3.00, "Pago Móvil"],
        [2, "Mañana", "Repostería", "Donas", 15, 2.00, "Efectivo"],
        [3, "Tarde", "Bebidas Frías", "Té Frío", 12, 2.50, "Punto/Tarjeta"],
        [4, "Mañana", "Café", "Espresso", 20, 1.50, "Efectivo"],
        [5, "Tarde", "Repostería", "Torta de Chocolate", 8, 4.00, "Pago Móvil"],
        [6, "Mañana", "Bebidas Frías", "Jugo Natural", 10, 3.00, "Punto/Tarjeta"],
        [7, "Tarde", "Café", "Cappuccino", 15, 3.00, "Pago Móvil"],
        [8, "Tarde", "Repostería", "Donas", 20, 2.00, "Efectivo"],
        [9, "Mañana", "Café", "Espresso", 14, 1.50, "Punto/Tarjeta"],
        [10, "Tarde", "Bebidas Frías", "Té Frío", 20, 2.50, "Pago Móvil"]
    ]

    g3_data = [
        [1, "Mañana", "Café", "Cappuccino", 10, 3.00, "Pago Móvil"],
        [2, "Mañana", "Repostería", "Donas", 15, 2.00, "Efectivo"],
        [3, "Tarde", "Bebidas Frías", "Té Frío", 12, 2.50, "Punto/Tarjeta"],
        [4, "Mañana", "Café", "Espresso", 10, 1.50, "Efectivo"],
        [5, "Tarde", "Repostería", "Torta de Chocolate", 8, 4.00, "Pago Móvil"],
        [6, "Mañana", "Bebidas Frías", "Jugo Natural", 10, 3.00, "Punto/Tarjeta"],
        [7, "Tarde", "Café", "Cappuccino", 15, 3.00, "Pago Móvil"],
        [8, "Tarde", "Repostería", "Donas", 25, 2.00, "Efectivo"],
        [9, "Mañana", "Café", "Espresso", 14, 1.50, "Punto/Tarjeta"],
        [10, "Tarde", "Bebidas Frías", "Té Frío", 25, 2.50, "Pago Móvil"]
    ]

    g4_data = [
        [1, "Mañana", "Café", "Cappuccino", 10, 3.00, "Pago Móvil"],
        [2, "Mañana", "Repostería", "Donas", 15, 2.00, "Efectivo"],
        [3, "Tarde", "Bebidas Frías", "Té Frío", 12, 2.50, "Punto/Tarjeta"],
        [4, "Mañana", "Café", "Espresso", 20, 1.50, "Efectivo"],
        [5, "Tarde", "Repostería", "Torta de Chocolate", 12, 4.00, "Pago Móvil"],
        [6, "Mañana", "Bebidas Frías", "Jugo Natural", 15, 3.00, "Punto/Tarjeta"],
        [7, "Tarde", "Café", "Cappuccino", 15, 3.00, "Pago Móvil"],
        [8, "Tarde", "Repostería", "Donas", 25, 2.00, "Efectivo"],
        [9, "Mañana", "Café", "Espresso", 14, 1.50, "Punto/Tarjeta"],
        [10, "Tarde", "Bebidas Frías", "Té Frío", 20, 2.50, "Pago Móvil"]
    ]

    g5_data = [
        [1, "Mañana", "Café", "Cappuccino", 10, 3.00, "Pago Móvil"],
        [2, "Mañana", "Repostería", "Donas", 15, 2.00, "Efectivo"],
        [3, "Tarde", "Bebidas Frías", "Té Frío", 8, 2.50, "Punto/Tarjeta"],
        [4, "Mañana", "Café", "Espresso", 20, 1.50, "Efectivo"],
        [5, "Tarde", "Repostería", "Torta de Chocolate", 8, 4.00, "Pago Móvil"],
        [6, "Mañana", "Bebidas Frías", "Jugo Natural", 10, 3.00, "Punto/Tarjeta"],
        [7, "Tarde", "Café", "Cappuccino", 20, 3.00, "Pago Móvil"],
        [8, "Tarde", "Repostería", "Donas", 25, 2.00, "Efectivo"],
        [9, "Mañana", "Café", "Espresso", 14, 1.50, "Punto/Tarjeta"],
        [10, "Tarde", "Bebidas Frías", "Té Frío", 20, 2.50, "Pago Móvil"]
    ]

    data_dict = {
        1: g1_data,
        2: g2_data,
        3: g3_data,
        4: g4_data,
        5: g5_data
    }

    # ------------------ MANAGEMENT REPORTS ------------------
    reports_dict = {
        1: (
            "1. Análisis de Turnos: El turno de la tarde genera el 59.5% de los ingresos ($207.00 vs $141.00 de la mañana). "
            "Se recomienda reforzar el personal en el turno de la tarde para optimizar los tiempos de atención durante este pico de demanda. "
            "Para el turno de la mañana, se sugiere lanzar promociones de combos (ej. Café + Dona a precio especial) para estimular las ventas matutinas.\n\n"
            "2. Optimización de Caja: El Pago Móvil es el método más utilizado con un 45.1% ($157.00) de la facturación, seguido por Efectivo (31.6%). "
            "Para agilizar la atención en caja, implementaremos códigos QR visibles en el mostrador para el Pago Móvil y capacitaremos al personal en la "
            "verificación rápida de transferencias, reduciendo considerablemente los tiempos de cola en el mostrador."
        ),
        2: (
            "1. Análisis de Turnos: El turno de la tarde representa el 55.8% de las ventas ($197.00 vs $156.00 de la mañana). "
            "Aunque la mañana muestra un desempeño sólido en comparación con otros grupos, se recomienda mantener la asignación óptima de personal en la tarde. "
            "Sugerimos introducir ofertas rápidas matutinas (como combos de 'Café Espresso y Donas') para dinamizar las horas tempranas y cerrar la brecha.\n\n"
            "2. Optimización de Caja: El Pago Móvil lidera con un 48.7% ($172.00) de los ingresos. Para acelerar el flujo en caja, "
            "colocaremos habladores con códigos QR en cada punto de pedido para facilitar el escaneo inmediato por parte del cliente y capacitaremos al personal "
            "para validar las notificaciones de pago digital de manera ágil sin interrumpir la entrega de pedidos."
        ),
        3: (
            "1. Análisis de Turnos: Existe una marcada concentración en la tarde, que genera el 63.5% de los ingresos ($219.50 vs $126.00 de la mañana). "
            "Es imperativo reestructurar los horarios de la plantilla, trasladando personal de apoyo de la mañana a la tarde. "
            "En la mañana, proponemos activar promociones matutinas agresivas de 8:00 AM a 10:00 AM para captar el flujo laboral.\n\n"
            "2. Optimización de Caja: El Pago Móvil es la opción preferida por los clientes, acumulando el 49.1% ($169.50) del total facturado. "
            "Recomendamos integrar una pantalla o dispositivo dedicado a la confirmación de transacciones digitales en caja y establecer un canal rápido "
            "para minimizar la manipulación de efectivo y recortar el tiempo de espera por transacción."
        ),
        4: (
            "1. Análisis de Turnos: El turno de la tarde lidera las ventas con un 58.8% ($223.00 vs $156.00 de la mañana). "
            "Se aconseja programar baristas adicionales en el turno de la tarde debido a la alta demanda de bebidas frías y repostería. "
            "Para captar clientes por la mañana, se propone otorgar cupones de descuento digital válidos únicamente antes de las 11:00 AM.\n\n"
            "2. Optimización de Caja: El Pago Móvil y las Tarjetas combinadas representan el 71.0% de los pagos (Pago Móvil 45.6%, Tarjetas 25.3%). "
            "Para acelerar la atención, implementaremos el cobro directo mediante terminales inalámbricas en la barra y un mostrador exclusivo para "
            "el retiro de pedidos rápidos ya pagados de forma electrónica."
        ),
        5: (
            "1. Análisis de Turnos: El turno de la tarde genera el 60.1% de los ingresos totales ($212.00 vs $141.00 de la mañana). "
            "Se sugiere reforzar la dotación de baristas y personal de barra en el turno de la tarde. "
            "Para impulsar el turno de la mañana, crearemos el combo 'Desayuno Express' con precios diferenciados para elevar el tráfico matutino.\n\n"
            "2. Optimización de Caja: El Pago Móvil destaca como el principal método de cobro con un 48.7% ($172.00) de los ingresos. "
            "Optimizaremos el despacho en caja habilitando un código QR único y de gran tamaño en el mostrador principal, y capacitando a los cajeros en la "
            "verificación de referencias de Pago Móvil en una tableta dedicada a fin de agilizar los despachos."
        )
    }

    try:
        print("Launching Excel...")
        excel = win32com.client.Dispatch("Excel.Application")
        excel.DisplayAlerts = False
        
        # Create workbook
        wb = excel.Workbooks.Add()
        
        # We will build sheets in order: G1_Datos, G1_Dashboard, G2_Datos, G2_Dashboard...
        # Let's keep reference to default sheet 1
        default_sheet = wb.Sheets(1)
        current_sheet = default_sheet
        current_sheet.Name = "Grupo 1 - Datos"
        
        sheets = {}
        
        # Generate sheets loop
        for grp_idx in range(1, 6):
            if grp_idx == 1:
                ws_datos = current_sheet
            else:
                ws_datos = wb.Sheets.Add(None, current_sheet)
                ws_datos.Name = f"Grupo {grp_idx} - Datos"
                current_sheet = ws_datos
                
            ws_dash = wb.Sheets.Add(None, current_sheet)
            ws_dash.Name = f"Grupo {grp_idx} - Dashboard"
            current_sheet = ws_dash
            
            sheets[grp_idx] = {
                'datos': ws_datos,
                'dashboard': ws_dash
            }
            
        # Delete any extra sheets that Excel might have created by default
        for sheet in list(wb.Sheets):
            if not (sheet.Name.startswith("Grupo ") and (" - Datos" in sheet.Name or " - Dashboard" in sheet.Name)):
                sheet.Delete()
                
        # Now populate each group
        for grp_idx in range(1, 6):
            print(f"Populating sheets for Grupo {grp_idx}...")
            ws_datos = sheets[grp_idx]['datos']
            ws_dash = sheets[grp_idx]['dashboard']
            
            # 1. Populate Raw Data in Datos sheet
            headers = ["N°", "Turno", "Categoría", "Producto", "Cantidad", "Precio Unitario", "Método de Pago", "Venta Total ($)"]
            for col_idx, h in enumerate(headers, 1):
                ws_datos.Cells(1, col_idx).Value = h
                
            group_rows = data_dict[grp_idx]
            for row_idx, row_vals in enumerate(group_rows, 2):
                for col_idx, val in enumerate(row_vals, 1):
                    ws_datos.Cells(row_idx, col_idx).Value = val
                # Formula for Venta Total
                ws_datos.Cells(row_idx, 8).Value = f"=E{row_idx}*F{row_idx}"
                
            # Formatting for raw table columns
            ws_datos.Columns("E:E").NumberFormat = "#,##0"
            ws_datos.Columns("F:F").NumberFormat = "$#,##0.00"
            ws_datos.Columns("H:H").NumberFormat = "$#,##0.00"
            
            # Format raw range as Table
            data_range = ws_datos.Range(f"A1:H{len(group_rows)+1}")
            table_name = f"Table_Grupo_{grp_idx}"
            table = ws_datos.ListObjects.Add(SourceType=1, Source=data_range, LinkSource=False, XlListObjectHasHeaders=1)
            table.Name = table_name
            table.TableStyle = "TableStyleMedium2"
            
            # 2. Create Pivot Cache from the Table
            pivot_cache = wb.PivotCaches().Create(SourceType=1, SourceData=table_name)
            
            # 3. Create Pivot Table 1 (Category Sales) at J5
            pivot_table_1 = pivot_cache.CreatePivotTable(TableDestination=ws_datos.Range("J5"), TableName=f"PivotCategory_G{grp_idx}")
            pivot_table_1.PivotFields("Categoría").Orientation = 1 # xlRowField
            val_field_1 = pivot_table_1.PivotFields("Venta Total ($)")
            val_field_1.Orientation = 4 # xlDataField
            val_field_1.Function = -4157 # xlSum
            val_field_1.NumberFormat = "$#,##0.00"
            
            # 4. Create Pivot Table 2 (Payment Method Sales) at M5
            pivot_table_2 = pivot_cache.CreatePivotTable(TableDestination=ws_datos.Range("M5"), TableName=f"PivotPayment_G{grp_idx}")
            pivot_table_2.PivotFields("Método de Pago").Orientation = 1 # xlRowField
            val_field_2 = pivot_table_2.PivotFields("Venta Total ($)")
            val_field_2.Orientation = 4 # xlDataField
            val_field_2.Function = -4157 # xlSum
            val_field_2.NumberFormat = "$#,##0.00"
            
            # 5. Create Pivot Table 3 (KPIs) at P5
            pivot_kpi = pivot_cache.CreatePivotTable(TableDestination=ws_datos.Range("P5"), TableName=f"PivotKPI_G{grp_idx}")
            
            val_kpi_1 = pivot_kpi.PivotFields("Venta Total ($)")
            val_kpi_1.Orientation = 4 # xlDataField
            val_kpi_1.Function = -4157 # xlSum
            val_kpi_1.NumberFormat = "$#,##0.00"
            
            val_kpi_2 = pivot_kpi.PivotFields("Cantidad")
            val_kpi_2.Orientation = 4 # xlDataField
            val_kpi_2.Function = -4157 # xlSum
            val_kpi_2.NumberFormat = "#,##0"
            
            pivot_kpi.AddDataField(pivot_kpi.PivotFields("Venta Total ($)"), "Ticket Promedio", -4106) # xlAverage = -4106
            pivot_kpi.DataFields(3).NumberFormat = "$#,##0.00"
            
            # Force calculate workbook
            excel.Calculate()
            
            # 6. Format Dashboard Sheet
            ws_dash.Columns("A").ColumnWidth = 3
            ws_dash.Columns("B:N").ColumnWidth = 12
            
            # Executive Title Header (B2:M2)
            ws_dash.Range("B2:M2").Merge()
            ws_dash.Range("B2").Value = f"CAFETERÍA GOURMET EL AROMA - DASHBOARD DE VENTAS GRUPO {grp_idx}"
            style_range(ws_dash, "B2:M2", bg_color=get_color(26, 54, 93), font_size=14, font_color=get_color(255, 255, 255), bold=True, align_h=-4108, align_v=-4108)
            ws_dash.Rows(2).RowHeight = 35
            
            # KPI Card 1: TOTAL FACTURADO (B4:D5)
            ws_dash.Range("B4:D4").Merge()
            ws_dash.Range("B4").Value = "TOTAL FACTURADO"
            style_range(ws_dash, "B4:D4", bg_color=get_color(248, 250, 252), font_size=9, font_color=get_color(113, 128, 150), bold=True, align_h=-4108, align_v=-4108)
            
            ws_dash.Range("B5:D5").Merge()
            ws_dash.Range("B5").Value = f"='Grupo {grp_idx} - Datos'!$P$6"
            style_range(ws_dash, "B5:D5", bg_color=get_color(248, 250, 252), font_size=18, font_color=get_color(43, 108, 176), bold=True, align_h=-4108, align_v=-4108, number_format="$#,##0.00")
            apply_borders(ws_dash.Range("B4:D5"))
            
            # KPI Card 2: UNIDADES VENDIDAS (F4:H5)
            ws_dash.Range("F4:H4").Merge()
            ws_dash.Range("F4").Value = "UNIDADES VENDIDAS"
            style_range(ws_dash, "F4:H4", bg_color=get_color(248, 250, 252), font_size=9, font_color=get_color(113, 128, 150), bold=True, align_h=-4108, align_v=-4108)
            
            ws_dash.Range("F5:H5").Merge()
            ws_dash.Range("F5").Value = f"='Grupo {grp_idx} - Datos'!$Q$6"
            style_range(ws_dash, "F5:H5", bg_color=get_color(248, 250, 252), font_size=18, font_color=get_color(47, 133, 90), bold=True, align_h=-4108, align_v=-4108, number_format="#,##0")
            apply_borders(ws_dash.Range("F4:H5"))
            
            # KPI Card 3: TICKET PROMEDIO (J4:L5)
            ws_dash.Range("J4:L4").Merge()
            ws_dash.Range("J4").Value = "TICKET PROMEDIO"
            style_range(ws_dash, "J4:L4", bg_color=get_color(248, 250, 252), font_size=9, font_color=get_color(113, 128, 150), bold=True, align_h=-4108, align_v=-4108)
            
            ws_dash.Range("J5:L5").Merge()
            ws_dash.Range("J5").Value = f"='Grupo {grp_idx} - Datos'!$R$6"
            style_range(ws_dash, "J5:L5", bg_color=get_color(248, 250, 252), font_size=18, font_color=get_color(221, 107, 32), bold=True, align_h=-4108, align_v=-4108, number_format="$#,##0.00")
            apply_borders(ws_dash.Range("J4:L5"))
            
            ws_dash.Rows(4).RowHeight = 15
            ws_dash.Rows(5).RowHeight = 25
            
            # 7. Slicer for Turno at B8
            slicer_cache = wb.SlicerCaches.Add2(pivot_table_1, "Turno", f"Slicer_Turno_G{grp_idx}")
            slicer = slicer_cache.Slicers.Add(
                ws_dash,
                Name=f"Slicer_Turno_G{grp_idx}_UI",
                Caption="Turno",
                Top=ws_dash.Range("B8").Top,
                Left=ws_dash.Range("B8").Left,
                Width=100,
                Height=105
            )
            slicer_cache.PivotTables.AddPivotTable(pivot_table_2)
            slicer_cache.PivotTables.AddPivotTable(pivot_kpi)
            
            # 8. Chart 1 (Category Sales Clustered Column Chart) at D8
            chart_obj_1 = ws_dash.ChartObjects().Add(
                Left=ws_dash.Range("D8").Left,
                Top=ws_dash.Range("D8").Top,
                Width=320,
                Height=210
            )
            chart_1 = chart_obj_1.Chart
            chart_1.SetSourceData(pivot_table_1.TableRange1)
            chart_1.ChartType = 51 # xlColumnClustered = 51
            chart_1.HasTitle = True
            chart_1.ChartTitle.Text = "Total Vendido por Categoría ($)"
            
            # Apply data labels and styling safely
            try:
                if chart_1.SeriesCollection().Count > 0:
                    chart_1.SeriesCollection(1).HasDataLabels = True
            except Exception as e:
                print(f"  Warning adding data labels for G{grp_idx} C1: {e}")
                
            # 9. Chart 2 (Payment Method Doughnut Chart) at I8
            chart_obj_2 = ws_dash.ChartObjects().Add(
                Left=ws_dash.Range("I8").Left,
                Top=ws_dash.Range("I8").Top,
                Width=320,
                Height=210
            )
            chart_2 = chart_obj_2.Chart
            chart_2.SetSourceData(pivot_table_2.TableRange1)
            chart_2.ChartType = -4120 # xlDoughnut = -4120
            chart_2.HasTitle = True
            chart_2.ChartTitle.Text = "Distribución por Método de Pago"
            
            try:
                if chart_2.SeriesCollection().Count > 0:
                    chart_2.SeriesCollection(1).HasDataLabels = True
            except Exception as e:
                print(f"  Warning adding data labels for G{grp_idx} C2: {e}")
                
            # 10. Manager's Report box at B20:M27
            ws_dash.Range("B20:M20").Merge()
            ws_dash.Range("B20").Value = "INFORME DE TOMA DE DECISIONES (ANÁLISIS OPERACIONAL)"
            style_range(ws_dash, "B20:M20", bg_color=get_color(45, 55, 72), font_size=10, font_color=get_color(255, 255, 255), bold=True, align_h=-4108, align_v=-4108)
            ws_dash.Rows(20).RowHeight = 22
            
            ws_dash.Range("B21:M27").Merge()
            ws_dash.Range("B21").Value = reports_dict[grp_idx]
            style_range(ws_dash, "B21:M27", bg_color=get_color(255, 255, 255), font_size=10, font_color=get_color(45, 55, 72), bold=False, align_h=-4131, align_v=-4160, wrap_text=True)
            apply_borders(ws_dash.Range("B20:M27"))
            
            # 11. Hide gridlines on the dashboard sheet
            ws_dash.Activate()
            excel.ActiveWindow.DisplayGridlines = False
            
            # 12. Clean up Datos Sheet
            ws_datos.Columns("A:R").AutoFit()
            
        # Set active sheet back to Grupo 1 - Dashboard
        wb.Sheets("Grupo 1 - Dashboard").Activate()
        
        # Save workbook
        out_path = os.path.abspath(r"C:\Users\BRILLO\Downloads\Tarea\Dashboard_Cafeteria_Aroma.xlsx")
        if os.path.exists(out_path):
            os.remove(out_path)
            
        print("Saving workbook...")
        wb.SaveAs(out_path)
        wb.Close(SaveChanges=True)
        excel.Quit()
        print("Dashboard generation complete! Saved file to:", out_path)
        
    except Exception as e:
        print("An error occurred during sheet generation:", e)
        try:
            excel.Quit()
        except Exception:
            pass
            
if __name__ == "__main__":
    main()
