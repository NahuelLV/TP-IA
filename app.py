import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# 1. Configuración de la página web
st.set_page_config(
    page_title="Optimizador Inmobiliario", page_icon="🏡", layout="wide"
)

st.title("🏡 Optimizador Inmobiliario")
st.markdown("### Sistema Experto de Búsqueda de Primera Vivienda")
st.markdown(
    "Definí tus criterios en el menú lateral y nuestro motor de inferencia"
    " filtrará las mejores opciones del mercado."
)


# 2. Carga de datos
@st.cache_data
def cargar_datos():
  file_id = "1eNFGYL2YttBPRyZjjkJJEBm8y-N3Fg7U"
  url = f"https://drive.google.com/uc?id={file_id}"

  inmuebles = pd.read_csv(url, sep=";")
  inmuebles = inmuebles.drop_duplicates()

  columnas_utiles = [
      "property_type",
      "place_with_parent_names",
      "price",
      "price_aprox_usd",
      "surface_total_in_m2",
      "rooms",
  ]
  df_limpio = inmuebles[columnas_utiles].copy()
  df_limpio = df_limpio.dropna(subset=["price"])
  df_limpio["rooms"] = df_limpio["rooms"].fillna(2)

  return df_limpio


df_limpio = cargar_datos()

# 3. Interfaz del Menú Lateral
st.sidebar.header("🔍 Filtros del Sistema Experto")

opcion_tipo = st.sidebar.selectbox(
    "1. ¿Qué tipo de propiedad buscas?",
    ["Todos / Indiferente", "Departamento (apartment)", "Casa (house)", "PH"],
)

presupuesto = st.sidebar.number_input(
    "2. Presupuesto máximo (USD) - 0 para sin límite:",
    min_value=0,
    value=150000,
    step=10000,
)

ambientes = st.sidebar.number_input(
    "3. Cantidad mínima de ambientes:", min_value=1, value=2, step=1
)

barrio = st.sidebar.text_input("4. ¿Algún barrio o zona específica? (Opcional)")

excluir = st.sidebar.text_input("5. ¿Querés excluir alguna zona? (Opcional)")

# 4. Botón de Búsqueda y Lógica
if st.sidebar.button("Buscar Propiedades 🚀"):
  df_filtrado = df_limpio.copy()

  if "Departamento" in opcion_tipo:
    df_filtrado = df_filtrado[
        df_filtrado["property_type"].str.contains(
            "apartment", case=False, na=False
        )
    ]
  elif "Casa" in opcion_tipo:
    df_filtrado = df_filtrado[
        df_filtrado["property_type"].str.contains("house", case=False, na=False)
    ]
  elif "PH" in opcion_tipo:
    df_filtrado = df_filtrado[
        df_filtrado["property_type"].str.contains("PH", case=False, na=False)
    ]

  if presupuesto > 0:
    df_filtrado = df_filtrado[df_filtrado["price_aprox_usd"] <= presupuesto]

  df_filtrado = df_filtrado[df_filtrado["rooms"] >= ambientes]

  if barrio:
    df_filtrado = df_filtrado[
        df_filtrado["place_with_parent_names"].str.contains(
            barrio, case=False, na=False
        )
    ]

  if excluir:
    df_filtrado = df_filtrado[
        ~df_filtrado["place_with_parent_names"].str.contains(
            excluir, case=False, na=False
        )
    ]

  st.subheader(
      f"✅ Propiedades que cumplen con las reglas: {len(df_filtrado)}"
  )

  if len(df_filtrado) > 0:
    df_filtrado = df_filtrado.sort_values(
        by=["surface_total_in_m2", "price_aprox_usd"], ascending=False
    )

    st.markdown("#### 🏆 Top 5 de opciones recomendadas:")
    columnas = [
        "property_type",
        "price_aprox_usd",
        "surface_total_in_m2",
        "rooms",
        "place_with_parent_names",
    ]
    vista_top5 = df_filtrado[columnas].head(5).copy()
    vista_top5["price_aprox_usd"] = vista_top5["price_aprox_usd"].apply(
        lambda x: f"USD {x:,.0f}"
    )

    st.dataframe(vista_top5, use_container_width=True)

    st.markdown("#### 📊 Relación Superficie vs. Precio (Top 200)")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))

    sns.scatterplot(
        data=df_filtrado.head(200),
        x="surface_total_in_m2",
        y="price_aprox_usd",
        hue="property_type",
        alpha=0.8,
        s=70,
        palette="viridis",
        ax=ax,
    )
    ax.set_xlabel("Superficie Total (m²)")
    ax.set_ylabel("Precio (USD)")
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, p: f"${x:,.0f}")
    )
    plt.legend(
        title="Tipo de Propiedad", bbox_to_anchor=(1.05, 1), loc="upper left"
    )

    st.pyplot(fig)
  else:
    st.warning(
        "💡 No se encontraron propiedades con esa combinación exacta. ¡Probá"
        " relajando alguna condición en el menú izquierdo!"
    )
