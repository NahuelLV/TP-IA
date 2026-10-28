import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Configuración de la página web
st.set_page_config(page_title="Optimizador Inmobiliario", page_icon="🏡", layout="wide")

st.title("🏡 Optimizador Inmobiliario")
st.markdown("### Sistema Experto de Búsqueda de Primera Vivienda")
st.markdown("Definí tus criterios en el menú lateral y nuestro motor de inferencia filtrará las mejores opciones del mercado.")

# 2. Carga de datos
@st.cache_data
def cargar_datos():
    file_id = '1eNFGYL2YttBPRyZjjkJJEBm8y-N3Fg7U'
    url = f'https://drive.google.com/uc?id={file_id}'
    
    inmuebles = pd.read_csv(url, sep=';')
    inmuebles = inmuebles.drop_duplicates()
    
    columnas_utiles = ['property_type', 'place_with_parent_names', 'price_aprox_usd', 'surface_total_in_m2', 'rooms', 'lat-lon']
    df_limpio = inmuebles[columnas_utiles].copy()
    
    for col in ['price_aprox_usd', 'surface_total_in_m2', 'rooms']:
        df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')
        
    df_limpio = df_limpio.dropna(subset=['price_aprox_usd'])
    return df_limpio

df_limpio = cargar_datos()

# 3. Interfaz del Menú Lateral
st.sidebar.header("🔍 Filtros del Sistema Experto")

opcion_tipo = st.sidebar.selectbox(
    "1. ¿Qué tipo de propiedad buscas?",
    ["Todos / Indiferente", "Departamento (apartment)", "Casa (house)", "PH"]
)

presupuesto = st.sidebar.number_input(
    "2. Presupuesto máximo (USD) - 0 para sin límite:", 
    min_value=0, value=150000, step=10000
)

ambientes = st.sidebar.number_input(
    "3. Cantidad mínima de ambientes:", 
    min_value=1, value=2, step=1
)

barrio = st.sidebar.text_input("4. ¿Algún barrio o zona específica? (Opcional)")

excluir = st.sidebar.text_input("5. ¿Querés excluir alguna zona? (Opcional)")

# 4. Botón de Búsqueda y Lógica (CON MEMORIA AGREGADA)
# Guardamos en la "memoria" si el botón fue presionado
if st.sidebar.button("Buscar Propiedades 🚀"):
    st.session_state['buscar'] = True

# Verificamos si la memoria recuerda que buscamos algo
if st.session_state.get('buscar', False):
    df_filtrado = df_limpio.copy()

    if "Departamento" in opcion_tipo:
        df_filtrado = df_filtrado[df_filtrado['property_type'].str.contains('apartment', case=False, na=False)]
    elif "Casa" in opcion_tipo:
        df_filtrado = df_filtrado[df_filtrado['property_type'].str.contains('house', case=False, na=False)]
    elif "PH" in opcion_tipo:
        df_filtrado = df_filtrado[df_filtrado['property_type'].str.contains('PH', case=False, na=False)]

    if presupuesto > 0:
        df_filtrado = df_filtrado[df_filtrado['price_aprox_usd'] <= presupuesto]

    df_filtrado = df_filtrado[df_filtrado['rooms'] >= ambientes]

    if barrio:
        df_filtrado = df_filtrado[df_filtrado['place_with_parent_names'].str.contains(barrio, case=False, na=False)]
        
    if excluir:
        df_filtrado = df_filtrado[~df_filtrado['place_with_parent_names'].str.contains(excluir, case=False, na=False)]

    # 5. Mostrar Resultados
    st.subheader(f"✅ Propiedades que cumplen con las reglas: {len(df_filtrado)}")

    if len(df_filtrado) > 0:
        df_filtrado = df_filtrado.sort_values(by=['surface_total_in_m2', 'price_aprox_usd'], ascending=False)
        
        st.markdown("#### 🏆 Top 5 de opciones recomendadas:")
        columnas_mostrar = ['property_type', 'price_aprox_usd', 'surface_total_in_m2', 'rooms', 'place_with_parent_names']
        vista_top5 = df_filtrado[columnas_mostrar].head(5).copy()
        vista_top5['price_aprox_usd'] = vista_top5['price_aprox_usd'].apply(lambda x: f"USD {x:,.0f}")
        
        st.dataframe(vista_top5, use_container_width=True)

        st.markdown("#### 🗺️ Mapa de Ubicaciones (Top 100)")
        
        if 'lat-lon' in df_filtrado.columns:
            df_filtrado[['lat', 'lon']] = df_filtrado['lat-lon'].str.split(',', expand=True).astype(float)

        if 'lat' in df_filtrado.columns and 'lon' in df_filtrado.columns:
            df_mapa = df_filtrado.dropna(subset=['lat', 'lon']).head(100)

            if len(df_mapa) > 0:
                lat_centro = df_mapa['lat'].mean()
                lon_centro = df_mapa['lon'].mean()

                mapa_propiedades = folium.Map(location=[lat_centro, lon_centro], zoom_start=12, tiles='Esri.WorldStreetMap')

                for idx, row in df_mapa.iterrows():
                    popup_texto = f"Tipo: {row['property_type']}<br>Precio: USD {row['price_aprox_usd']}<br>Superficie: {row['surface_total_in_m2']} m²"

                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=5,
                        popup=popup_texto,
                        color='blue',
                        fill=True,
                        fill_color='blue',
                        fill_opacity=0.6
                    ).add_to(mapa_propiedades)

                # El returned_objects=[] evita que interactuar con el mapa recargue toda la página
                st_folium(mapa_propiedades, width=1000, height=500, returned_objects=[])
            else:
                st.warning("🗺️ Las propiedades encontradas no tienen coordenadas geográficas válidas para mostrar en el mapa.")
        else:
            st.warning("🗺️ El dataset no cuenta con la columna de coordenadas ('lat-lon').")
    else:
        st.warning("💡 No se encontraron propiedades con esa combinación exacta de filtros. ¡Probá relajando alguna condición!")
