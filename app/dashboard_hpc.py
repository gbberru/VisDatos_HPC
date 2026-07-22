# ============================================================
# DASHBOARD HPC - ENERGÍA, TEMPERATURA Y EFICIENCIA OPERATIVA
# Proyecto: Visualización de datos para Data Center HPC
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# 0. COLORES FIJOS
# ============================================================

HARDWARE_COLORS = {
    "CPU-only": "#1f77b4",
    "GPU": "#ff7f0e"
}

HARDWARE_ORDER = ["CPU-only", "GPU"]

MAX_SCATTER_POINTS = 6000
CRITICAL_TEMP_C = 70


# ============================================================
# 1. CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Dashboard HPC",
    page_icon="⚡",
    layout="wide"
)

st.title("Dashboard de Energía, Temperatura y Eficiencia Operativa - Data Center HPC")

st.caption(
    "Análisis interactivo de consumo energético, comportamiento térmico y eficiencia operativa "
    "en servidores de un clúster HPC."
)


# ============================================================
# 2. RUTAS DEL PROYECTO
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

HOURLY_PATH = PROCESSED_DIR / "hourly_node_metrics.parquet"
DETAIL_PATH = PROCESSED_DIR / "job_node_detail.parquet"
SCATTER_PATH = PROCESSED_DIR / "scatter_sample.parquet"


# ============================================================
# 3. CARGA DE DATOS
# ============================================================

@st.cache_data
def load_data():
    hourly = pd.read_parquet(HOURLY_PATH)
    detail = pd.read_parquet(DETAIL_PATH)
    scatter = pd.read_parquet(SCATTER_PATH)

    hourly["hour"] = pd.to_datetime(hourly["hour"])
    detail["start_date"] = pd.to_datetime(detail["start_date"])
    detail["end_date"] = pd.to_datetime(detail["end_date"])
    scatter["start_date"] = pd.to_datetime(scatter["start_date"])
    scatter["end_date"] = pd.to_datetime(scatter["end_date"])

    hourly["rack"] = hourly["rack_inferred"].astype(str)
    detail["rack"] = detail["rack_inferred"].astype(str)
    scatter["rack"] = scatter["rack_inferred"].astype(str)

    hourly["tipo_hardware"] = np.where(hourly["gpu_node"] == 1, "GPU", "CPU-only")
    detail["tipo_hardware"] = np.where(detail["gpu_node"] == 1, "GPU", "CPU-only")
    scatter["tipo_hardware"] = np.where(scatter["gpu_node"] == 1, "GPU", "CPU-only")

    return hourly, detail, scatter


try:
    hourly, detail, scatter = load_data()
except Exception as e:
    st.error("No se pudieron cargar los datasets procesados.")
    st.write("Verifica que existan los archivos dentro de `data/processed/`.")
    st.exception(e)
    st.stop()


# ============================================================
# 4. FILTROS GLOBALES
# ============================================================

st.sidebar.header("Filtros globales")

min_date = hourly["hour"].min().date()
max_date = hourly["hour"].max().date()

