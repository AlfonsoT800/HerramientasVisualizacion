# Dashboard meteorológico - Práctica 8B
# Ejecutar: streamlit run dashboard.py
# Instalar: pip install streamlit requests pandas matplotlib seaborn

import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

GRIS = "#B9C3D1"
AZUL = "#1C4C9A"
ROJO = "#B2182B"
NARANJA = "#E69F00"
sns.set_theme(style="whitegrid")

CIUDADES = {
    "Morelia": (19.7008, -101.1844),
    "Querétaro": (20.5888, -100.3899),
}

VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "precipitation_sum",
    "precipitation_hours",
    "windspeed_10m_max",
    "shortwave_radiation_sum",
]

NOMBRES = {
    "temperature_2m_max": "TempMax",
    "temperature_2m_min": "TempMin",
    "temperature_2m_mean": "TempMedia",
    "apparent_temperature_max": "Sensacion",
    "precipitation_sum": "Lluvia",
    "precipitation_hours": "HorasLluvia",
    "windspeed_10m_max": "Viento",
    "shortwave_radiation_sum": "Radiacion",
}

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

st.set_page_config(
    page_title="Dashboard meteorológico",
    page_icon="🌦️",
    layout="wide",
)

st.title("Dashboard meteorológico")
st.caption("Práctica 8B · Herramientas de Visualización · IDIA224 · Unidad II")
st.write(
    "Explora los datos históricos de temperatura, precipitación y radiación solar "
    "obtenidos de la API de Open-Meteo."
)

with st.sidebar:
    st.header("Filtros")
    ciudad = st.selectbox("Ciudad", list(CIUDADES.keys()))
    anio = st.selectbox("Año para la gráfica anual", list(range(2021, 2026)), index=4)
    st.caption("La API histórica puede tardar unos segundos en responder.")

@st.cache_data(ttl=3600, show_spinner="Consultando datos meteorológicos...")
def cargar_datos(nombre_ciudad):
    latitud, longitud = CIUDADES[nombre_ciudad]
    respuesta = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": latitud,
            "longitude": longitud,
            "start_date": "2021-01-01",
            "end_date": "2025-12-31",
            "daily": ",".join(VARIABLES),
            "timezone": "America/Mexico_City",
        },
        timeout=60,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    tabla = pd.DataFrame(datos["daily"])
    tabla["time"] = pd.to_datetime(tabla["time"])
    tabla = tabla.rename(columns={"time": "Fecha", **NOMBRES})
    tabla["Anio"] = tabla["Fecha"].dt.year
    tabla["Mes"] = tabla["Fecha"].dt.month
    tabla["Amplitud"] = tabla["TempMax"] - tabla["TempMin"]
    tabla["Temporada"] = tabla["Mes"].apply(
        lambda m: "Lluvias" if 6 <= m <= 10 else "Secas"
    )
    return tabla, datos["daily_units"]

try:
    df, unidades = cargar_datos(ciudad)
except requests.RequestException as exc:
    st.error(f"No se pudieron obtener los datos de Open-Meteo: {exc}")
    st.stop()
except (KeyError, ValueError) as exc:
    st.error(f"La respuesta de la API no tiene el formato esperado: {exc}")
    st.stop()

datos_anio = df[df["Anio"] == anio]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Días consultados", f"{len(df):,}")
c2.metric("Temperatura media", f"{df['TempMedia'].mean():.1f} °C")
c3.metric("Lluvia acumulada", f"{df['Lluvia'].sum():,.1f} mm")
c4.metric("Radiación media diaria", f"{df['Radiacion'].mean():,.0f}")

st.subheader(f"Gráfica 4 · Radiación solar contra temperatura — {ciudad}")
st.write(
    "Cada punto representa un día. La línea roja resume la tendencia lineal; "
    "una asociación no demuestra por sí sola causalidad."
)
fig4, ax4 = plt.subplots(figsize=(10, 5))
sns.scatterplot(
    data=df, x="Radiacion", y="TempMedia",
    color=AZUL, alpha=0.30, s=18, ax=ax4
)
sns.regplot(
    data=df, x="Radiacion", y="TempMedia",
    scatter=False, color=ROJO,
    line_kws={"linewidth": 2}, ax=ax4
)
ax4.set_title(f"Radiación solar contra temperatura media en {ciudad}")
ax4.set_xlabel(f"Radiación solar ({unidades.get('shortwave_radiation_sum', 'unidad de API')})")
ax4.set_ylabel(f"Temperatura media ({unidades.get('temperature_2m_mean', '°C')})")
fig4.tight_layout()
st.pyplot(fig4, use_container_width=True)
plt.close(fig4)

st.subheader("Gráfica 5 · Mapa de calor mes por año")
st.write("Los valores de las celdas son promedios mensuales de temperatura media.")
tabla_calor = df.pivot_table(
    index="Anio", columns="Mes", values="TempMedia", aggfunc="mean"
).reindex(index=range(2021, 2026), columns=range(1, 13))
tabla_calor.columns = MESES

fig5, ax5 = plt.subplots(figsize=(12, 5))
sns.heatmap(
    tabla_calor, annot=True, fmt=".1f", cmap="coolwarm",
    linewidths=0.5,
    cbar_kws={"label": f"Temperatura media ({unidades.get('temperature_2m_mean', '°C')})"},
    ax=ax5,
)
ax5.set_title(f"Temperatura media por mes y año — {ciudad}")
ax5.set_xlabel("Mes")
ax5.set_ylabel("Año")
fig5.tight_layout()
st.pyplot(fig5, use_container_width=True)
plt.close(fig5)

st.subheader(f"Exploración adicional · Datos de {anio}")
tab1, tab2 = st.tabs(["Temperaturas", "Tabla de datos"])
with tab1:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(
        datos_anio["Fecha"], datos_anio["TempMin"], datos_anio["TempMax"],
        color=GRIS, label="Rango mínima–máxima"
    )
    ax.plot(datos_anio["Fecha"], datos_anio["TempMedia"],
            color=AZUL, linewidth=1.5, label="Temperatura media")
    ax.set_title(f"Rango de temperatura en {ciudad}, {anio}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel(f"Temperatura ({unidades.get('temperature_2m_mean', '°C')})")
    ax.legend(frameon=False)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
with tab2:
    st.dataframe(
        datos_anio[["Fecha", "TempMax", "TempMin", "TempMedia",
                    "Lluvia", "Viento", "Radiacion"]],
        use_container_width=True,
        hide_index=True,
    )

st.caption("Fuente de datos: Open-Meteo Historical Weather API. Datos sujetos a disponibilidad de la API.")
