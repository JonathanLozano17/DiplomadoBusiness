import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .utils import ejecutar_query, get_db_connection

# ============================================================
# VISTAS PRINCIPALES
# ============================================================

def index(request):
    """Vista principal del dashboard."""
    return render(request, 'dashboard/index.html')

def carga_excel(request):
    """Vista para cargar y procesar el Excel."""
    return render(request, 'dashboard/carga.html')

def dashboard_kpis(request):
    """Vista del dashboard de KPIs estratégicos."""
    return render(request, 'dashboard/kpis.html')

# ============================================================
# API ENDPOINTS (JSON)
# ============================================================

def api_resumen(request):
    """Retorna el resumen operativo (KPIs principales) en JSON con filtros opcionales."""
    carrera = request.GET.get('carrera', '')
    semestre = request.GET.get('semestre', '')
    
    try:
        where_clauses = []
        params = {}
        
        if carrera:
            where_clauses.append("c.nombre = %(carrera)s")
            params['carrera'] = carrera
            
        if semestre:
            where_clauses.append("s.semestre::text = %(semestre)s") # Convertimos a texto para comparar
            params['semestre'] = str(semestre)
        
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        # Usamos una sola conexión para varias consultas si es posible, 
        # pero con tu función ejecutar_query está bien así:
        
        query_total = f"SELECT COUNT(*) as total FROM F_HechoMatricula f INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre {where_sql}"
        res_total = ejecutar_query(query_total, params)
        
        query_unidades = f"SELECT COALESCE(SUM(f.valor_perdida_por_desercion), 0) as total FROM F_HechoMatricula f INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre {where_sql}"
        res_unidades = ejecutar_query(query_unidades, params)

        query_tipos = f"""
            SELECT m.tipo, COUNT(*) as cantidad
            FROM F_HechoMatricula f
            INNER JOIN D_Motivo m ON f.id_motivo = m.id_motivo
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            {where_sql}
            GROUP BY m.tipo
        """
        tipos = ejecutar_query(query_tipos, params)

        return JsonResponse({
            'success': True,
            'total_servicios': res_total[0]['total'] if res_total else 0,
            'total_unidades': float(res_unidades[0]['total']) if res_unidades else 0,
            'tipos': tipos or []
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    """Retorna el resumen operativo (KPIs principales) en JSON con filtros opcionales."""
    carrera = request.GET.get('carrera', '')
    semestre = request.GET.get('semestre', '')
    
    try:
        # Construir cláusula WHERE dinámica
        where_clauses = []
        params = {}
        
        if carrera:
            where_clauses.append("c.nombre = %(carrera)s")
            params['carrera'] = carrera
            
        if semestre:
            where_clauses.append("s.semestre = %(semestre)s")
            params['semestre'] = int(semestre)  # Convertir a entero
        
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # Total servicios (hechos)
        query_total = f"""
            SELECT COUNT(*) as total 
            FROM F_HechoMatricula f
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            {where_sql}
        """
        resultado = ejecutar_query(query_total, params if params else None)
        total_servicios = resultado[0]['total'] if resultado else 0

        # Total unidades (suma de valor_perdida_por_desercion)
        query_unidades = f"""
            SELECT COALESCE(SUM(f.valor_perdida_por_desercion), 0) as total 
            FROM F_HechoMatricula f
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            {where_sql}
        """
        resultado_unidades = ejecutar_query(query_unidades, params if params else None)
        total_unidades = float(resultado_unidades[0]['total']) if resultado_unidades else 0.0

        # Servicios por tipo - Consulta simplificada y robusta
        query_tipos = f"""
            SELECT 
                COALESCE(m.tipo, 'sin definir') as tipo,
                COUNT(*) as cantidad
            FROM F_HechoMatricula f
            INNER JOIN D_Motivo m ON f.id_motivo = m.id_motivo
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            {where_sql}
            GROUP BY m.tipo
            ORDER BY cantidad DESC
        """
        tipos = ejecutar_query(query_tipos, params if params else None)
        
        # Si no hay datos, devolver estructura vacía pero válida
        if not tipos:
            tipos = [{'tipo': 'Área', 'cantidad': 0}, {'tipo': 'Mixta', 'cantidad': 0}]

        return JsonResponse({
            'success': True,
            'total_servicios': total_servicios,
            'total_unidades': total_unidades,
            'tipos': tipos
        })
    except Exception as e:
        # Para debugging: imprime el error en la consola del servidor
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'total_servicios': 0,
            'total_unidades': 0,
            'tipos': []
        })
        
    """Retorna el resumen operativo (KPIs principales) en JSON."""
    try:
        # Total servicios (hechos)
        query_total = "SELECT COUNT(*) as total FROM F_HechoMatricula"
        total_servicios = ejecutar_query(query_total)[0]['total']
        
        # Total unidades (suma de valor_perdida_por_desercion)
        query_unidades = "SELECT COALESCE(SUM(valor_perdida_por_desercion), 0) as total FROM F_HechoMatricula"
        total_unidades = float(ejecutar_query(query_unidades)[0]['total'])
        
        # Servicios por tipo (Mixta/Área)
        query_tipos = """
            SELECT 
                CASE 
                    WHEN motivo = 'mixta' OR motivo ILIKE '%mixt%' THEN 'Mixta'
                    ELSE 'Área'
                END as tipo,
                COUNT(*) as cantidad
            FROM F_HechoMatricula f
            INNER JOIN D_Motivo m ON f.id_motivo = m.id_motivo
            GROUP BY tipo
        """
        tipos = ejecutar_query(query_tipos)
        
        return JsonResponse({
            'success': True,
            'total_servicios': total_servicios,
            'total_unidades': total_unidades,
            'tipos': tipos
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_servicios_por_dia(request):
    """Retorna la distribución de servicios por día en JSON."""
    try:
        query = """
            SELECT 
                CONCAT(fd.anio, '-', LPAD(fd.mes::text, 2, '0'), '-', LPAD(fd.dia::text, 2, '0')) as fecha,
                COUNT(*) as cantidad
            FROM F_HechoMatricula f
            INNER JOIN D_Fecha fd ON f.id_fecha_inicio_semestre = fd.id_fecha
            GROUP BY fd.anio, fd.mes, fd.dia
            ORDER BY fd.anio, fd.mes, fd.dia
        """
        datos = ejecutar_query(query)
        return JsonResponse({'success': True, 'datos': datos})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_kpis(request):
    """Retorna los KPIs estratégicos con filtros opcionales."""
    carrera = request.GET.get('carrera', '')
    semestre = request.GET.get('semestre', '')
    
    try:
        # Construir cláusula WHERE dinámica
        where_clauses = []
        params = {}
        
        if carrera:
            where_clauses.append("c.nombre = %(carrera)s")
            params['carrera'] = carrera
            
        if semestre:
            where_clauses.append("s.semestre = %(semestre)s")
            params['semestre'] = semestre
            
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # KPI 1: Tasa de Deserción Semestral
        query_kpi1 = f"""
            SELECT 
                s.semestre,
                COUNT(DISTINCT CASE WHEN f.id_fecha_desercion != 39991231 THEN a.numero_identificacion END) * 100.0 / 
                NULLIF(COUNT(DISTINCT a.numero_identificacion), 0) as tasa_desercion
            FROM F_HechoMatricula f
            INNER JOIN D_Alumno a ON f.id_alumno = a.id_alumno
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            {where_sql}
            GROUP BY s.semestre
            ORDER BY s.semestre
        """
        kpi1_data = ejecutar_query(query_kpi1, params if params else None)
        
        # KPI 2: Impacto Económico
        query_kpi2 = f"""
            SELECT 
                COALESCE(SUM(f.valor_perdida_por_desercion), 0) as impacto_economico
            FROM F_HechoMatricula f
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            {where_sql}
        """
        kpi2_data = ejecutar_query(query_kpi2, params if params else None)
        
        # KPI 3: Concentración de Riesgo Sociodemográfico
        query_kpi3 = f"""
            SELECT 
                e.descripcion as estrato,
                COUNT(DISTINCT a.numero_identificacion) as estudiantes,
                COUNT(DISTINCT CASE WHEN f.id_fecha_desercion != 39991231 THEN a.numero_identificacion END) as desertores,
                COUNT(DISTINCT CASE WHEN f.id_fecha_desercion != 39991231 THEN a.numero_identificacion END) * 100.0 / 
                NULLIF(COUNT(DISTINCT a.numero_identificacion), 0) as tasa_riesgo
            FROM F_HechoMatricula f
            INNER JOIN D_Alumno a ON f.id_alumno = a.id_alumno
            INNER JOIN D_Estrato e ON a.id_estrato = e.id_estrato
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            {where_sql}
            GROUP BY e.descripcion
            ORDER BY e.descripcion
        """
        kpi3_data = ejecutar_query(query_kpi3, params if params else None)
        
        return JsonResponse({
            'success': True,
            'kpi1_tasa_desercion': kpi1_data,
            'kpi2_impacto_economico': kpi2_data,
            'kpi3_concentracion_riesgo': kpi3_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def api_filtros(request):
    """Retorna las opciones disponibles para los filtros."""
    try:
        carreras = ejecutar_query("SELECT DISTINCT nombre FROM D_Carrera ORDER BY nombre")
        semestres = ejecutar_query("SELECT DISTINCT semestre FROM D_Semestre ORDER BY semestre")
        
        return JsonResponse({
            'success': True,
            'carreras': [c['nombre'] for c in carreras],
            'semestres': [s['semestre'] for s in semestres]
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})