date_range = st.sidebar.date_input(
    "Rango temporal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
else:
    start_date = pd.to_datetime(min_date)
    end_date = pd.to_datetime(max_date) + pd.Timedelta(days=1)


rack_options = sorted(
    hourly["rack"].dropna().unique(),
    key=lambda x: int("".join(filter(str.isdigit, str(x))) or 0)
)

selected_racks = st.sidebar.multiselect(
    "Rack",
    options=rack_options,
    default=rack_options
)


hardware_options = HARDWARE_ORDER

selected_hardware = st.sidebar.multiselect(
    "Tipo de hardware",
    options=hardware_options,
    default=hardware_options
)


state_options = sorted(detail["state"].dropna().unique())

selected_states = st.sidebar.multiselect(
    "Estado del job",
    options=state_options,
    default=state_options
)


duration_min = float(detail["job_duration_hours"].min())
duration_max = float(np.ceil(detail["job_duration_hours"].max()))

selected_duration = st.sidebar.slider(
    "Duración del job (horas)",
    min_value=duration_min,
    max_value=duration_max,
    value=(duration_min, duration_max),
    step=1.0
)


if selected_racks:
    node_options = sorted(
        hourly[hourly["rack"].isin(selected_racks)]["node"]
        .dropna()
        .unique()
    )
else:
    node_options = sorted(hourly["node"].dropna().unique())

selected_nodes = st.sidebar.multiselect(
    "Nodo",
    options=node_options,
    default=node_options
)


# ============================================================
# 5. APLICACIÓN DE FILTROS
# ============================================================

hourly_f = hourly[
    (hourly["hour"] >= start_date) &
    (hourly["hour"] < end_date) &
    (hourly["rack"].isin(selected_racks)) &
    (hourly["node"].isin(selected_nodes)) &
    (hourly["tipo_hardware"].isin(selected_hardware)) &
    (hourly["state"].isin(selected_states))
].copy()

detail_f = detail[
    (detail["start_date"] < end_date) &
    (detail["end_date"] >= start_date) &
    (detail["rack"].isin(selected_racks)) &
    (detail["node"].isin(selected_nodes)) &
    (detail["tipo_hardware"].isin(selected_hardware)) &
    (detail["state"].isin(selected_states)) &
    (detail["job_duration_hours"].between(selected_duration[0], selected_duration[1]))
].copy()

scatter_f = scatter[
    (scatter["start_date"] < end_date) &
    (scatter["end_date"] >= start_date) &
    (scatter["rack"].isin(selected_racks)) &
    (scatter["node"].isin(selected_nodes)) &
    (scatter["tipo_hardware"].isin(selected_hardware)) &
    (scatter["state"].isin(selected_states)) &
    (scatter["job_duration_hours"].between(selected_duration[0], selected_duration[1]))
].copy()


if hourly_f.empty or detail_f.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
    st.stop()


# ============================================================
# 6. FUNCIONES AUXILIARES
# ============================================================

def get_agg_func(metric_col):
    if metric_col in ["energy_kwh", "co2_kg"]:
        return "sum"
    if metric_col == "temp_max_c":
        return "max"
    return "mean"


def format_or_no_data(value, unit):
    if pd.isna(value):
        return "Sin datos"
    return f"{value:.2f} {unit}"


def calculate_kpis(hourly_df, detail_df):
    energia_total_mwh = hourly_df["energy_kwh"].sum() / 1000

    node_hour_power = (
        hourly_df.groupby(["hour", "node"], as_index=False)
        .agg(power_mean_kw=("power_mean_kw", "mean"))
    )

    cluster_power_by_hour = (
        node_hour_power.groupby("hour", as_index=False)
        .agg(cluster_power_kw=("power_mean_kw", "sum"))
    )

    potencia_promedio_cluster_kw = cluster_power_by_hour["cluster_power_kw"].mean()

    node_hour_temp = (
        hourly_df.groupby(["hour", "node"], as_index=False)
        .agg(temp_mean_c=("temp_mean_c", "mean"))
    )

    temperatura_promedio_cluster = node_hour_temp["temp_mean_c"].mean()

    co2_total_ton = hourly_df["co2_kg"].sum() / 1000

    estados_criticos = [
        "FAILED",
        "TIMEOUT",
        "CANCELLED",
        "OUT_OF_MEMORY",
        "NODE_FAIL"
    ]

    jobs_criticos = detail_df[
        detail_df["state"].isin(estados_criticos)
    ]["slurm_id"].nunique()

    return (
        energia_total_mwh,
        potencia_promedio_cluster_kw,
        temperatura_promedio_cluster,
        co2_total_ton,
        jobs_criticos
    )


def plot_time_series(hourly_df):
    time_series_total = (
        hourly_df.groupby("hour", as_index=False)
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            cluster_power_kw=("power_mean_kw", "sum"),
            temp_min_c=("temp_mean_c", "min"),
            temp_mean_c=("temp_mean_c", "mean"),
            temp_max_c=("temp_max_c", "max")
        )
    )

    time_series_hw = (
        hourly_df.groupby(["hour", "tipo_hardware"], as_index=False)
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            cluster_power_kw=("power_mean_kw", "sum"),
            temp_min_c=("temp_mean_c", "min"),
            temp_mean_c=("temp_mean_c", "mean"),
            temp_max_c=("temp_max_c", "max")
        )
    )

    hw_wide = time_series_hw.pivot(
        index="hour",
        columns="tipo_hardware",
        values=[
            "energy_kwh",
            "cluster_power_kw",
            "temp_min_c",
            "temp_mean_c",
            "temp_max_c"
        ]
    )

    hw_wide.columns = [
        f"{metric}_{hardware}".replace("-", "_").replace(" ", "_")
        for metric, hardware in hw_wide.columns
    ]

    hw_wide = hw_wide.reset_index()

    time_series = time_series_total.merge(
        hw_wide,
        on="hour",
        how="left"
    )

    required_cols = [
        "energy_kwh_CPU_only",
        "energy_kwh_GPU",
        "cluster_power_kw_CPU_only",
        "cluster_power_kw_GPU",
        "temp_min_c_CPU_only",
        "temp_min_c_GPU",
        "temp_mean_c_CPU_only",
        "temp_mean_c_GPU",
        "temp_max_c_CPU_only",
        "temp_max_c_GPU"
    ]

    for col in required_cols:
        if col not in time_series.columns:
            time_series[col] = np.nan

    time_series["energy_cpu_txt"] = time_series["energy_kwh_CPU_only"].apply(
        lambda x: format_or_no_data(x, "kWh")
    )
    time_series["energy_gpu_txt"] = time_series["energy_kwh_GPU"].apply(
        lambda x: format_or_no_data(x, "kWh")
    )
    time_series["power_cpu_txt"] = time_series["cluster_power_kw_CPU_only"].apply(
        lambda x: format_or_no_data(x, "kW")
    )
    time_series["power_gpu_txt"] = time_series["cluster_power_kw_GPU"].apply(
        lambda x: format_or_no_data(x, "kW")
    )

    time_series["temp_min_cpu_txt"] = time_series["temp_min_c_CPU_only"].apply(
        lambda x: format_or_no_data(x, "°C")
    )
    time_series["temp_min_gpu_txt"] = time_series["temp_min_c_GPU"].apply(
        lambda x: format_or_no_data(x, "°C")
    )
    time_series["temp_mean_cpu_txt"] = time_series["temp_mean_c_CPU_only"].apply(
        lambda x: format_or_no_data(x, "°C")
    )
    time_series["temp_mean_gpu_txt"] = time_series["temp_mean_c_GPU"].apply(
        lambda x: format_or_no_data(x, "°C")
    )
    time_series["temp_max_cpu_txt"] = time_series["temp_max_c_CPU_only"].apply(
        lambda x: format_or_no_data(x, "°C")
    )
    time_series["temp_max_gpu_txt"] = time_series["temp_max_c_GPU"].apply(
        lambda x: format_or_no_data(x, "°C")
    )

    customdata = time_series[
        [
            "energy_cpu_txt",
            "energy_gpu_txt",
            "power_cpu_txt",
            "power_gpu_txt",
            "temp_min_cpu_txt",
            "temp_min_gpu_txt",
            "temp_mean_cpu_txt",
            "temp_mean_gpu_txt",
            "temp_max_cpu_txt",
            "temp_max_gpu_txt"
        ]
    ].to_numpy()

    temp_values = time_series[["temp_min_c", "temp_mean_c", "temp_max_c"]].stack()

    temp_axis_min = min(20, np.floor(temp_values.min() / 5) * 5)
    temp_axis_max = max(75, np.ceil(temp_values.max() / 5) * 5)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        row_heights=[0.58, 0.42],
        subplot_titles=[
            "Energía y potencia",
            "Temperatura del clúster"
        ],
        specs=[
            [{"secondary_y": True}],
            [{"secondary_y": False}]
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=time_series["hour"],
            y=time_series["energy_kwh"],
            mode="lines",
            name="Energía (kWh)",
            line=dict(width=2, color="#2ca02c"),
            customdata=customdata,
            hovertemplate=(
                "<b>Energía:</b> %{y:.2f} kWh<br>"
                "<b>Detalle por hardware:</b><br>"
                "CPU-only: %{customdata[0]}<br>"
                "GPU: %{customdata[1]}"
                "<extra></extra>"
            )
        ),
        row=1,
        col=1,
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=time_series["hour"],
            y=time_series["cluster_power_kw"],
            mode="lines",
            name="Potencia (kW)",
            line=dict(width=2, color="#9467bd"),
            customdata=customdata,
            hovertemplate=(
                "<b>Potencia:</b> %{y:.2f} kW<br>"
                "<b>Detalle por hardware:</b><br>"
                "CPU-only: %{customdata[2]}<br>"
                "GPU: %{customdata[3]}"
                "<extra></extra>"
            )
        ),
        row=1,
        col=1,
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(
            x=time_series["hour"],
            y=time_series["temp_min_c"],
            mode="lines",
            name="Temperatura mínima (°C)",
            line=dict(width=1.8, color="#1f77b4", dash="dot"),
            customdata=customdata,
            hovertemplate=(
                "<b>Temperatura mínima:</b> %{y:.2f} °C<br>"
                "<b>Detalle por hardware:</b><br>"
                "CPU-only: %{customdata[4]}<br>"
                "GPU: %{customdata[5]}"
                "<extra></extra>"
            )
        ),
        row=2,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=time_series["hour"],
            y=time_series["temp_max_c"],
            mode="lines",
            name="Temperatura máxima (°C)",
            line=dict(width=1.8, color="#d62728"),
            fill="tonexty",
            fillcolor="rgba(214, 39, 40, 0.14)",
            customdata=customdata,
            hovertemplate=(
                "<b>Temperatura máxima:</b> %{y:.2f} °C<br>"
                "<b>Detalle por hardware:</b><br>"
                "CPU-only: %{customdata[8]}<br>"
                "GPU: %{customdata[9]}"
                "<extra></extra>"
            )
        ),
        row=2,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=time_series["hour"],
            y=time_series["temp_mean_c"],
            mode="lines",
            name="Temperatura promedio (°C)",
            line=dict(width=2.2, color="#ff7f0e"),
            customdata=customdata,
            hovertemplate=(
                "<b>Temperatura promedio:</b> %{y:.2f} °C<br>"
                "<b>Detalle por hardware:</b><br>"
                "CPU-only: %{customdata[6]}<br>"
                "GPU: %{customdata[7]}"
                "<extra></extra>"
            )
        ),
        row=2,
        col=1
    )

    fig.update_yaxes(
        title_text="Energía (kWh)",
        row=1,
        col=1,
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="Potencia (kW)",
        row=1,
        col=1,
        secondary_y=True
    )

    fig.update_yaxes(
        title_text="Temperatura (°C)",
        range=[temp_axis_min, temp_axis_max],
        tick0=0,
        dtick=5,
        row=2,
        col=1
    )

    fig.update_xaxes(
        title_text="Fecha y hora",
        row=2,
        col=1,
        rangeslider=dict(visible=True),
        type="date"
    )

    fig.update_layout(
        title="Evolución temporal de energía, potencia y temperatura",
        hovermode="x unified",
        height=760,
        margin=dict(l=60, r=60, t=110, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="right",
            x=1
        )
    )

    return fig


