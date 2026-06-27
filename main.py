from fastmcp import FastMCP
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import statistics

print("INICIANDO MCP BIU")

load_dotenv()

# CONEXION A SUPABASE

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

mcp = FastMCP("MCP Estación Meteorológica BIU")

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
# HERRAMIENTAS MCP Proporcionadas por el Profesor)
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
    """
    return _obtener_ultima_lectura()


@mcp.tool()
def obtener_ultimas_lecturas(limite: int = 50):
    """
    Obtiene las últimas lecturas registradas en la estación meteorológica.
    """
    return _obtener_ultimas_lecturas(limite)


@mcp.tool()
def obtener_datos_grafico(limite: int = 100):
    """
    Obtiene datos meteorológicos preparados para construir gráficos.
    """
    return _obtener_datos_grafico(limite)


@mcp.tool()
def obtener_resumen_estacion(limite: int = 100):
    """
    Calcula un resumen estadístico de la estación meteorológica.
    """
    return _obtener_resumen_estacion(limite)


@mcp.tool()
def detectar_alertas():
    """
    Detecta alertas meteorológicas usando la última lectura registrada.
    """
    return _detectar_alertas()


@mcp.tool()
def datos_para_dashboard(limite: int = 100):
    """
    Obtiene todos los datos necesarios para construir un dashboard meteorológico completo.
    """
    return _datos_para_dashboard(limite)

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