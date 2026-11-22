import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns
import streamlit as st
import folium
from streamlit_folium import st_folium

# 1. Configuración de la página
st.set_page_config(page_title="Optimizador Inmobiliario", page_icon="🏡", layout="wide")

# 2. CSS personalizado
st.markdown("""
    <style>
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.8rem;}

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    h1 {
        font-weight: 800;
        margin-bottom: 0;
    }
    h1 span {
        background: linear-gradient(90deg, #00C49A, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Tarjetas de métricas (KPIs) */
    [data-testid="stMetric"] {
        background-color: #151C2C;
        border: 1px solid #263147;
        padding: 14px 18px;
        border-radius: 12px;
        animation: fadeIn 0.5s ease-out;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        color: #F8FAFC;
        font-size: 1.5rem;
        font-weight: 700;
    }

    /* Botón principal */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00C49A 0%, #0284C7 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        width: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0, 196, 154, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado con emoji a color y texto degradado
st.markdown('<h1><span>Optimizador Inmobiliario</span></h1>', unsafe_allow_html=True)
st.caption("Sistema Experto de recomendación y georreferenciación de propiedades")

# 3. Carga de datos
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

# 4. Menú Lateral
st.sidebar.header("Filtros de Búsqueda")

opcion_tipo = st.sidebar.selectbox(
    "Tipo de propiedad",
    ["Todos / Indiferente", "Departamento (apartment)", "Casa (house)", "PH"]
)

presupuesto = st.sidebar.number_input(
    "Presupuesto máximo (USD) — 0 sin límite", 
    min_value=0, value=200000, step=10000
)

ambientes = st.sidebar.number_input(
    "Mínimo de ambientes", 
    min_value=1, value=2, step=1
)

barrio = st.sidebar.text_input("Barrio o zona (Opcional)", placeholder="Ej: Villa Luro, Palermo...")
excluir = st.sidebar.text_input("Excluir zona (Opcional)", placeholder="Ej: Centro...")

if st.sidebar.button("Buscar Propiedades"):
    st.session_state['buscar'] = True

# 5. Motor de Inferencia y Visualización
if st.session_state.get('buscar', True):
    with st.spinner("Aplicando reglas del sistema experto..."):
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

    if len(df_filtrado) > 0:
        # Fila de Tarjetas KPI
        precio_prom = df_filtrado['price_aprox_usd'].mean()
        sup_valida = df_filtrado[df_filtrado['surface_total_in_m2'] > 0]['surface_total_in_m2']
        sup_prom = sup_valida.mean() if len(sup_valida) > 0 else 0
        usd_m2 = (precio_prom / sup_prom) if sup_prom > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Propiedades Encontradas", f"{len(df_filtrado):,}")
        k2.metric("Precio Promedio", f"USD {precio_prom:,.0f}")
        k3.metric("Superficie Media", f"{sup_prom:,.0f} m²" if sup_prom > 0 else "N/D")
        k4.metric("Valor Promedio / m²", f"USD {usd_m2:,.0f}" if usd_m2 > 0 else "N/D")

        st.markdown("<br>", unsafe_allow_html=True)

        # Pestañas para organizar sin llenar de texto
        tab_mapa, tab_analisis = st.tabs(["🗺️ Mapa y Top Recomendaciones", "📊 Análisis de Mercado"])

        with tab_mapa:
            col_mapa, col_tabla = st.columns([1.2, 1])

            with col_mapa:
                st.markdown("**Ubicación Geográfica (Top 100)**")
                if 'lat-lon' in df_filtrado.columns:
                    coords = df_filtrado['lat-lon'].dropna().str.split(',', expand=True)
                    if coords.shape[1] == 2:
                        df_filtrado['lat'] = pd.to_numeric(coords[0], errors='coerce')
                        df_filtrado['lon'] = pd.to_numeric(coords[1], errors='coerce')

                if 'lat' in df_filtrado.columns and 'lon' in df_filtrado.columns:
                    df_mapa = df_filtrado.dropna(subset=['lat', 'lon']).head(100)
                    if len(df_mapa) > 0:
                        mapa_propiedades = folium.Map(
                            location=[df_mapa['lat'].mean(), df_mapa['lon'].mean()],
                            zoom_start=12,
                            tiles='Esri.WorldStreetMap'
                        )
                        for _, row in df_mapa.iterrows():
                            popup_texto = f"<b>{row['property_type'].upper()}</b><br>USD {row['price_aprox_usd']:,.0f}<br>{row['surface_total_in_m2']} m²"
                            folium.CircleMarker(
                                location=[row['lat'], row['lon']],
                                radius=7,
                                popup=popup_texto,
                                color='#0B0F19',
                                weight=1.5,
                                fill=True,
                                fill_color='#00C49A',
                                fill_opacity=0.9
                            ).add_to(mapa_propiedades)

                        st_folium(mapa_propiedades, height=390, use_container_width=True, returned_objects=[])
                    else:
                        st.info("Sin coordenadas válidas para graficar en esta búsqueda.")

            with col_tabla:
                st.markdown("**Top 5 Mejores Opciones**")
                df_filtrado = df_filtrado.sort_values(by=['surface_total_in_m2', 'price_aprox_usd'], ascending=False)
                vista = df_filtrado[['property_type', 'price_aprox_usd', 'surface_total_in_m2', 'rooms', 'place_with_parent_names']].head(5).copy()

                nombres_tipo = {'apartment': 'Depto', 'house': 'Casa', 'PH': 'PH', 'store': 'Local'}
                vista['property_type'] = vista['property_type'].map(nombres_tipo).fillna(vista['property_type'])
                vista['price_aprox_usd'] = vista['price_aprox_usd'].apply(lambda x: f"USD {x:,.0f}")
                vista['surface_total_in_m2'] = vista['surface_total_in_m2'].apply(lambda x: f"{x:,.0f} m²" if pd.notna(x) else "-")
                vista['rooms'] = vista['rooms'].apply(lambda x: f"{int(x)} amb." if pd.notna(x) else "-")
                vista['place_with_parent_names'] = vista['place_with_parent_names'].apply(
                    lambda x: " › ".join([p for p in str(x).split('|') if p][-2:])
                )

                vista.columns = ['Tipo', 'Precio', 'Sup.', 'Amb.', 'Ubicación']
                st.dataframe(vista, use_container_width=True, hide_index=True, height=235)

        with tab_analisis:
            st.markdown("**Relación Superficie vs. Precio en tu búsqueda**")
            df_plot = df_filtrado.dropna(subset=['surface_total_in_m2', 'price_aprox_usd']).head(250)
            if len(df_plot) > 2:
                plt.style.use("dark_background")
                fig, ax = plt.subplots(figsize=(9, 3.8))
                fig.patch.set_facecolor('#0B0F19')
                ax.set_facecolor('#151C2C')
                sns.scatterplot(
                    data=df_plot,
                    x='surface_total_in_m2',
                    y='price_aprox_usd',
                    hue='property_type',
                    palette=['#00C49A', '#38BDF8', '#F59E0B', '#A855F7'],
                    s=65,
                    alpha=0.85,
                    ax=ax
                )
                ax.set_xlabel("Superficie Total (m²)", color="#94A3B8")
                ax.set_ylabel("Precio (USD)", color="#94A3B8")
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
                ax.grid(True, linestyle='--', alpha=0.2)
                plt.legend(title="Tipo", frameon=False)
                st.pyplot(fig)
            else:
                st.info("Se necesitan más propiedades para mostrar la distribución gráfica.")
    else:
        st.warning("No se encontraron propiedades con esos filtros. Probá ampliar el presupuesto o cambiar la zona.")