def plot_ranking(hourly_df, metric_col, metric_label, group_col, node_ranking_mode="Top 10 real"):
    agg_func = get_agg_func(metric_col)

    if group_col == "rack":
        ranking_total = (
            hourly_df.groupby("rack", as_index=False)
            .agg(total_value=(metric_col, agg_func))
            .sort_values("total_value", ascending=False)
            .head(10)
        )

        top_racks = ranking_total["rack"].tolist()

        ranking_detail = (
            hourly_df[hourly_df["rack"].isin(top_racks)]
            .groupby(["rack", "tipo_hardware"], as_index=False)
            .agg(value=(metric_col, agg_func))
        )

        ranking_detail = ranking_detail.merge(
            ranking_total,
            on="rack",
            how="left"
        )

        ordered_groups = (
            ranking_total.sort_values("total_value", ascending=True)["rack"].tolist()
        )

        bar_mode = "stack" if metric_col in ["energy_kwh", "co2_kg"] else "group"

        fig = px.bar(
            ranking_detail,
            x="value",
            y="rack",
            orientation="h",
            color="tipo_hardware",
            color_discrete_map=HARDWARE_COLORS,
            hover_data={
                "tipo_hardware": True,
                "value": ":.2f",
                "total_value": ":.2f"
            },
            title=f"Top 10 Rack por {metric_label}",
            labels={
                "value": metric_label,
                "total_value": f"Total {metric_label}",
                "rack": "Rack",
                "tipo_hardware": "Tipo de hardware"
            },
            category_orders={
                "tipo_hardware": HARDWARE_ORDER,
                "rack": ordered_groups
            }
        )

        fig.update_layout(
            barmode=bar_mode,
            height=460,
            margin=dict(l=40, r=40, t=70, b=40),
            legend_title_text="Tipo de hardware",
            xaxis_title=metric_label,
            yaxis_title="Rack"
        )

        return fig

    node_base = (
        hourly_df.groupby(["node", "rack", "tipo_hardware"], as_index=False)
        .agg(
            value=(metric_col, agg_func),
            energy_kwh=("energy_kwh", "sum"),
            power_mean_kw=("power_mean_kw", "mean"),
            temp_mean_c=("temp_mean_c", "mean"),
            temp_max_c=("temp_max_c", "max"),
            co2_kg=("co2_kg", "sum"),
            records=("records", "sum")
        )
    )

    if node_ranking_mode == "Comparativo CPU/GPU":
        node_rank = (
            node_base
            .sort_values(["tipo_hardware", "value"], ascending=[True, False])
            .groupby("tipo_hardware", group_keys=False)
            .head(5)
            .copy()
        )
        chart_title = f"Top 5 nodos CPU-only y Top 5 nodos GPU por {metric_label}"
    else:
        node_rank = (
            node_base
            .sort_values("value", ascending=False)
            .head(10)
            .copy()
        )
        chart_title = f"Top 10 Nodo por {metric_label}"

    node_rank["node_label"] = (
        node_rank["node"].astype(str)
        + " | "
        + node_rank["rack"].astype(str)
        + " | "
        + node_rank["tipo_hardware"].astype(str)
    )

    node_rank = node_rank.sort_values("value", ascending=True)

    fig = px.bar(
        node_rank,
        x="value",
        y="node_label",
        orientation="h",
        color="tipo_hardware",
        color_discrete_map=HARDWARE_COLORS,
        text="value",
        hover_data={
            "node": True,
            "rack": True,
            "tipo_hardware": True,
            "value": ":.2f",
            "energy_kwh": ":.2f",
            "power_mean_kw": ":.3f",
            "temp_mean_c": ":.2f",
            "temp_max_c": ":.2f",
            "co2_kg": ":.2f",
            "records": True,
            "node_label": False
        },
        title=chart_title,
        labels={
            "value": metric_label,
            "node_label": "Nodo | Rack | Tipo de hardware",
            "node": "Nodo",
            "rack": "Rack",
            "tipo_hardware": "Tipo de hardware",
            "energy_kwh": "Energía (kWh)",
            "power_mean_kw": "Potencia (kW)",
            "temp_mean_c": "Temperatura promedio (°C)",
            "temp_max_c": "Temperatura máxima (°C)",
            "co2_kg": "CO₂ (kg)",
            "records": "Registros"
        },
        category_orders={
            "tipo_hardware": HARDWARE_ORDER,
            "node_label": node_rank["node_label"].tolist()
        }
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    max_value = node_rank["value"].max()

    fig.update_layout(
        height=520,
        margin=dict(l=40, r=100, t=80, b=40),
        legend_title_text="Tipo de hardware",
        xaxis_title=metric_label,
        yaxis_title="Nodo | Rack | Tipo de hardware",
        xaxis=dict(range=[0, max_value * 1.12 if max_value > 0 else 1])
    )

    return fig


# ============================================================
# FUNCIÓN MODIFICADA:
# HEATMAP RACK/HORA ORDENADO POR CONSUMO O MÉTRICA SELECCIONADA
# Arriba = racks con mayor valor de la métrica seleccionada
# Abajo = racks con menor valor
# ============================================================

def plot_heatmap(hourly_df, metric_col, metric_label):
    heatmap_data = hourly_df.copy()
    heatmap_data["hour_of_day"] = heatmap_data["hour"].dt.hour

    agg_func = get_agg_func(metric_col)

    heatmap_grouped = (
        heatmap_data.groupby(["rack", "hour_of_day"], as_index=False)
        .agg(value=(metric_col, agg_func))
    )

    heatmap_matrix = heatmap_grouped.pivot(
        index="rack",
        columns="hour_of_day",
        values="value"
    )

    heatmap_matrix = heatmap_matrix.reindex(columns=range(24))

    if metric_col in ["energy_kwh", "co2_kg"]:
        heatmap_matrix = heatmap_matrix.fillna(0)

    # Orden del eje Y según la métrica seleccionada.
    # Para energía y CO2 se ordena por suma.
    # Para temperatura máxima se ordena por máximo.
    # Para potencia y temperatura promedio se ordena por promedio.
    if metric_col in ["energy_kwh", "co2_kg"]:
        rack_order = (
            heatmap_matrix.sum(axis=1)
            .sort_values(ascending=False)
            .index
            .tolist()
        )
    elif metric_col == "temp_max_c":
        rack_order = (
            heatmap_matrix.max(axis=1)
            .sort_values(ascending=False)
            .index
            .tolist()
        )
    else:
        rack_order = (
            heatmap_matrix.mean(axis=1)
            .sort_values(ascending=False)
            .index
            .tolist()
        )

    heatmap_matrix = heatmap_matrix.reindex(index=rack_order)

    fig = px.imshow(
        heatmap_matrix,
        labels=dict(
            x="Hora del día",
            y="Rack",
            color=metric_label
        ),
        title=f"Heatmap Rack/Hora - {metric_label}",
        aspect="auto",
        color_continuous_scale="Viridis"
    )

    fig.update_layout(
        height=500,
        margin=dict(l=40, r=40, t=70, b=40)
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(24)),
        ticktext=[f"{h:02d}" for h in range(24)],
        range=[-0.5, 23.5]
    )

    return fig


