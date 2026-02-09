# core/reportes/excel_generator.py
import pandas as pd
from datetime import datetime, timedelta, date
from pathlib import Path
from sqlalchemy import func, extract
from config.database import get_db_session
from config.settings import Settings
from core.models.models import Pedido, DetallePedido, Producto, Mesa

class ExcelGenerator:
    def __init__(self):
        self.output_dir = Settings.BASE_DIR / "exports"
        self.output_dir.mkdir(exist_ok=True)
    
    def generar_reporte(self, tipo_periodo="dia", fecha_inicio=None, fecha_fin=None):
        """
        Genera reporte Excel según período
        
        tipo_periodo: 'dia', 'semana', 'mes', 'anual'
        """
        # Calcular fechas si no se proporcionan
        hoy = date.today()
        
        if tipo_periodo == "dia":
            if not fecha_inicio:
                fecha_inicio = hoy
            if not fecha_fin:
                fecha_fin = hoy
        
        elif tipo_periodo == "semana":
            if not fecha_inicio:
                # Lunes de esta semana
                fecha_inicio = hoy - timedelta(days=hoy.weekday())
            if not fecha_fin:
                fecha_fin = fecha_inicio + timedelta(days=6)
        
        elif tipo_periodo == "mes":
            if not fecha_inicio:
                fecha_inicio = hoy.replace(day=1)
            if not fecha_fin:
                # Último día del mes
                if hoy.month == 12:
                    fecha_fin = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    fecha_fin = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
        
        elif tipo_periodo == "anual":
            if not fecha_inicio:
                fecha_inicio = hoy.replace(month=1, day=1)
            if not fecha_fin:
                fecha_fin = hoy.replace(month=12, day=31)
        
        else:
            raise ValueError("Tipo de período no válido")
        
        # Convertir a datetime para consultas
        dt_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        dt_fin = datetime.combine(fecha_fin, datetime.max.time())
        
        # Obtener datos
        with get_db_session() as db:
            pedidos = db.query(Pedido).filter(
                Pedido.fecha_hora >= dt_inicio,
                Pedido.fecha_hora <= dt_fin,
                Pedido.estado.in_(['entregado', 'listo'])
            ).all()
            
            return self._crear_excel(pedidos, tipo_periodo, fecha_inicio, fecha_fin)
    
    def _crear_excel(self, pedidos, tipo_periodo, fecha_inicio, fecha_fin):
        """Crea archivo Excel con múltiples hojas"""
        
        # Nombre del archivo
        fecha_str = fecha_inicio.strftime("%Y%m%d")
        nombre_archivo = f"reporte_{tipo_periodo}_{fecha_str}.xlsx"
        ruta_archivo = self.output_dir / nombre_archivo
        
        # Crear writer de Excel
        with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
            
            # ===== HOJA 1: RESUMEN GENERAL =====
            self._hoja_resumen(writer, pedidos, tipo_periodo, fecha_inicio, fecha_fin)
            
            # ===== HOJA 2: DETALLE DE PEDIDOS =====
            self._hoja_pedidos(writer, pedidos)
            
            # ===== HOJA 3: PRODUCTOS MÁS VENDIDOS =====
            self._hoja_productos(writer, pedidos)
            
            # ===== HOJA 4: VENTAS POR MESA =====
            self._hoja_mesas(writer, pedidos)
            
            # ===== HOJA 5: ANÁLISIS TEMPORAL (solo semana/mes/año) =====
            if tipo_periodo in ['semana', 'mes', 'anual']:
                self._hoja_temporal(writer, pedidos, tipo_periodo)
        
        return str(ruta_archivo)
    
    def _hoja_resumen(self, writer, pedidos, tipo_periodo, fecha_inicio, fecha_fin):
        """Hoja de resumen ejecutivo"""
        
        total_ventas = sum(p.total for p in pedidos)
        total_pedidos = len(pedidos)
        promedio_pedido = total_ventas / total_pedidos if total_pedidos > 0 else 0
        
        # Calcular totales por estado
        pedidos_entregados = [p for p in pedidos if p.estado == 'entregado']
        pedidos_cancelados = []  # Necesitaríamos consulta separada
        
        # Top producto
        productos_count = {}
        for p in pedidos:
            for d in p.detalles:
                nombre = d.producto.nombre
                productos_count[nombre] = productos_count.get(nombre, 0) + d.cantidad
        
        top_producto = max(productos_count.items(), key=lambda x: x[1])[0] if productos_count else "N/A"
        
        # Crear DataFrame de resumen
        resumen_data = {
            'Métrica': [
                'Período',
                'Fecha Inicio',
                'Fecha Fin',
                'Total de Pedidos',
                'Total de Ventas',
                'Promedio por Pedido',
                'Pedidos Entregados',
                'Producto Estrella',
                'Fecha de Generación'
            ],
            'Valor': [
                tipo_periodo.upper(),
                fecha_inicio.strftime("%d/%m/%Y"),
                fecha_fin.strftime("%d/%m/%Y"),
                total_pedidos,
                f"${total_ventas:,.2f}",
                f"${promedio_pedido:,.2f}",
                len(pedidos_entregados),
                top_producto,
                datetime.now().strftime("%d/%m/%Y %H:%M")
            ]
        }
        
        df = pd.DataFrame(resumen_data)
        df.to_excel(writer, sheet_name='📊 Resumen', index=False)
        
        # Auto-ajustar columnas
        worksheet = writer.sheets['📊 Resumen']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 30
    
    def _hoja_pedidos(self, writer, pedidos):
        """Hoja con detalle de cada pedido"""
        
        data = []
        for p in sorted(pedidos, key=lambda x: x.fecha_hora, reverse=True):
            data.append({
                'ID Pedido': p.id,
                'Fecha': p.fecha_hora.strftime("%d/%m/%Y"),
                'Hora': p.fecha_hora.strftime("%H:%M"),
                'Mesa': p.mesa.nombre,
                'Estado': p.estado.upper(),
                'Total': p.total,
                'Cantidad Items': sum(d.cantidad for d in p.detalles),
                'Notas': p.notas or ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='📋 Pedidos', index=False)
        
        # Formato de moneda
        worksheet = writer.sheets['📋 Pedidos']
        for idx, cell in enumerate(worksheet['F'], 1):  # Columna F = Total
            if idx > 1:  # Saltar header
                cell.number_format = '$#,##0.00'
    
    def _hoja_productos(self, writer, pedidos):
        """Hoja de productos más vendidos"""
        
        productos_stats = {}
        
        for p in pedidos:
            for d in p.detalles:
                prod_id = d.producto.id
                if prod_id not in productos_stats:
                    productos_stats[prod_id] = {
                        'nombre': d.producto.nombre,
                        'categoria': d.producto.categoria,
                        'cantidad': 0,
                        'total': 0
                    }
                productos_stats[prod_id]['cantidad'] += d.cantidad
                productos_stats[prod_id]['total'] += d.cantidad * d.precio_unitario
        
        # Convertir a lista y ordenar
        data = []
        for stats in sorted(productos_stats.values(), key=lambda x: x['cantidad'], reverse=True):
            data.append({
                'Producto': stats['nombre'],
                'Categoría': stats['categoria'],
                'Unidades Vendidas': stats['cantidad'],
                'Total Ventas': stats['total']
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='🍔 Productos', index=False)
        
        # Formato
        worksheet = writer.sheets['🍔 Productos']
        for idx, cell in enumerate(worksheet['D'], 1):
            if idx > 1:
                cell.number_format = '$#,##0.00'
    
    def _hoja_mesas(self, writer, pedidos):
        """Hoja de ventas por mesa"""
        
        mesas_stats = {}
        
        for p in pedidos:
            mesa_id = p.mesa.id
            if mesa_id not in mesas_stats:
                mesas_stats[mesa_id] = {
                    'nombre': p.mesa.nombre,
                    'pedidos': 0,
                    'total': 0
                }
            mesas_stats[mesa_id]['pedidos'] += 1
            mesas_stats[mesa_id]['total'] += p.total
        
        data = []
        for stats in sorted(mesas_stats.values(), key=lambda x: x['total'], reverse=True):
            data.append({
                'Mesa': stats['nombre'],
                'Pedidos Atendidos': stats['pedidos'],
                'Total Ventas': stats['total'],
                'Promedio por Pedido': stats['total'] / stats['pedidos']
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='🪑 Mesas', index=False)
        
        worksheet = writer.sheets['🪑 Mesas']
        for col in ['C', 'D']:  # Total y Promedio
            for idx, cell in enumerate(worksheet[col], 1):
                if idx > 1:
                    cell.number_format = '$#,##0.00'
    
    def _hoja_temporal(self, writer, pedidos, tipo_periodo):
        """Análisis temporal de ventas"""
        
        if tipo_periodo == 'semana':
            # Agrupar por día de la semana
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            ventas_por_dia = {dia: {'ventas': 0, 'pedidos': 0} for dia in dias}
            
            for p in pedidos:
                dia_semana = p.fecha_hora.weekday()
                nombre_dia = dias[dia_semana]
                ventas_por_dia[nombre_dia]['ventas'] += p.total
                ventas_por_dia[nombre_dia]['pedidos'] += 1
            
            data = []
            for dia in dias:
                stats = ventas_por_dia[dia]
                data.append({
                    'Día': dia,
                    'Pedidos': stats['pedidos'],
                    'Ventas': stats['ventas'],
                    'Promedio': stats['ventas'] / stats['pedidos'] if stats['pedidos'] > 0 else 0
                })
        
        elif tipo_periodo == 'mes':
            # Agrupar por semana del mes
            ventas_por_semana = {}
            
            for p in pedidos:
                semana = (p.fecha_hora.day - 1) // 7 + 1
                if semana not in ventas_por_semana:
                    ventas_por_semana[semana] = {'ventas': 0, 'pedidos': 0}
                ventas_por_semana[semana]['ventas'] += p.total
                ventas_por_semana[semana]['pedidos'] += 1
            
            data = []
            for semana in sorted(ventas_por_semana.keys()):
                stats = ventas_por_semana[semana]
                data.append({
                    'Semana': f'Semana {semana}',
                    'Pedidos': stats['pedidos'],
                    'Ventas': stats['ventas'],
                    'Promedio': stats['ventas'] / stats['pedidos']
                })
        
        else:  # anual
            # Agrupar por mes
            meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            ventas_por_mes = {mes: {'ventas': 0, 'pedidos': 0} for mes in meses}
            
            for p in pedidos:
                mes = p.fecha_hora.month - 1
                nombre_mes = meses[mes]
                ventas_por_mes[nombre_mes]['ventas'] += p.total
                ventas_por_mes[nombre_mes]['pedidos'] += 1
            
            data = []
            for mes in meses:
                stats = ventas_por_mes[mes]
                if stats['pedidos'] > 0:  # Solo meses con ventas
                    data.append({
                        'Mes': mes,
                        'Pedidos': stats['pedidos'],
                        'Ventas': stats['ventas'],
                        'Promedio': stats['ventas'] / stats['pedidos']
                    })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='📈 Tendencias', index=False)
        
        worksheet = writer.sheets['📈 Tendencias']
        for col in ['C', 'D']:  # Ventas y Promedio
            for idx, cell in enumerate(worksheet[col], 1):
                if idx > 1:
                    cell.number_format = '$#,##0.00'