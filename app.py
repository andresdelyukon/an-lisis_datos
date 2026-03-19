import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# --- Funciones ---

def preparar_kleenbebe(df, multiplicar=1):
    df = df[df['Marca'] == 'KLEENBEBE'].copy()
    df['Sell Out Ventas Valor'] = (
        df['Sell Out Ventas Valor']
        .str.replace(',', '')
        .str.replace(' ', '')
        .str.replace('-', '')
        .astype(float)
    ) * multiplicar
    df['Fecha cierre de semana'] = pd.to_datetime(df['Fecha cierre de semana'])
    return df[df['Sell Out Ventas Valor'] >= 0].copy()

def agrupar_sumar(df, valor_columna, *columnas_agrupacion):
    return df.groupby(list(columnas_agrupacion))[valor_columna].sum().reset_index()


# --- Carga de datos (cacheada para no recargar en cada interacción) ---

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/Base_panal_cadena_semana_codigo_2022_2025 vf(Base de datos) - Base_panal_cadena_semana_codigo_2022_2025 vf(Base de datos).csv")
    df_nuevo = preparar_kleenbebe(df)

    df_antiguo = pd.read_csv('data/pañalitos_sin_espacios.csv')
    df_antiguo = df_antiguo.rename(columns={' Sell Out Ventas Valor': 'Sell Out Ventas Valor'})
    df_antiguo = preparar_kleenbebe(df_antiguo, multiplicar=1000)

    return df_nuevo, df_antiguo


df_kleenbebe_positivos, df_kleenbebe_positivos_antiguo = cargar_datos()

canales_por_dia = agrupar_sumar(df_kleenbebe_positivos, 'Sell Out Ventas Valor', 'Fecha cierre de semana', 'Canal')
canales_por_cadena_por_dia = agrupar_sumar(df_kleenbebe_positivos, 'Sell Out Ventas Valor', 'Fecha cierre de semana', 'Canal', 'Cadena')
canales_por_cadena_por_dia_por_producto = agrupar_sumar(df_kleenbebe_positivos, 'Sell Out Ventas Valor', 'Fecha cierre de semana', 'Canal', 'Descripción')
canales_por_dia_2 = agrupar_sumar(df_kleenbebe_positivos_antiguo, 'Sell Out Ventas Valor', 'Fecha cierre de semana', 'Canal')

dfs_por_canal = {canal: grupo.copy() for canal, grupo in canales_por_cadena_por_dia.groupby('Canal')}
dfs_por_canal_producto = {canal: grupo.copy() for canal, grupo in canales_por_cadena_por_dia_por_producto.groupby('Canal')}


# --- App ---

st.title('Ventas KLEENBEBE')

seccion = st.sidebar.radio('Sección', [
    'Ventas por cadena',
    'Participación por cadena',
    'Participación por producto',
    'Comparación datos históricos',
    'Tabla semestral',
])

canal_seleccionado = st.sidebar.selectbox('Canal', sorted(dfs_por_canal.keys()))


# --- Ventas por cadena ---

if seccion == 'Ventas por cadena':
    st.header(f'Ventas por Cadena - {canal_seleccionado}')
    df_canal = dfs_por_canal[canal_seleccionado]

    fig, ax = plt.subplots(figsize=(12, 6))
    for cadena, grupo in df_canal.groupby('Cadena'):
        ax.plot(grupo['Fecha cierre de semana'], grupo['Sell Out Ventas Valor'], label=cadena)
    ax.legend()
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Ventas ($)')
    ax.set_title(f'Ventas por Cadena - {canal_seleccionado}')
    plt.tight_layout()
    st.pyplot(fig)


# --- Participación por cadena ---

elif seccion == 'Participación por cadena':
    st.header(f'Participación por Cadena - {canal_seleccionado}')
    df_canal = dfs_por_canal[canal_seleccionado]
    ventas_cadena = df_canal.groupby('Cadena')['Sell Out Ventas Valor'].sum()
    ventas_cadena_pct = (ventas_cadena / ventas_cadena.sum() * 100).sort_values()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(ventas_cadena_pct.index, ventas_cadena_pct.values)
    for bar, pct in zip(bars, ventas_cadena_pct.values):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f' {pct:.1f}%', va='center')
    ax.set_xlabel('% de Ventas')
    ax.set_title(f'Participación por Cadena - {canal_seleccionado}')
    plt.tight_layout()
    st.pyplot(fig)


# --- Participación por producto ---

elif seccion == 'Participación por producto':
    st.header(f'Participación por Producto - {canal_seleccionado}')
    df_canal = dfs_por_canal_producto[canal_seleccionado]
    ventas_producto = df_canal.groupby('Descripción')['Sell Out Ventas Valor'].sum()
    ventas_producto_pct = (ventas_producto / ventas_producto.sum() * 100).sort_values()

    if canal_seleccionado in ['MAYOREO', 'AUTOSERVICIO']:
        ventas_producto_pct = ventas_producto_pct[ventas_producto_pct >= 1]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(ventas_producto_pct.index, ventas_producto_pct.values)
    for bar, pct in zip(bars, ventas_producto_pct.values):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f' {pct:.1f}%', va='center')
    ax.set_xlabel('% de Ventas')
    ax.set_title(f'Participación por Producto - {canal_seleccionado}')
    plt.tight_layout()
    st.pyplot(fig)


# --- Comparación histórica ---

elif seccion == 'Comparación datos históricos':
    st.header('Datos nuevos vs históricos (fechas coincidentes)')

    fechas_comunes = set(canales_por_dia['Fecha cierre de semana']) & set(canales_por_dia_2['Fecha cierre de semana'])
    df1_filtrado = canales_por_dia[canales_por_dia['Fecha cierre de semana'].isin(fechas_comunes)]
    df2_filtrado = canales_por_dia_2[canales_por_dia_2['Fecha cierre de semana'].isin(fechas_comunes)]

    fig, ax = plt.subplots(figsize=(12, 6))
    for canal, grupo in df1_filtrado.groupby('Canal'):
        ax.plot(grupo['Fecha cierre de semana'], grupo['Sell Out Ventas Valor'], label=canal)
    for canal, grupo in df2_filtrado.groupby('Canal'):
        ax.plot(grupo['Fecha cierre de semana'], grupo['Sell Out Ventas Valor'], label=f'{canal} (antiguo)', linestyle='--')
    ax.legend()
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Ventas ($)')
    ax.set_title('Ventas por Canal - KLEENBEBE')
    plt.tight_layout()
    st.pyplot(fig)


# --- Tabla semestral ---

elif seccion == 'Tabla semestral':
    st.header('Tabla Semestral por Canal')

    canales_por_dia['Semestre'] = (
        canales_por_dia['Fecha cierre de semana'].dt.year.astype(str) + '-S' +
        canales_por_dia['Fecha cierre de semana'].dt.month.apply(lambda m: '1' if m <= 6 else '2')
    )
    tabla_semestral = canales_por_dia.groupby(['Semestre', 'Canal'])['Sell Out Ventas Valor'].sum().unstack(fill_value=0)
    st.dataframe((tabla_semestral / 1_000_000).round(1).style.format('{:.1f}M'))
