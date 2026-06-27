from fastmcp import FastMCP
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import statistics

load_dotenv()

# CONEXION A SUPABASE

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

mcp = FastMCP("MCP Estación Meteorológica BIU", debug=True)

TABLA = "datos_meteorologicos"
def limpiar_valores(datos, campo): 
    return [ float(x[campo]) 
            for x in datos
              if x.get(campo) is not None 
              ]

# ==================================================================================
# FUNCIONES INTERNAS PROPORCIONADAS POR EL DOCENTE QUE EXTRAEN LOS DATOS DE LA TABLA
# ===================================================================================

def _obtener_ultima_lectura():

    response = (
        supabase.table(TABLA)
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return {"mensaje": "No se encuentran lecturas registradas"}

    return response.data[0]


def _obtener_ultimas_lecturas(limite=10):

    response = (
        supabase.table(TABLA)
        .select("*")
        .order("created_at", desc=True)
        .limit(limite)
        .execute()
    )

    return response.data


def _obtener_datos_grafico(limite=20):


#Obtener los datos registrados en la tabla datos_meteorologicos
    response = (
        supabase.table(TABLA)
        .select("created_at,temperatura,humedad,presion,latitud,longitud")
        .order("created_at")
        .limit(limite)
        .execute()
    )

    return response.data


def _obtener_resumen_estacion(limite=20):

    datos = _obtener_ultimas_lecturas(limite)

    if not datos:
        return {"mensaje": "No se encuentran datos registrados en la Estación Meterologica BIU"}

    temperaturas = limpiar_valores(datos, "temperatura")
    humedades = limpiar_valores(datos, "humedad")
    presiones = limpiar_valores(datos, "presion")
    latitudes = limpiar_valores(datos, "latitud")
    longitudes = limpiar_valores(datos, "longitud")

    return {
        "total_lecturas": len(datos),
        "temperatura_promedio": round(statistics.mean(temperaturas),2) if temperaturas else None,
        "temperatura_maxima": max(temperaturas),
        "temperatura_minima": min(temperaturas),
        "humedad_promedio": round(statistics.mean(humedades),2),
        "humedad_maxima": max(humedades),
        "humedad_minima": min(humedades),
        "presion_promedio": round(statistics.mean(presiones),2),
        "presion_maxima": max(presiones),
        "presion_minima": min(presiones),
        "ultima_latitud": latitudes[-1] if latitudes else None,
        "ultima_longitud": longitudes[-1] if longitudes else None
    }


def _detectar_alertas():

    lectura = _obtener_ultima_lectura()

    if "mensaje" in lectura:
        return lectura

    alertas = []

    temp = float(lectura.get("temperatura") or 0)
    humedad = float(lectura.get("humedad") or 0)
    presion = float(lectura.get("presion") or 0)

    if temp >= 30:
        alertas.append("Temperatura alta")

    if temp <= 15:
        alertas.append("Temperatura baja")

    if humedad >= 85:
        alertas.append("Humedad elevada")

    if presion < 1000:
        alertas.append("Posible lluvia")

    return {
        "estado": "Con alertas" if alertas else "Normal",
        "alertas": alertas
    }


def _datos_para_dashboard(limite=100):

    return {
        "ultima_lectura": _obtener_ultima_lectura(),
        "resumen": _obtener_resumen_estacion(limite),
        "alertas": _detectar_alertas(),
        "historico": _obtener_datos_grafico(limite),
        "tabla": _obtener_ultimas_lecturas(limite)
    }

# ==========================
# HERRAMIENTAS MCP
# ==========================

@mcp.tool()
def obtener_ultima_lectura():
    """
    Obtiene la lectura más reciente registrada por la estación meteorológica.

    Usar esta herramienta cuando el usuario pregunte por:
    - temperatura actual
    - humedad actual
    - presión actual
    - última lectura del sensor
    - estado actual de la estación meteorológica

    Devuelve:
    - id
    - fecha y hora de registro
    - temperatura
    - humedad
    - presión atmosférica
    - Coordenadas de ubicación de la estación: latitud y longitud

    No usar para:
    - históricos
    - gráficos
    - promedios
    - análisis de tendencias
    """
    return _obtener_ultima_lectura()


@mcp.tool()
def obtener_ultimas_lecturas(limite: int = 10):
    """
    Obtiene las últimas lecturas registradas en la estación meteorológica.

    Usar esta herramienta cuando el usuario pida:
    - últimas lecturas
    - tabla de datos recientes
    - registros recientes del sensor
    - listado de mediciones
    - últimos datos guardados en Supabase

    Parámetros:
    - limite: número máximo de registros a devolver. Por defecto 10.

    Devuelve una lista ordenada desde la lectura más reciente hacia atrás.

    No usar para:
    - resumen estadístico
    - alertas
    - gráficos cronológicos completos
    """
    return _obtener_ultimas_lecturas(limite)


@mcp.tool()
def obtener_datos_grafico(limite: int = 20):
    """
    Obtiene datos meteorológicos preparados para construir gráficos.

    Usar esta herramienta cuando el usuario solicite:
    - gráfico de temperatura
    - gráfico de humedad
    - gráfico de presión
    - serie temporal
    - visualización histórica
    - datos para dashboard gráfico

    Parámetros:
    - limite: número máximo de registros a devolver. Por defecto 20.

    Devuelve:
    - fecha y hora
    - temperatura
    - humedad
    - presión
    - id del sensor

    Los datos se devuelven ordenados cronológicamente.

    No usar para:
    - última lectura actual
    - tabla de registros recientes
    - alertas automáticas
    """
    return _obtener_datos_grafico(limite)


@mcp.tool()
def obtener_resumen_estacion(limite: int = 100):
    """
    Calcula un resumen estadístico de la estación meteorológica.

    Usar esta herramienta cuando el usuario pregunte por:
    - promedio de temperatura
    - temperatura máxima o mínima
    - humedad promedio
    - presión promedio
    - resumen general de la estación
    - estadísticas de las lecturas

    Parámetros:
    - limite: cantidad de lecturas recientes que se usarán para calcular el resumen. Por defecto 100.

    Devuelve:
    - total de lecturas analizadas
    - temperatura promedio, máxima y mínima
    - humedad promedio, máxima y mínima
    - presión promedio, máxima y mínima

    No usar para:
    - obtener solo la última lectura
    - generar una tabla detallada
    - detectar alertas actuales
    """
    return _obtener_resumen_estacion(limite)


@mcp.tool()
def detectar_alertas():
    """
    Detecta alertas meteorológicas usando la última lectura registrada.

    Usar esta herramienta cuando el usuario pregunte:
    - hay alertas
    - estado de riesgo
    - temperatura alta
    - posible lluvia
    - humedad elevada
    - estado actual de la estación

    Criterios de alerta:
    - temperatura >= 35: temperatura alta
    - temperatura <= 15: temperatura baja
    - humedad >= 85: humedad elevada
    - presión < 1000: posible lluvia

    Devuelve:
    - estado general: Normal o Con alertas
    - lista de alertas detectadas

    No usar para:
    - análisis histórico
    - gráficos
    - promedios
    """
    return _detectar_alertas()


@mcp.tool()
def datos_para_dashboard(limite: int = 100):
    """
    Obtiene todos los datos necesarios para construir un dashboard meteorológico completo.

    Usar esta herramienta cuando el usuario solicite:
    - crear dashboard
    - panel meteorológico
    - página web de monitoreo
    - dashboard tipo Power BI
    - dashboard tipo Grafana
    - indicadores, gráficos, alertas y tabla en una sola vista

    Parámetros:
    - limite: número máximo de registros recientes para gráficos, tabla y resumen. Por defecto 100.

    Devuelve:
    - última lectura
    - resumen estadístico
    - alertas actuales
    - histórico para gráficos
    - tabla de lecturas recientes

    Esta es la herramienta recomendada para construir interfaces web, dashboards o reportes completos.
    """
    return _datos_para_dashboard(limite)

@mcp.prompt()
def prompt_dashboard_tendencias(fecha_inicio: str, fecha_fin: str):
    """
    Prompt para analizar tendencias entre dos fechas.
    """
    return f"""
Utiliza la herramienta obtener_lecturas_por_fecha(
    fecha_inicio="{fecha_inicio}",
    fecha_fin="{fecha_fin}"
).

Construye un dashboard analítico de tendencias para una estación meteorológica.

Incluye:

1. Serie temporal de temperatura.
2. Serie temporal de humedad.
3. Serie temporal de presión atmosférica.
5. Detección automática de:
   - Picos máximos
   - Picos mínimos
   - Cambios bruscos
6. Estadísticas:
   - Promedio
   - Desviación estándar
   - Valor máximo
   - Valor mínimo
7. Conclusiones automáticas sobre el comportamiento de la estación.

El dashboard debe ser una página web descargable.
Entrega el resultado como una página web completa en HTML, CSS y JavaScript.
El diseño debe ser tipo Power BI o Grafana.
"""

@mcp.prompt()
def prompt_dashboard_personalizado(tipo_dashboard: str = "ejecutivo", limite: int = 100):
    return f"""
Utiliza la herramienta datos_para_dashboard(limite={limite}).

Crea un dashboard meteorológico de tipo: {tipo_dashboard}.

Incluye KPIs, gráficos interactivos, alertas automáticas, tabla de lecturas recientes y conclusiones.

Entrega el resultado como una página web completa en HTML, CSS y JavaScript.
"""
if __name__ == "__main__":
    mcp.run()