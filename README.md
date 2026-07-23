Visualización de datos para el análisis del consumo energético, temperatura y eficiencia operativa en servidores de un Data Center HPC
1. Descripción del proyecto
Este proyecto desarrolla un dashboard interactivo para analizar el consumo energético, la temperatura y la eficiencia operativa de servidores en un Data Center HPC.
El análisis se basa en métricas temporales de nodos CPU/GPU y registros de jobs ejecutados en el clúster. El objetivo es identificar patrones de consumo, picos térmicos, diferencias entre nodos con y sin GPU, y posibles ineficiencias operativas asociadas al uso de recursos computacionales.
El dashboard permite responder preguntas como:
¿Cómo evoluciona la energía, potencia y temperatura del clúster en el tiempo?
¿Qué racks o nodos concentran mayor consumo o temperatura?
¿Qué horarios presentan patrones recurrentes de consumo o picos térmicos?
¿Qué relación existe entre potencia, temperatura, RAM y energía?
¿Qué estados de job concentran energía productiva o potencialmente no productiva?
---
2. Fuente de datos
Los datos provienen del dataset público Generic and ML Workloads in an HPC Datacenter, disponible en Zenodo:
https://zenodo.org/records/11028934
Archivos originales utilizados:
Archivo	Descripción
`prom_slurm_joined.zip`	Dataset principal con métricas temporales de monitoreo unidas con información de jobs SLURM.
`node_hardware_info.parquet`	Información de hardware de los nodos del clúster.
`slurm_table_cleaned.parquet`	Información limpia de los jobs ejecutados en el Data Center HPC.
> **Nota:** Por tamaño, el dataset original completo no se incluye necesariamente en el repositorio. Para reproducir el proyecto desde cero, se deben descargar los archivos originales desde Zenodo y ubicarlos en la carpeta indicada en la sección de reproducción.
---
3. Estructura del repositorio
```text
VisDatos_HPC/
│
├── app/
│   └── dashboard_hpc.py
│
├── data/
│   ├── raw/
│   │   └── datacenter_enriched_core_single.parquet  # Dataset base procesado / o archivo generado localmente
│   │
│   └── processed/
│       ├── heatmap_rack_hour.parquet
│       ├── hourly_node_metrics.parquet
│       ├── job_node_detail.parquet
│       ├── ranking_rack_node.parquet
│       ├── scatter_sample.parquet
│       └── state_summary.parquet
│
├── Transform_data/
│   ├── Transform_data.ipynb
│   ├── Revison_data.ipynb
│   ├── Prepare_dashboard_data.ipynb
│   └── Visual_tests.ipynb
│
├── .gitignore
├── README.md
└── requirements.txt
```
Descripción de carpetas
Carpeta / archivo	Descripción
`app/dashboard_hpc.py`	Aplicación principal del dashboard en Streamlit.
`data/raw/`	Carpeta para almacenar el dataset base utilizado para generar los archivos del dashboard.
`data/processed/`	Archivos Parquet agregados y optimizados para la visualización.
`Transform_data/`	Notebooks usados para transformación, revisión, preparación y pruebas visuales.
`requirements.txt`	Dependencias necesarias para ejecutar el proyecto.
`README.md`	Documentación del proyecto y pasos de reproducción.
---
4. Proceso realizado para obtener el dataset final
El procesamiento de datos se realizó principalmente en el notebook `Transform_data.ipynb`.
De forma resumida, el proceso consistió en:
Descargar los archivos originales desde Zenodo.
Descomprimir `prom_slurm_joined.zip`.
Leer los archivos `.parquet` del dataset principal.
Seleccionar las columnas relevantes para consumo energético, temperatura, uso de recursos y jobs SLURM.
Integrar información de hardware desde `node_hardware_info.parquet`.
Crear variables derivadas para facilitar el análisis visual.
Convertir unidades técnicas a formatos interpretables: bytes a GB, miliwatts a watts, joules a kWh y segundos a horas.
Generar un dataset final reducido y enriquecido en formato Parquet.
Preparar archivos agregados para mejorar el rendimiento del dashboard.
---
5. Dataset final utilizado
Característica	Valor
Filas	11.930.727
Columnas	53
Tamaño aproximado en disco	716 MB
Formato	Parquet
Rango temporal	2022-06-30 a 2022-11-01
El dataset final contiene información temporal por nodo, métricas de energía, potencia, temperatura, RAM, GPU, red, disco y datos de jobs SLURM.
---
6. Archivos procesados para el dashboard
Para que el dashboard funcione de forma fluida, se generaron archivos agregados en `data/processed/`:
Archivo	Uso en el dashboard
`hourly_node_metrics.parquet`	Series temporales, KPIs, heatmaps por rack/hora y análisis térmico por nodo.
`job_node_detail.parquet`	Tabla de detalle operativo por job, nodo, rack y estado.
`scatter_sample.parquet`	Muestra optimizada para gráficas de dispersión y relaciones entre variables.
`heatmap_rack_hour.parquet`	Archivo auxiliar para patrones por rack y hora.
`ranking_rack_node.parquet`	Archivo auxiliar para rankings por rack o nodo.
`state_summary.parquet`	Resumen por estado de job.
---
7. Columnas principales del dataset final
Columna	Significado	Unidad / tipo
`timestamp`	Fecha y hora de la medición.	Fecha/hora
`node`	Nombre del nodo físico del clúster.	Categórico
`rack_inferred`	Rack inferido a partir del nombre del nodo.	Categórico
`gpu_node`	Indica si el nodo tiene GPU.	0 = No, 1 = Sí
`gpu_model`	Modelo de GPU del nodo.	Categórico
`gpu_count`	Cantidad de GPU disponibles en el nodo.	Número
`node_power_usage`	Potencia registrada del nodo.	Watts
`node_rapl_package_power_sum`	Potencia estimada del paquete CPU mediante RAPL.	Watts
`cpu_package_energy_kwh`	Energía CPU convertida a kWh.	kWh
`ram_active_gb`	Memoria RAM activa convertida a GB.	GB
`ram_free_gb`	Memoria RAM libre convertida a GB.	GB
`node_hwmon_temp_celsius_mean`	Temperatura promedio de sensores hardware del nodo.	°C
`node_hwmon_temp_celsius_max`	Temperatura máxima de sensores hardware del nodo.	°C
`gpu_memory_used_gb`	Memoria GPU utilizada convertida a GB.	GB
`gpu_power_watts_mean`	Potencia promedio de GPU convertida a watts.	Watts
`gpu_power_watts_max`	Potencia máxima de GPU convertida a watts.	Watts
`gpu_energy_kwh_est`	Energía estimada consumida por GPU.	kWh
`co2_kg_est`	Emisiones estimadas de CO₂ calculadas desde la energía.	kg CO₂
`slurm_id`	Identificador del job SLURM.	ID
`start_date`	Fecha y hora de inicio del job.	Fecha/hora
`end_date`	Fecha y hora de finalización del job.	Fecha/hora
`job_duration_hours`	Duración del job.	Horas
`state`	Estado final del job.	Categórico
`numnodes`	Número de nodos utilizados por el job.	Cantidad
`numcores`	Número de cores utilizados por el job.	Cantidad
---
8. Dashboard desarrollado
El dashboard fue construido con Streamlit y Plotly. Está organizado en cuatro pestañas principales:
8.1 Vista general
Permite analizar el comportamiento global del clúster mediante:
KPIs de energía, potencia, temperatura, CO₂ y jobs críticos.
Serie temporal de energía, potencia y temperatura.
Ranking por rack o nodo según la métrica seleccionada.
8.2 Patrones térmicos y horarios
Permite identificar patrones por hora del día, rack y nodo mediante:
Heatmap Rack/Hora para energía, potencia, temperatura o CO₂.
Perfil horario de energía y temperatura.
Heatmap de top nodos por temperatura máxima registrada.
8.3 Relación entre variables
Permite explorar asociaciones entre variables mediante:
Relación entre potencia promedio y temperatura promedio.
RAM activa vs temperatura promedio.
RAM activa vs energía.
8.4 Detalle operativo
Permite revisar el comportamiento operativo por job mediante:
Energía acumulada por estado del job.
Diagrama Sankey de flujo de energía: tipo de hardware → estado del job → resultado operativo.
Tabla de detalle filtrada por job, nodo, rack, estado y recursos utilizados.
---
9. Cómo reproducir el proyecto
9.1 Clonar el repositorio
```bash
git clone https://github.com/gbberru/VisDatos_HPC.git
cd VisDatos_HPC
```
9.2 Crear entorno virtual
En Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
En Linux / macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```
9.3 Instalar dependencias
```bash
pip install -r requirements.txt
```
9.4 Obtener los datos
Descargar desde Zenodo los archivos originales:
`prom_slurm_joined.zip`
`node_hardware_info.parquet`
`slurm_table_cleaned.parquet`
Ubicarlos localmente en la ruta usada por los notebooks de transformación. Si se desea ejecutar directamente el dashboard, debe existir la carpeta:
```text
data/processed/
```
con los archivos Parquet procesados:
```text
heatmap_rack_hour.parquet
hourly_node_metrics.parquet
job_node_detail.parquet
ranking_rack_node.parquet
scatter_sample.parquet
state_summary.parquet
```
9.5 Ejecutar notebooks de preparación
Ejecutar en este orden:
`Transform_data/Transform_data.ipynb`
`Transform_data/Revison_data.ipynb`
`Transform_data/Prepare_dashboard_data.ipynb`
`Transform_data/Visual_tests.ipynb` (opcional, usado para pruebas de visualización)
9.6 Ejecutar el dashboard
```bash
streamlit run app/dashboard_hpc.py
```
Luego abrir en el navegador la URL local generada por Streamlit, usualmente:
```text
http://localhost:8501
```
---
10. Interpretación de métricas principales
Métrica	Interpretación
Energía (kWh)	Energía acumulada en el periodo analizado.
Potencia (kW)	Potencia promedio registrada en las agregaciones del dashboard.
Temperatura promedio (°C)	Temperatura media del nodo o clúster según el nivel de análisis.
Temperatura máxima (°C)	Pico térmico máximo registrado.
CO₂ (kg o t)	Emisión estimada a partir de la energía consumida.
Jobs críticos	Jobs con estados no exitosos como `FAILED`, `TIMEOUT`, `CANCELLED`, `OUT_OF_MEMORY` o `NODE_FAIL`.
---
11. Limitaciones del análisis
La energía y el CO₂ se calculan a partir de métricas disponibles y factores de estimación, por lo que deben interpretarse como valores aproximados.
La temperatura depende del tipo de sensor disponible y puede variar entre nodos CPU-only y GPU.
El análisis visual permite identificar patrones y posibles relaciones, pero no reemplaza una evaluación estadística formal de causalidad.
Algunos archivos fueron agregados o muestreados para mejorar el rendimiento del dashboard.
---
12. Principales hallazgos esperados
El dashboard permite identificar:
Racks y nodos que concentran mayor consumo energético.
Horarios con mayor energía o picos térmicos.
Diferencias de comportamiento entre nodos CPU-only y GPU.
Jobs no exitosos que acumulan energía relevante.
Casos específicos para revisión operativa mediante tabla de detalle.
---
13. Herramientas utilizadas
Python
Pandas
NumPy
PyArrow
Streamlit
Plotly
Jupyter Notebook
Git / GitHub
---
14. Estado del proyecto
El proyecto cuenta con:
Dataset final generado y revisado.
Archivos procesados para visualización.
Dashboard interactivo funcional.
Repositorio organizado para reproducción.
La siguiente etapa corresponde a la elaboración del documento técnico y la preparación de la presentación oral del proyecto.