def plot_hourly_profile(hourly_df):
    df = hourly_df.copy()
    df["hour_of_day"] = df["hour"].dt.hour

    hourly_profile = (
        df.groupby("hour_of_day", as_index=False)
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            power_mean_kw=("power_mean_kw", "mean"),
            temp_mean_c=("temp_mean_c", "mean"),
            temp_max_c=("temp_max_c", "max"),
            records=("records", "sum")
        )
    )

    base_hours = pd.DataFrame({"hour_of_day": list(range(24))})

    hourly_profile = base_hours.merge(
        hourly_profile,
        on="hour_of_day",
        how="left"
    )

    hourly_profile["energy_kwh"] = hourly_profile["energy_kwh"].fillna(0)

    hourly_profile["hour_label"] = hourly_profile["hour_of_day"].apply(
        lambda h: f"{h:02d}:00"
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=hourly_profile["hour_label"],
            y=hourly_profile["energy_kwh"],
            name="Energía (kWh)",
            marker_color="#2ca02c",
            opacity=0.75,
            hovertemplate=(
                "<b>Hora:</b> %{x}<br>"
                "<b>Energía:</b> %{y:.2f} kWh"
                "<extra></extra>"
            )
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=hourly_profile["hour_label"],
            y=hourly_profile["temp_mean_c"],
            mode="lines+markers",
            name="Temperatura promedio (°C)",
            line=dict(color="#d62728", width=2),
            marker=dict(size=6),
            hovertemplate=(
                "<b>Hora:</b> %{x}<br>"
                "<b>Temp. promedio:</b> %{y:.2f} °C"
                "<extra></extra>"
            )
        ),
        secondary_y=True
    )

    fig.add_trace(
        go.Scatter(
            x=hourly_profile["hour_label"],
            y=hourly_profile["temp_max_c"],
            mode="lines+markers",
            name="Temperatura máxima (°C)",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            marker=dict(size=6),
            hovertemplate=(
                "<b>Hora:</b> %{x}<br>"
                "<b>Temp. máxima:</b> %{y:.2f} °C"
                "<extra></extra>"
            )
        ),
        secondary_y=True
    )

    fig.update_layout(
        title=(
            "Perfil horario del clúster: energía y temperatura<br>"
            "<sup>Barras = energía | Líneas = temperatura promedio y máxima</sup>"
        ),
        height=520,
        margin=dict(l=40, r=40, t=90, b=40),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        title_text="Hora del día",
        categoryorder="array",
        categoryarray=[f"{h:02d}:00" for h in range(24)]
    )

    fig.update_yaxes(
        title_text="Energía (kWh)",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="Temperatura (°C)",
        secondary_y=True
    )

    return fig


