import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA DE STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Video Game Market | Dashboard Ejecutivo",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo general de gráficos
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({'figure.max_open_warning': 0})

# ----------------------------------------------------------------------------------
# 1. FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS
# ----------------------------------------------------------------------------------
# cache_resource y no cache_data: no serializa el DataFrame (en la demo con stlite el pandas
# de Pyodide falla al deserializar fechas) y la app nunca modifica el df cacheado.
@st.cache_resource
def load_and_clean_data(file_path="vgchartz-2024.csv"):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        df = pd.read_csv("Data/vgchartz-2024.csv")
    n_crudo = len(df)

    columnas_originales = df.columns.tolist()
    mapeo_columnas = {}

    for col in columnas_originales:
        col_low = col.lower().strip()
        if col_low in ['year', 'year_of_release', 'release_year']: mapeo_columnas[col] = 'year'
        elif col_low in ['total_sales', 'global_sales', 'sales', 'total_sales_millions']: mapeo_columnas[col] = 'total_sales'
        elif col_low in ['genre', 'genero']: mapeo_columnas[col] = 'genre'
        elif col_low in ['console', 'platform', 'plataforma']: mapeo_columnas[col] = 'console'
        elif col_low in ['critic_score', 'score', 'critic']: mapeo_columnas[col] = 'critic_score'
        elif col_low in ['release_date', 'date', 'fecha']: mapeo_columnas[col] = 'release_date'
        elif col_low in ['na_sales', 'na_sales_millions']: mapeo_columnas[col] = 'na_sales'
        elif col_low in ['jp_sales', 'jp_sales_millions']: mapeo_columnas[col] = 'jp_sales'
        elif col_low in ['pal_sales', 'eu_sales', 'europe_sales']: mapeo_columnas[col] = 'pal_sales'
        elif col_low in ['other_sales', 'others_sales']: mapeo_columnas[col] = 'other_sales'

    df = df.rename(columns=mapeo_columnas)

    # Sanitización de variables cualitativas críticas
    df['genre'] = df['genre'].fillna('Unknown')
    df['console'] = df['console'].fillna('Unknown')

    # Rellenamos las ventas vacías con 0 en lugar de borrarlas para que el PC no desaparezca del catálogo por culpa del formato digital
    df['total_sales'] = df['total_sales'].fillna(0)
    for col_reg in ['na_sales', 'pal_sales', 'jp_sales', 'other_sales']:
        if col_reg in df.columns:
            df[col_reg] = df[col_reg].fillna(0)

    # Convertimos fecha y aseguramos la existencia de la columna 'year' ANTES de filtrar
    if 'release_date' in df.columns:
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

    if 'year' not in df.columns or df['year'].isnull().all():
        if 'release_date' in df.columns:
            df['year'] = df['release_date'].dt.year

    # Conservamos los juegos con ventas y, además, los de PC con año válido: VGChartz no recoge
    # ventas digitales, así que sin esta excepción el PC casi desaparecería del catálogo.
    df = df[(df['total_sales'] > 0) | ((df['console'].str.lower().str.strip() == 'pc') & (df['year'].notnull()) & (df['year'] > 1980))]

    # Limpieza final de nulos de años remanentes y casteo a entero
    df = df.dropna(subset=['year'])
    df['year'] = df['year'].astype(int)

    return df, n_crudo

df, df_raw_len = load_and_clean_data()

img_col = next((c for c in df.columns if 'img' in c or 'image' in c or 'url' in c), 'img')
title_col = next((c for c in df.columns if 'title' in c or 'name' in c), 'title')
sales_col = next((c for c in df.columns if 'sales' in c or 'total' in c), 'total_sales')
console_col = next((c for c in df.columns if 'console' in c or 'platform' in c), 'console')
publisher_col = next((c for c in df.columns if 'pub' in c), 'publisher')

# ----------------------------------------------------------------------------------
# 2. BARRA LATERAL
# ----------------------------------------------------------------------------------
st.sidebar.title("Navegación")
st.sidebar.markdown("---")