def plot_scatter_power_temp(scatter_df):
    plot_df = scatter_df.copy()

    if plot_df.empty:
        return None

    if len(plot_df) > MAX_SCATTER_POINTS:
        plot_df = plot_df.sample(MAX_SCATTER_POINTS, random_state=42)

    plot_df["duracion_visual"] = plot_df["job_duration_hours"].clip(
        lower=0.1,
        upper=24
    )

    fig = px.scatter(
        plot_df,
        x="power_mean_kw",
        y="temp_mean_c",
        color="tipo_hardware",
        color_discrete_map=HARDWARE_COLORS,
        category_orders={"tipo_hardware": HARDWARE_ORDER},
        size="duracion_visual",
        symbol="state",
        opacity=0.65,
        hover_data={
            "slurm_id": True,
            "node": True,
            "rack": True,
            "state": True,
            "power_mean_kw": ":.3f",
            "temp_mean_c": ":.2f",
            "temp_max_c": ":.2f",
            "energy_kwh": ":.2f",
            "co2_kg": ":.2f",
            "job_duration_hours": ":.2f",
            "load1_per_core_mean": ":.2f",
            "ram_active_gb_mean": ":.2f",
            "gpu_memory_used_gb_mean": ":.2f",
            "gpu_duty_cycle_mean": ":.2f",
            "duracion_visual": False
        },
        title="Relación entre potencia consumida y temperatura por nodo",
        labels={
            "power_mean_kw": "Potencia (kW)",
            "temp_mean_c": "Temperatura promedio (°C)",
            "tipo_hardware": "Tipo de hardware",
            "state": "Estado del job",
            "rack": "Rack",
            "node": "Nodo",
            "slurm_id": "Job ID"
        }
    )

    fig.update_layout(
        height=620,
        margin=dict(l=40, r=40, t=70, b=40),
        legend_title_text="Tipo de hardware / estado"
    )

    return fig


def plot_ram_relationship(detail_df):
    ram_df = detail_df[
        detail_df["ram_active_gb_mean"].notna()
    ].copy()

    if ram_df.empty:
        return None

    if len(ram_df) > MAX_SCATTER_POINTS:
        ram_df = ram_df.sample(MAX_SCATTER_POINTS, random_state=42)

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            "RAM activa vs temperatura promedio",
            "RAM activa vs energía"
        ],
        horizontal_spacing=0.12
    )

    color_map = HARDWARE_COLORS

    for tipo in HARDWARE_ORDER:
        df_tipo = ram_df[ram_df["tipo_hardware"] == tipo]

        if df_tipo.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=df_tipo["ram_active_gb_mean"],
                y=df_tipo["temp_mean_c"],
                mode="markers",
                name=f"{tipo} - Temp.",
                marker=dict(
                    size=7,
                    color=color_map.get(tipo, "gray"),
                    opacity=0.65,
                    line=dict(width=0.4, color="white")
                ),
                customdata=np.stack(
                    [
                        df_tipo["slurm_id"],
                        df_tipo["node"],
                        df_tipo["rack"],
                        df_tipo["state"],
                        df_tipo["energy_kwh"],
                        df_tipo["power_mean_kw"]
                    ],
                    axis=-1
                ),
                hovertemplate=(
                    "RAM: %{x:.2f} GB<br>"
                    "Temperatura: %{y:.2f} °C<br>"
                    "Job: %{customdata[0]}<br>"
                    "Nodo: %{customdata[1]}<br>"
                    "Rack: %{customdata[2]}<br>"
                    "Estado: %{customdata[3]}<br>"
                    "Energía: %{customdata[4]:.2f} kWh<br>"
                    "Potencia: %{customdata[5]:.3f} kW"
                    "<extra></extra>"
                )
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=df_tipo["ram_active_gb_mean"],
                y=df_tipo["energy_kwh"],
                mode="markers",
                name=f"{tipo} - Energía",
                marker=dict(
                    size=7,
                    color=color_map.get(tipo, "gray"),
                    opacity=0.65,
                    line=dict(width=0.4, color="white")
                ),
                customdata=np.stack(
                    [
                        df_tipo["slurm_id"],
                        df_tipo["node"],
                        df_tipo["rack"],
                        df_tipo["state"],
                        df_tipo["temp_mean_c"],
                        df_tipo["power_mean_kw"]
                    ],
                    axis=-1
                ),
                hovertemplate=(
                    "RAM: %{x:.2f} GB<br>"
                    "Energía: %{y:.2f} kWh<br>"
                    "Job: %{customdata[0]}<br>"
                    "Nodo: %{customdata[1]}<br>"
                    "Rack: %{customdata[2]}<br>"
                    "Estado: %{customdata[3]}<br>"
                    "Temperatura: %{customdata[4]:.2f} °C<br>"
                    "Potencia: %{customdata[5]:.3f} kW"
                    "<extra></extra>"
                )
            ),
            row=1,
            col=2
        )

    fig.update_layout(
        title="Relación entre uso de RAM, temperatura y energía",
        height=620,
        margin=dict(l=40, r=40, t=90, b=40),
        legend_title_text="Tipo de hardware"
    )

    fig.update_xaxes(title_text="RAM activa promedio (GB)", row=1, col=1)
    fig.update_yaxes(title_text="Temperatura promedio (°C)", row=1, col=1)

    fig.update_xaxes(title_text="RAM activa promedio (GB)", row=1, col=2)
    fig.update_yaxes(title_text="Energía (kWh)", row=1, col=2)

    return fig


def plot_state_energy(detail_df):
    state_energy = (
        detail_df.groupby(["state", "tipo_hardware"], as_index=False)
        .agg(energy_kwh=("energy_kwh", "sum"))
    )

    fig = px.bar(
        state_energy,
        x="state",
        y="energy_kwh",
        color="tipo_hardware",
        color_discrete_map=HARDWARE_COLORS,
        category_orders={"tipo_hardware": HARDWARE_ORDER},
        title="Consumo energético por estado de job",
        labels={
            "state": "Estado del job",
            "energy_kwh": "Energía (kWh)",
            "tipo_hardware": "Tipo de hardware"
        }
    )

    fig.update_layout(
        height=480,
        margin=dict(l=40, r=40, t=70, b=40),
        legend_title_text="Tipo de hardware"
    )

    return fig