SECCIONES_MAP = {
    "Dashboard General": "dashboard",
    "Buscador & Catálogo por Publisher": "search_and_catalog",
    "Títulos Líderes en el Mercado": "market_leaders",
    "Datos": "docs"
}

seccion_seleccionada = st.sidebar.radio("Selecciona la sección:", list(SECCIONES_MAP.keys()))
app_mode = SECCIONES_MAP[seccion_seleccionada]

st.sidebar.markdown("---")
st.sidebar.info(
    "**Autor:** Álvaro Domingo Cordón\n\n"
    "[LinkedIn](https://www.linkedin.com/in/alvaro-domingo) | [GitHub](https://github.com/alvarodc093-pixel)"
)

# ==============================================================================
# 3. EJECUCIÓN DE SECCIONES
# ==============================================================================

if app_mode == "dashboard":
    df_filtered = df.copy()

    st.title("🎮 Video Game Market Analytics")
    st.markdown("""
    ### Qué se vende, dónde y cuándo: 64.000 juegos del histórico de VGChartz
    *Las ventas están en millones de unidades y corresponden sobre todo a copias físicas en consola.*
    """)
    st.markdown("---")

    tabs = st.tabs([
        "Introducción",
        "Catálogo vs ventas",
        "Concentración del mercado",
        "Crítica y regiones",
        "Estacionalidad"
    ])

    # TAB 1: INTRODUCCIÓN Y AUDITORÍA
    with tabs[0]:
        st.markdown("## Contexto de Negocio y Calidad de la Información")
        kpi_a, kpi_b, kpi_c = st.columns(3)
        with kpi_a: st.metric(label="Registros en el CSV", value=f"{df_raw_len:,}")
        with kpi_b: st.metric(label="Registros tras la limpieza", value=f"{len(df):,}", help="Juegos con ventas registradas más los de PC con año conocido")
        with kpi_c:
            st.metric(label="Registros descartados", value=f"{df_raw_len - len(df):,}", help="Sin ventas registradas o sin año de lanzamiento")

        st.markdown("---")
        col_izq, col_der = st.columns([5, 4])
        with col_izq:
            st.markdown("""
            ### El problema
            Las ventas de videojuegos siguen una distribución de cola larga: unos pocos títulos se llevan una parte enorme del total y la mayoría vende poco. Elegir mal el género, la plataforma, la región o la fecha de lanzamiento sale caro.

            ### Preguntas que responde el dashboard
            """)
            st.info("""
            * **1. Catálogo frente a ventas:** qué se publica más y qué vende más.
            * **2. Concentración:** qué consolas, géneros y publishers acumulan más ventas.
            * **3. Regiones:** en qué se diferencian Norteamérica, Europa y Japón.
            * **4. Crítica:** relación entre la nota de la crítica y las ventas.
            * **5. Estacionalidad:** en qué meses salen los superventas.
            """)
        with col_der:
            st.markdown("### Limpieza aplicada")
            with st.expander("Ver detalles", expanded=True):
                st.markdown("""
                * **Ventas:** se descartan los juegos sin ventas registradas, salvo los de `PC`, que se mantienen porque VGChartz no recoge ventas digitales y sin ellos el PC desaparecería del catálogo.
                * **Nulos en género y consola:** se rellenan con `Unknown`.
                * **Año:** se extrae de `release_date`; los registros sin fecha se descartan.
                """)
            st.warning("Alrededor del 70 % de los registros originales no tiene ventas. Las cifras de ventas describen sobre todo el mercado físico de consola hasta ~2018.")

    # TAB 2: VOLUMEN

    with tabs[1]:

        st.header("Distribución del Mercado: Volumen de Producción vs Éxito Real")

        col1, col2,col3 = st.columns(3)
        with col1:
            st.subheader("Volumen de Títulos por Género")
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            order_genres = df_filtered["genre"].value_counts().index if not df_filtered.empty else []
            if len(order_genres) > 0:
                sns.countplot(data=df_filtered, y="genre", order=order_genres, palette="magma", hue="genre", legend=False, ax=ax1)
            st.pyplot(fig1)
        with col2:
            st.subheader("Top 15 Plataformas con Mayor Catálogo")
            if not df_filtered.empty:
                # Solo juegos con ventas, como en el notebook: los miles de juegos de PC sin ventas
                # registradas inflarían su barra y harían el ranking incomparable.
                df_grafico = df_filtered[df_filtered["total_sales"] > 0]

                fig_univ, ax_univ = plt.subplots(figsize=(10, 5))
                order_consoles = df_grafico["console"].value_counts().head(15).index

                sns.countplot(
                    data=df_grafico,
                    x="console",
                    order=order_consoles,
                    palette="crest",
                    hue="console",
                    legend=False,
                    ax=ax_univ
                )

                ax_univ.set_title("Análisis Univariante: Top 15 Plataformas con Mayor Catálogo de Juegos", fontsize=11, fontweight="bold", pad=10)
                ax_univ.set_xlabel("Consola / Plataforma", fontsize=10)
                ax_univ.set_ylabel("Cantidad de Títulos Registrados", fontsize=10)
                ax_univ.tick_params(axis='x', rotation=45)

                st.pyplot(fig_univ)
        with col3:
            st.subheader("Distribución de ventas por juego (escala log)")
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            df_con_ventas = df_filtered[df_filtered["total_sales"] > 0]
            if not df_con_ventas.empty:
                sns.histplot(data=df_con_ventas, x="total_sales", bins=50, log_scale=True, color="purple", ax=ax2)
                ax2.set_xlabel("Ventas por juego (millones de unidades)")
            st.pyplot(fig2)

    # TAB 3: CONCENTRACIÓN
    with tabs[2]:
        st.header("Concentración de ventas: ¿quién se lleva el mercado?")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 10 consolas por unidades vendidas")
            if not df_filtered.empty:
                top_consoles = df_filtered.groupby("console")["total_sales"].sum().sort_values(ascending=False).head(10).reset_index()
                fig3, ax3 = plt.subplots(figsize=(10, 5))
                sns.barplot(data=top_consoles, x="total_sales", y="console", palette="Blues_r", hue="console", legend=False, ax=ax3)
                st.pyplot(fig3)
        with col2:
            st.subheader("Unidades vendidas por género")
            if not df_filtered.empty:
                ventas_genero = df_filtered.groupby("genre")["total_sales"].sum().sort_values(ascending=False).reset_index()
                fig4, ax4 = plt.subplots(figsize=(10, 5))
                sns.barplot(data=ventas_genero, x="total_sales", y="genre", palette="viridis", hue="genre", legend=False, ax=ax4)
                st.pyplot(fig4)
        # --- FILA 2: Heatmap y Distribución Regional (2 columnas) ---
        fila2_col1, fila2_col2 = st.columns(2)

        with fila2_col1:
            st.subheader("Top 10 publishers por género")
            if not df_filtered.empty:
                top_10_publishers = df_filtered.groupby(publisher_col)["total_sales"].sum().nlargest(10).index
                df_top_pub = df_filtered[df_filtered[publisher_col].isin(top_10_publishers)]

                if not df_top_pub.empty:
                    matriz_pub_genre = df_top_pub.pivot_table(index=publisher_col, columns="genre", values="total_sales", aggfunc="sum").fillna(0)
                    matriz_pub_genre = matriz_pub_genre.reindex(top_10_publishers)

                    fig_heatmap, ax_heat = plt.subplots(figsize=(10, 6.5))
                    sns.heatmap(matriz_pub_genre, cmap="YlGnBu", annot=True, fmt=".1f", linewidths=.5, cbar_kws={'label': 'Ventas globales (millones de unidades)'}, ax=ax_heat)
                    ax_heat.set_title("Top 10 publishers: ventas por género", fontsize=11, fontweight="bold", pad=10)
                    ax_heat.set_xlabel("Género del Videojuego", fontsize=9, fontweight="bold")
                    ax_heat.set_ylabel("Publisher / Compañía", fontsize=9, fontweight="bold")
                    ax_heat.tick_params(axis='x', rotation=45, labelsize=9)
                    ax_heat.tick_params(axis='y', labelsize=9)
                    plt.tight_layout()
                    st.pyplot(fig_heatmap)


    # TAB 4: CRÍTICA Y GEOGRAFÍA (Con el gráfico de consumo relativo regional adaptado)
    with tabs[3]:
        st.header("Crítica y regiones")

        st.subheader("1. Nota de la crítica frente a ventas")
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            df_critics = df_filtered[(df_filtered["critic_score"].notnull()) & (df_filtered["critic_score"] > 0) & (df_filtered["total_sales"] > 0)] if not df_filtered.empty else pd.DataFrame()
            if not df_critics.empty:
                fig5, ax5 = plt.subplots(figsize=(10, 4.5))
                sns.scatterplot(data=df_critics, x="critic_score", y="total_sales", alpha=0.4, color="teal", ax=ax5)
                sns.regplot(data=df_critics, x="critic_score", y="total_sales", scatter=False, color="crimson", ax=ax5)
                ax5.set_yscale("log")
                st.pyplot(fig5)
        with col_c2:
            st.markdown("#### Lectura")
            if len(df_critics) > 10:
                rho = df_critics["critic_score"].rank().corr(df_critics["total_sales"].rank())
                altas = df_critics.loc[df_critics["critic_score"] >= 9, "total_sales"].median()
                medias = df_critics.loc[df_critics["critic_score"].between(7, 8), "total_sales"].median()
                st.caption(
                    f"Correlación de Spearman: **{rho:.2f}** ({len(df_critics):,} juegos con nota y ventas). "
                    f"La relación es positiva pero moderada: los juegos con nota ≥ 9 tienen una mediana de "
                    f"**{altas:.2f} M** de unidades frente a **{medias:.2f} M** de los que sacan entre 7 y 8. "
                    "Una buena nota ayuda, pero no explica por sí sola el éxito comercial."
                )

        st.markdown("---")

        st.subheader("2. Ventas por región")
        col_g1, col_g2, col_g3 = st.columns(3)

        with col_g1:
            st.markdown("##### Unidades vendidas por región")
            if not df_filtered.empty:
                regiones = {"Norteamérica (NA)": df_filtered["na_sales"].sum(), "Europa / PAL": df_filtered["pal_sales"].sum(), "Japón (JP)": df_filtered["jp_sales"].sum(), "Otros Mercados": df_filtered["other_sales"].sum()}
                df_regiones = pd.DataFrame(list(regiones.items()), columns=["Region", "Ventas"])
                fig6, ax6 = plt.subplots(figsize=(10, 5.5))
                sns.barplot(data=df_regiones, x="Region", y="Ventas", palette="autumn", hue="Region", legend=False, ax=ax6)
                st.pyplot(fig6)

        with col_g2:
            st.markdown("##### Cuota Relativa de Mercado (Top 10 Consolas)")
            columnas_regiones = ['na_sales', 'pal_sales', 'jp_sales', 'total_sales']
            if all(c in df_filtered.columns for c in columnas_regiones) and 'console' in df_filtered.columns:
                df_platforms = df_filtered.groupby('console')[columnas_regiones].sum()
                top_10_platforms = df_platforms.sort_values(by='total_sales', ascending=False).head(10)

                top_10_porcentual = top_10_platforms[['na_sales', 'pal_sales', 'jp_sales']].copy()
                suma_regiones = top_10_porcentual.sum(axis=1)

                # Evitar división por cero si alguna plataforma del top tiene 0 ventas regionales guardadas
                suma_regiones = suma_regiones.replace(0, 1)
                top_10_porcentual = top_10_porcentual.div(suma_regiones, axis=0) * 100
                top_10_porcentual.columns = ['Norteamérica (NA)', 'Europa / PAL', 'Japón (JP)']

                fig_apilado, ax_apilado = plt.subplots(figsize=(10, 5.5))
                top_10_porcentual.plot(kind='barh', stacked=True, color=['#3182bd', '#9ecae1', '#de2d26'], ax=ax_apilado, edgecolor='white', linewidth=1)
                ax_apilado.set_xlabel("Porcentaje de Ventas (%)", fontsize=9)
                ax_apilado.set_ylabel("")
                ax_apilado.legend(title="Región", loc='lower left', fontsize=8)

                for patch_col in ax_apilado.containers:
                    labels = [f'{val:.0f}%' if val > 8 else '' for val in patch_col.datavalues]
                    ax_apilado.bar_label(patch_col, labels=labels, label_type='center', fontsize=8, fontweight='bold', color='white')
                st.pyplot(fig_apilado)

                if not top_10_porcentual.empty:
                    consola_mas_jp = top_10_porcentual['Japón (JP)'].idxmax()
                    cuota_jp = top_10_porcentual.loc[consola_mas_jp, 'Japón (JP)']
                    xbox = [c for c in top_10_porcentual.index if c.upper() in ("XB", "X360", "XONE", "XS")]
                    texto_xbox = ""
                    if xbox:
                        cuota_na_xbox = top_10_porcentual.loc[xbox, 'Norteamérica (NA)'].mean()
                        texto_xbox = f" Las consolas de Xbox del top venden de media un {cuota_na_xbox:.0f} % en Norteamérica."
                    st.info(f"**{consola_mas_jp.upper()}** es la consola del top 10 con más peso en Japón ({cuota_jp:.0f} % de sus ventas).{texto_xbox}")
        st.markdown("### Análisis Complementario")

        col_g3, col_g4, col_g5 = st.columns(3)

        with col_g3:

            st.markdown("##### Preferencias Regionales por Género")

            if all(col in df_filtered.columns for col in ["genre", "na_sales", "pal_sales", "jp_sales"]):

                df_geo_genre = (
                    df_filtered
                    .groupby("genre")[["na_sales", "pal_sales", "jp_sales"]]
                    .sum()
                )

                df_geo_genre["total_global"] = df_geo_genre.sum(axis=1)

                df_geo_genre = (
                    df_geo_genre
                    .sort_values("total_global", ascending=False)
                    .drop(columns="total_global")
                )

                df_geo_melted = (
                    df_geo_genre
                    .reset_index()
                    .melt(
                        id_vars="genre",
                        var_name="Region",
                        value_name="Sales"
                    )
                )

                mapa_regiones = {
                    "na_sales": "NA",
                    "pal_sales": "PAL",
                    "jp_sales": "JP"
                }

                df_geo_melted["Region"] = (
                    df_geo_melted["Region"]
                    .map(mapa_regiones)
                )

                fig_genre, ax_genre = plt.subplots(figsize=(7, 5))

                sns.barplot(
                    data=df_geo_melted,
                    x="genre",
                    y="Sales",
                    hue="Region",
                    palette=["#3182bd", "#9ecae1", "#de2d26"],
                    ax=ax_genre
                )

                ax_genre.set_xlabel("")
                ax_genre.set_ylabel("Ventas")
                ax_genre.tick_params(axis="x", rotation=45)
                ax_genre.legend(title="")

                plt.tight_layout()

                st.pyplot(fig_genre, width="stretch")

        with col_g4:

            st.markdown("##### Género líder por región")

            genero_jp = (
                df_filtered.groupby("genre")["jp_sales"]
                .sum()
                .idxmax()
            )

            genero_na = (
                df_filtered.groupby("genre")["na_sales"]
                .sum()
                .idxmax()
            )

            genero_pal = (
                df_filtered.groupby("genre")["pal_sales"]
                .sum()
                .idxmax()
            )

            st.metric(
                "Género líder en Japón",
                genero_jp
            )

            st.metric(
                "Género líder en Norteamérica",
                genero_na
            )

            st.metric(
                "Género líder en Europa",
                genero_pal
            )

            st.info(
                f"""
                • Japón: **{genero_jp}**.

                • Norteamérica: **{genero_na}**.

                • Europa: **{genero_pal}**.

                Japón es el mercado que más se separa del resto.
                """
            )
    # TAB 5: ESTACIONALIDAD
    with tabs[4]:
        st.header("Estacionalidad de los lanzamientos")
        df_season = df_filtered[df_filtered["release_date"].notnull() & (df_filtered["total_sales"] > 0)].copy() if not df_filtered.empty else pd.DataFrame()
        if not df_season.empty:
            df_season["month_num"] = df_season["release_date"].dt.month
            meses_es = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
            df_season["month_es"] = df_season["month_num"].map(meses_es)

            st.subheader("1. Ventas y lanzamientos por mes")
            df_monthly = df_season.groupby(["month_num", "month_es"]).agg(total_sales_millions=("total_sales", "sum"), titles_launched=("total_sales", "count"), avg_sales_per_title=("total_sales", "mean")).reset_index().sort_values("month_num")

            fig7, axes_s = plt.subplots(1, 2, figsize=(16, 5))
            sns.barplot(data=df_monthly, x="month_es", y="total_sales_millions", ax=axes_s[0], color="#4a90e2", alpha=0.8)
            axes_s[0].tick_params(axis="x", rotation=45)
            axes_s[0].set(xlabel="", ylabel="Ventas (millones de unidades)", title="Ventas totales (barras) y juegos lanzados (línea)")
            ax0_2 = axes_s[0].twinx()
            sns.lineplot(data=df_monthly, x="month_es", y="titles_launched", ax=ax0_2, color="#d0021b", marker="o")
            ax0_2.set_ylabel("Juegos lanzados", color="#d0021b")
            ax0_2.grid(False)

            sns.barplot(data=df_monthly, x="month_es", y="avg_sales_per_title", ax=axes_s[1], palette="Oranges_r", hue="month_es", legend=False)
            axes_s[1].tick_params(axis="x", rotation=45)
            axes_s[1].set(xlabel="", ylabel="Media por juego (millones de unidades)", title="Ventas medias por juego según el mes")
            plt.tight_layout()
            st.pyplot(fig7)

            st.markdown("---")
            st.subheader("2. Superventas (top 5 % por ventas)")
            df_hits = df_season.copy()
            if not df_hits.empty:
                df_hits["quarter"] = "Q" + df_hits["release_date"].dt.quarter.astype(str)
                umbral_top_5 = df_hits["total_sales"].quantile(0.95)
                df_blockbusters = df_hits[df_hits["total_sales"] >= umbral_top_5]

                col_b1, col_b2 = st.columns(2)
                with col_b1: st.info(f"**Umbral del percentil 95:** más de **{umbral_top_5:.2f} M** de unidades vendidas.")
                with col_b2: st.success(f"**{df_blockbusters.shape[0]} juegos** superan ese umbral.")
                st.markdown("---")
                st.subheader("Los 5 juegos más vendidos del grupo")

                df_control = df_blockbusters.copy()

                if not df_control.empty:

                    if "year" not in df_control.columns:
                        df_control["year"] = df_control["release_date"].dt.year

                    # Ordenar por ventas globales
                    df_control = df_control.sort_values(by="total_sales",ascending=False)
                    columnas_mostrar = ["title","console","year","total_sales","month_es"]

                    columnas_validas = [
                        c for c in columnas_mostrar
                        if c in df_control.columns
                    ]

                    df_elite_top5 = (df_control[columnas_validas].head(5).reset_index(drop=True))

                    df_elite_top5.index = ( df_elite_top5.index + 1)

                    st.dataframe(df_elite_top5,width="stretch")

                    st.caption("Ventas en millones de unidades.")

                else:
                    st.warning("No hay superventas con los filtros actuales.")

                st.markdown("---")
                orden_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                orden_trimestres = ["Q1", "Q2", "Q3", "Q4"]

                fig_hits, axes_hits = plt.subplots(1, 2, figsize=(18, 6))
                sns.countplot(data=df_blockbusters, x="month_es", order=orden_meses, palette="Purples_r", ax=axes_hits[0], hue="month_es", legend=False)
                axes_hits[0].tick_params(axis="x", rotation=40)
                for p in axes_hits[0].patches:
                    height = p.get_height()
                    if height > 0: axes_hits[0].annotate(f'{int(height)}', (p.get_x() + p.get_width() / 2., height + 1), ha='center', va='bottom', fontsize=10, fontweight='bold')

                conteo_q = df_blockbusters["quarter"].value_counts().reindex(orden_trimestres)
                axes_hits[1].pie(conteo_q, labels=conteo_q.index, autopct='%1.1f%%', startangle=90, colors=["#9dc6e0", "#a1dab4", "#feb24c", "#f03b20"], textprops={'fontsize': 12, 'fontweight': 'bold'}, wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                st.pyplot(fig_hits)


# ------------------------------------------------------------------------------
# MODO B: SECCIÓN COMBINADA CON FILTROS INTEGRADOS
# ------------------------------------------------------------------------------
elif app_mode == "search_and_catalog":
    st.title("Explorador de videojuegos")
    st.markdown("---")

    col_filtro_izq, col_filtro_der = st.columns(2)
    with col_filtro_izq:
        min_year, max_year = int(df['year'].min()), int(df['year'].max())
        year_range = st.slider("Rango de Años", min_value=min_year, max_value=max_year, value=(min_year, max_year))
    with col_filtro_der:
        lista_generos = sorted(df['genre'].unique().tolist())
        generos_seleccionados = st.multiselect("Filtrar por Género", options=lista_generos, default=lista_generos)

    df_filtered = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1]) & (df['genre'].isin(generos_seleccionados))]
    tab_buscador, tab_publisher, tab_plataforma = st.tabs(["🔍 Buscador Individual", "🏢 Catálogo por Publisher", "🎮 Catálogo por Consola / PC"])

    with tab_buscador:
        lista_titulos = sorted(df_filtered[title_col].dropna().unique()) if not df_filtered.empty else []
        if len(lista_titulos) > 0:
            titulo_seleccionado = st.selectbox("Seleccione el videojuego:", lista_titulos)
            df_juego = df_filtered[df_filtered[title_col] == titulo_seleccionado]
            if not df_juego.empty:
                juego_data = df_juego.iloc[0]
                col_img, col_metrics = st.columns([1, 2])
                with col_img:
                    path_foto = str(juego_data[img_col]).strip()
                    url_final = f"https://www.vgchartz.com{path_foto}" if path_foto.startswith('/') else "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=400"
                    try: st.image(url_final, width="stretch")
                    except Exception: st.image("https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=400", width="stretch")
                with col_metrics:
                    st.markdown(f"## {juego_data[title_col]}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("🎮 Plataforma", str(juego_data[console_col]).upper())
                    c2.metric("🏢 Editor / Publisher", str(juego_data[publisher_col]))

                    ventas_mostrar = f"{juego_data[sales_col]:.2f} M uds." if juego_data[sales_col] > 0 else "Sin datos"
                    c3.metric("📈 Ventas registradas", ventas_mostrar)

                    with st.expander("🌍 Desglose Geográfico Directo"):
                        r1, r2, r3 = st.columns(3)
                        r1.metric("🇺🇸 NA", f"{juego_data['na_sales']:.2f} M" if ('na_sales' in juego_data and juego_data['na_sales'] > 0) else "N/D")
                        r2.metric("🇪🇺 PAL", f"{juego_data['pal_sales']:.2f} M" if ('pal_sales' in juego_data and juego_data['pal_sales'] > 0) else "N/D")
                        r3.metric("🇯🇵 JP", f"{juego_data['jp_sales']:.2f} M" if ('jp_sales' in juego_data and juego_data['jp_sales'] > 0) else "N/D")
        else:
            st.warning("No hay títulos que coincidan con los criterios de filtrado.")

    with tab_publisher:
        lista_publishers = sorted(df_filtered[publisher_col].dropna().unique()) if (publisher_col in df_filtered.columns and not df_filtered.empty) else []
        if len(lista_publishers) > 0:
            pub_seleccionado = st.selectbox("Selecciona un publisher:", lista_publishers)
            df_pub = df_filtered[df_filtered[publisher_col] == pub_seleccionado].sort_values(by=sales_col, ascending=False)
            if not df_pub.empty:
                st.markdown(f"### Catálogo de {pub_seleccionado}")
                max_mostrar = st.slider("Cantidad de títulos:", min_value=4, max_value=40, value=12, step=4, key="pub_slider")
                grid_cols = st.columns(4)
                for idx, (index, row) in enumerate(df_pub.head(max_mostrar).iterrows()):
                    col_target = idx % 4
                    with grid_cols[col_target]:
                        img_p = str(row[img_col]).strip()
                        url_img = f"https://www.vgchartz.com{img_p}" if img_p.startswith('/') else "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=200"
                        try: st.image(url_img, width="stretch")
                        except Exception: st.image("https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=200", width="stretch")
                        st.markdown(f"**{row[title_col]}**")
                        st.caption(f"🕹️ `{str(row[console_col]).upper()}` | {int(row['year'])}")
                        v_card = f"📈 **{row[sales_col]:.2f} M uds.**" if row[sales_col] > 0 else "*Sin datos de ventas*"
                        st.markdown(v_card)

    with tab_plataforma:
        st.markdown("### Exploración por Consola o PC")
        lista_consolas = sorted(df_filtered[console_col].dropna().unique()) if (console_col in df_filtered.columns and not df_filtered.empty) else []
        if len(lista_consolas) > 0:
            consola_seleccionada = st.selectbox("Selecciona una plataforma:", lista_consolas, key="box_console_tab")
            df_consola = df_filtered[df_filtered[console_col] == consola_seleccionada].sort_values(by=sales_col, ascending=False)
            if not df_consola.empty:
                kpi1, kpi2 = st.columns(2)
                kpi1.metric("Títulos detectados bajo el filtro", f"{len(df_consola)}")
                kpi2.metric("Unidades vendidas registradas", f"{df_consola[sales_col].sum():.2f} M")
                st.markdown("---")
                max_mostrar_c = st.slider("Cantidad de títulos:", min_value=4, max_value=40, value=12, step=4)
                grid_cols_c = st.columns(4)
                for idx, (index, row) in enumerate(df_consola.head(max_mostrar_c).iterrows()):
                    col_target = idx % 4
                    with grid_cols_c[col_target]:
                        img_p = str(row[img_col]).strip()
                        url_img = f"https://www.vgchartz.com{img_p}" if img_p.startswith('/') else "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=200"
                        try: st.image(url_img, width="stretch")
                        except Exception: st.image("https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=200", width="stretch")
                        st.markdown(f"**{row[title_col]}**")
                        st.caption(f"`{row[publisher_col]}` | {int(row['year'])}")
                        v_c_card = f"**{row[sales_col]:.2f} M uds.**" if row[sales_col] > 0 else "*Sin datos de ventas*"
                        st.markdown(v_c_card)

# ------------------------------------------------------------------------------
# MODO C: TÍTULOS LÍDERES
# ------------------------------------------------------------------------------
elif app_mode == "market_leaders":
    df_filtered = df[df[sales_col] > 0].copy()
    st.title("Títulos Líderes en el Mercado")
    if not df_filtered.empty:
        top_n = st.slider("Tamaño del ranking:", min_value=5, max_value=50, value=10, step=5)
        top_games = df_filtered.sort_values(by=sales_col, ascending=False).head(top_n)
        cols_per_row = 5
        for i in range(0, len(top_games), cols_per_row):
            chunk = top_games.iloc[i:i+cols_per_row]
            cols = st.columns(cols_per_row)
            for idx, (index, row) in enumerate(chunk.iterrows()):
                with cols[idx]:
                    st.markdown(f"### #{i + idx + 1}")
                    img_path = str(row[img_col]).strip()
                    url_final = f"https://www.vgchartz.com{img_path}" if img_path.startswith('/') else "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=200"
                    try: st.image(url_final, width="stretch")
                    except Exception: st.image("https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=200", width="stretch")
                    st.markdown(f"**{row[title_col]}**")
                    st.markdown(f"Total: **{row[sales_col]:.2f} M uds.**")

# ------------------------------------------------------------------------------
# MODO D: DOCUMENTACIÓN TÉCNICA
# ------------------------------------------------------------------------------
elif app_mode == "docs":
    st.title("Datos")
    st.markdown(
        "Fuente: **VGChartz 2024** (`Data/vgchartz-2024.csv`). Las ventas están en millones de unidades. "
        "El análisis completo, con la limpieza paso a paso, está en `Notebook/Preprocesamiento.ipynb`."
    )
    st.dataframe(df.head(20), width="stretch")