def plot_node_hour_temperature_peaks(hourly_df, top_nodes=25):
    node_temp = hourly_df.copy()

    if node_temp.empty:
        return None

    node_temp["hour_of_day"] = node_temp["hour"].dt.hour

    node_hour_temp = (
        node_temp
        .groupby(["node", "rack", "tipo_hardware", "hour_of_day"], as_index=False)
        .agg(
            temp_max_c=("temp_max_c", "max"),
            temp_mean_c=("temp_mean_c", "mean"),
            power_mean_kw=("power_mean_kw", "mean"),
            energy_kwh=("energy_kwh", "sum"),
            records=("records", "sum")
        )
    )

    node_stats = (
        node_hour_temp
        .groupby(["node", "rack", "tipo_hardware"], as_index=False)
        .agg(
            temp_max_global=("temp_max_c", "max"),
            temp_mean_global=("temp_mean_c", "mean"),
            energy_total_kwh=("energy_kwh", "sum"),
            power_mean_kw=("power_mean_kw", "mean"),
            records=("records", "sum")
        )
        .sort_values(
            ["temp_max_global", "temp_mean_global", "energy_total_kwh", "node"],
            ascending=[False, False, False, True]
        )
        .head(top_nodes)
    )

    node_stats["node_label"] = (
        node_stats["node"].astype(str)
        + " | máx. "
        + node_stats["temp_max_global"].round(1).astype(str)
        + " °C"
    )

    node_hour_top = node_hour_temp.merge(
        node_stats[["node", "temp_max_global", "temp_mean_global", "node_label"]],
        on="node",
        how="inner"
    )

    display_order = (
        node_stats
        .sort_values(
            ["temp_max_global", "temp_mean_global", "energy_total_kwh", "node"],
            ascending=[True, True, True, False]
        )
    )

    node_order = display_order["node_label"].tolist()

    temp_matrix = node_hour_top.pivot(
        index="node_label",
        columns="hour_of_day",
        values="temp_max_c"
    )

    temp_matrix = temp_matrix.reindex(index=node_order)
    temp_matrix = temp_matrix.reindex(columns=range(24))

    if np.isnan(temp_matrix.values).all():
        return None

    temp_min_visual = np.nanmin(temp_matrix.values)
    temp_matrix_visual = temp_matrix.fillna(temp_min_visual)

    critical_points = node_hour_top[
        node_hour_top["temp_max_c"] >= CRITICAL_TEMP_C
    ].copy()

    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            z=temp_matrix_visual.values,
            x=temp_matrix_visual.columns,
            y=temp_matrix_visual.index,
            colorscale="Inferno",
            colorbar=dict(title="Temp. máx. °C"),
            hovertemplate=(
                "Nodo: %{y}<br>"
                "Hora del día: %{x}:00<br>"
                "Temp. máxima registrada: %{z:.2f} °C"
                "<extra></extra>"
            )
        )
    )

    if not critical_points.empty:
        critical_points["node_label"] = (
            critical_points["node"].map(
                node_stats.set_index("node")["node_label"]
            )
        )

        fig.add_trace(
            go.Scatter(
                x=critical_points["hour_of_day"],
                y=critical_points["node_label"],
                mode="markers",
                name=f"Temperatura crítica ≥ {CRITICAL_TEMP_C} °C",
                marker=dict(
                    size=16,
                    color="rgba(0,0,0,0)",
                    line=dict(color="#00FFFF", width=2.5),
                    symbol="circle"
                ),
                customdata=np.stack(
                    [
                        critical_points["node"],
                        critical_points["rack"],
                        critical_points["tipo_hardware"],
                        critical_points["temp_max_c"],
                        critical_points["temp_mean_c"],
                        critical_points["power_mean_kw"],
                        critical_points["energy_kwh"]
                    ],
                    axis=-1
                ),
                hovertemplate=(
                    "<b>Temperatura crítica</b><br>"
                    "Nodo: %{customdata[0]}<br>"
                    "Hora: %{x}:00<br>"
                    "Rack: %{customdata[1]}<br>"
                    "Tipo hardware: %{customdata[2]}<br>"
                    "Temp. máxima registrada: %{customdata[3]:.2f} °C<br>"
                    "Temp. promedio: %{customdata[4]:.2f} °C<br>"
                    "Potencia: %{customdata[5]:.3f} kW<br>"
                    "Energía: %{customdata[6]:.2f} kWh"
                    "<extra></extra>"
                )
            )
        )

    fig.update_layout(
        title=(
            "Top nodos por temperatura máxima registrada<br>"
            f"<sup>Arriba = mayor criticidad térmica | "
            f"Círculos = temperatura crítica ≥ {CRITICAL_TEMP_C} °C</sup>"
        ),
        xaxis_title="Hora del día",
        yaxis_title="Nodo | temperatura máxima global",
        height=820,
        margin=dict(l=40, r=40, t=100, b=40),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(24)),
        ticktext=[f"{h:02d}" for h in range(24)],
        range=[-0.5, 23.5]
    )

    return fig


# ============================================================
# 7. KPIs
# ============================================================

(
    energia_total_mwh,
    potencia_promedio_cluster_kw,
    temperatura_promedio_cluster,
    co2_total_ton,
    jobs_criticos
) = calculate_kpis(hourly_f, detail_f)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("Energía", f"{energia_total_mwh:,.2f} MWh")
kpi2.metric("Potencia prom. clúster", f"{potencia_promedio_cluster_kw:,.2f} kW")
kpi3.metric("Temp. promedio", f"{temperatura_promedio_cluster:,.2f} °C")
kpi4.metric("CO₂", f"{co2_total_ton:,.2f} t")
kpi5.metric("Jobs críticos", f"{jobs_criticos:,}")


# ============================================================
# 8. PESTAÑAS DEL DASHBOARD
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Vista general",
    "Patrones térmicos y horarios",
    "Relación entre variables",
    "Detalle operativo"
])


metric_options = {
    "Energía (kWh)": "energy_kwh",
    "Potencia (kW)": "power_mean_kw",
    "Temperatura promedio (°C)": "temp_mean_c",
    "Temperatura máxima (°C)": "temp_max_c",
    "CO₂ (kg)": "co2_kg"
}


# ============================================================
# TAB 1: VISTA GENERAL
# ============================================================

with tab1:
    st.subheader("Vista general del clúster")

    st.markdown(
        "Esta sección resume el comportamiento general del clúster. "
        "La serie temporal permite observar tendencias, variaciones y picos. "
        "El control inferior de la gráfica funciona como **range slider temporal**."
    )

    st.plotly_chart(
        plot_time_series(hourly_f),
        use_container_width=True
    )

    col1, col2 = st.columns(2)

    with col1:
        selected_metric_label = st.selectbox(
            "Métrica para ranking",
            options=list(metric_options.keys()),
            index=0
        )

    with col2:
        selected_group_label = st.selectbox(
            "Nivel de comparación",
            options=["Rack", "Nodo"],
            index=0
        )

    selected_group = "rack" if selected_group_label == "Rack" else "node"

    node_ranking_mode = "Top 10 real"

    if selected_group == "node":
        node_ranking_mode = st.selectbox(
            "Modo de ranking de nodos",
            options=["Top 10 real", "Comparativo CPU/GPU"],
            index=0,
            help=(
                "Top 10 real muestra los nodos con mayor valor sin forzar tipos de hardware. "
                "Comparativo CPU/GPU muestra nodos destacados de ambos tipos para facilitar comparación."
            )
        )

    st.plotly_chart(
        plot_ranking(
            hourly_f,
            metric_options[selected_metric_label],
            selected_metric_label,
            selected_group,
            node_ranking_mode=node_ranking_mode
        ),
        use_container_width=True
    )

    if selected_group == "node" and node_ranking_mode == "Top 10 real":
        st.info(
            "Si el Top 10 real muestra solo CPU-only o solo GPU, no es un error: "
            "significa que, con los filtros actuales, esos nodos concentran los valores más altos. "
            "Usa el modo 'Comparativo CPU/GPU' si deseas ver ambos tipos de hardware en la misma vista."
        )


# ============================================================
# TAB 2: PATRONES TÉRMICOS Y HORARIOS
# ============================================================

with tab2:
    st.subheader("Patrones por rack, nodo y hora del día")

    st.markdown(
        "Esta sección permite identificar horarios, racks y nodos con mayor consumo "
        "o temperatura elevada. El selector de métrica permite cambiar el enfoque del análisis."
    )

    heatmap_metric_label = st.selectbox(
        "Métrica para heatmap Rack/Hora",
        options=list(metric_options.keys()),
        index=0
    )

    st.plotly_chart(
        plot_heatmap(
            hourly_f,
            metric_options[heatmap_metric_label],
            heatmap_metric_label
        ),
        use_container_width=True
    )

    st.markdown("### Perfil horario de energía y temperatura")

    st.markdown(
        "Este gráfico resume el comportamiento del clúster por hora del día. "
        "Permite identificar horarios donde coinciden mayor consumo energético, "
        "temperatura promedio elevada o picos de temperatura máxima."
    )

    st.plotly_chart(
        plot_hourly_profile(hourly_f),
        use_container_width=True
    )

    st.markdown("### Top nodos por temperatura máxima registrada")

    st.markdown(
        "Este gráfico permite identificar los nodos con mayor criticidad térmica. "
        "Cada fila representa un nodo y cada columna una hora del día. "
        f"El color representa la temperatura máxima registrada y los círculos resaltan "
        f"temperaturas críticas iguales o superiores a {CRITICAL_TEMP_C} °C."
    )

    top_nodes_temp = st.slider(
        "Cantidad de nodos más calientes a mostrar",
        min_value=10,
        max_value=40,
        value=25,
        step=5
    )

    fig_node_peaks = plot_node_hour_temperature_peaks(
        hourly_f,
        top_nodes=top_nodes_temp
    )

    if fig_node_peaks is not None:
        st.plotly_chart(fig_node_peaks, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para generar el heatmap de nodos.")


# ============================================================
# TAB 3: RELACIÓN ENTRE VARIABLES
# ============================================================

with tab3:
    st.subheader("Relaciones multivariables")

    st.markdown(
        "Esta sección permite explorar asociaciones entre potencia, temperatura, RAM, energía "
        "y tipo de hardware. Los tooltips muestran detalle bajo demanda por job, nodo y rack."
    )

    fig_scatter = plot_scatter_power_temp(scatter_f)

    if fig_scatter is not None:
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para el scatterplot con los filtros seleccionados.")

    fig_ram = plot_ram_relationship(detail_f)

    if fig_ram is not None:
        st.plotly_chart(fig_ram, use_container_width=True)
    else:
        st.warning("No hay datos suficientes para analizar RAM, temperatura y energía.")


# ============================================================
# TAB 4: DETALLE OPERATIVO
# ============================================================

with tab4:
    st.subheader("Detalle operativo por job, nodo y estado")

    st.markdown(
        "Esta sección permite revisar estados de job, consumo asociado y registros específicos. "
        "Funciona como nivel final del drill-down: de rack a nodo y de nodo a job."
    )

    st.plotly_chart(
        plot_state_energy(detail_f),
        use_container_width=True
    )

    st.markdown("### Tabla de detalle filtrada")

    cols_table = [
        "slurm_id",
        "node",
        "rack",
        "tipo_hardware",
        "gpu_model",
        "gpu_count",
        "state",
        "job_duration_hours",
        "power_mean_kw",
        "energy_kwh",
        "temp_mean_c",
        "temp_max_c",
        "co2_kg",
        "load1_per_core_mean",
        "ram_active_gb_mean",
        "gpu_memory_used_gb_mean",
        "gpu_duty_cycle_mean",
        "numcores",
        "numnodes"
    ]

    detail_table = (
        detail_f[cols_table]
        .sort_values("energy_kwh", ascending=False)
        .reset_index(drop=True)
    )

    detail_table = detail_table.rename(columns={
        "slurm_id": "Job ID",
        "node": "Nodo",
        "rack": "Rack",
        "tipo_hardware": "Tipo de hardware",
        "gpu_model": "Modelo GPU",
        "gpu_count": "Cantidad GPU",
        "state": "Estado",
        "job_duration_hours": "Duración job (h)",
        "power_mean_kw": "Potencia (kW)",
        "energy_kwh": "Energía (kWh)",
        "temp_mean_c": "Temp. prom. (°C)",
        "temp_max_c": "Temp. máx. (°C)",
        "co2_kg": "CO₂ (kg)",
        "load1_per_core_mean": "Carga CPU/core",
        "ram_active_gb_mean": "RAM activa (GB)",
        "gpu_memory_used_gb_mean": "Memoria GPU (GB)",
        "gpu_duty_cycle_mean": "Uso GPU (%)",
        "numcores": "Cores",
        "numnodes": "Nodos job"
    })

    st.dataframe(
        detail_table,
        use_container_width=True,
        height=500
    )