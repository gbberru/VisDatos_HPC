# Visualización de datos para el análisis del consumo energético, temperatura y eficiencia operativa en servidores de un data center HPC

## Descripción del proyecto

Este proyecto desarrolla una visualización de datos para analizar el consumo energético, la temperatura y la eficiencia operativa de servidores en un data center HPC.

El análisis se basa en métricas temporales de nodos CPU/GPU y registros de jobs ejecutados en el clúster. El objetivo es identificar patrones de consumo, picos térmicos, diferencias entre nodos con y sin GPU, y posibles ineficiencias operativas asociadas al uso de recursos computacionales.

## Fuente de datos

Los datos fueron descargados desde el dataset público **Generic and ML Workloads in an HPC Datacenter**, disponible en Zenodo:

https://zenodo.org/records/11028934

## Estructura del repositorio

```text
VisDatos_HPC/
│
├── README.md
│
└── Transform_data/
    ├── Transform_data.ipynb
    └── Revison_data.ipynb
```

## Archivos originales utilizados

| Archivo | Descripción |
|---|---|
| `prom_slurm_joined.zip` | Dataset principal con métricas temporales de monitoreo unidas con información de jobs SLURM. |
| `node_hardware_info.parquet` | Información de hardware de los nodos del clúster. |
| `slurm_table_cleaned.parquet` | Información limpia de los jobs ejecutados en el data center HPC. |

## Proceso realizado para obtener el dataset final

El procesamiento de datos se realizó en el notebook `Transform_data.ipynb`.

De forma resumida, el proceso consistió en:

1. Descargar los archivos originales desde Zenodo.
2. Descomprimir `prom_slurm_joined.zip`.
3. Leer los archivos `.parquet` del dataset principal.
4. Seleccionar las columnas relevantes para el análisis de consumo energético, temperatura, uso de recursos y jobs SLURM.
5. Integrar información de hardware desde `node_hardware_info.parquet`.
6. Crear variables derivadas para facilitar el análisis visual.
7. Convertir unidades técnicas a formatos más interpretables, como bytes a GB, miliwatts a watts, joules a kWh y segundos a horas.
8. Generar un dataset final reducido y enriquecido en formato Parquet.


## Dataset final

| Característica | Valor |
|---|---:|
| Filas | 11.930.727 |
| Columnas | 53 |
| Tamaño aproximado en disco | 716 MB |
| Formato | Parquet |
| Rango temporal | 2022-06-30 a 2022-11-01 |


## Columnas del dataset final

| Columna | Significado | Unidad / Tipo |
|---|---|---|
| `prom_id` | Identificador del registro de monitoreo. | ID |
| `timestamp` | Fecha y hora de la medición. | Fecha/hora |
| `timestamp_seconds` | Fecha y hora representada en segundos Unix. | Segundos |
| `timestamp_seconds_delta` | Diferencia de tiempo entre mediciones consecutivas. | Segundos |
| `node` | Nombre del nodo físico del clúster. | Categórico |
| `rack_inferred` | Rack inferido a partir del nombre del nodo. | Categórico |
| `node_position_inferred` | Posición inferida del nodo dentro del rack. | Categórico |
| `gpu_node` | Indica si el nodo tiene GPU. | 0 = No, 1 = Sí |
| `gpu_model` | Modelo de GPU del nodo. | Categórico |
| `gpu_count` | Cantidad de GPU disponibles en el nodo. | Número de GPU |
| `cpu_tdp_total` | TDP total estimado de CPU del nodo. | Watts |
| `gpu_tdp_total` | TDP total estimado de GPU del nodo. | Watts |
| `node_load1` | Carga promedio del nodo en el último minuto. | Índice de carga |
| `node_load5` | Carga promedio del nodo en los últimos 5 minutos. | Índice de carga |
| `node_load15` | Carga promedio del nodo en los últimos 15 minutos. | Índice de carga |
| `node_load1_per_core` | Carga del nodo ajustada por número de cores. | Índice de carga por core |
| `node_power_usage` | Potencia instantánea consumida por el nodo. | Watts |
| `node_rapl_package_power_sum` | Potencia estimada del paquete CPU mediante RAPL. | Watts |
| `node_rapl_package_joules_total_sum_delta` | Energía CPU consumida entre mediciones. | Joules |
| `cpu_package_energy_kwh` | Energía CPU convertida a kWh. | kWh |
| `node_memory_Active_bytes` | Memoria RAM activa del nodo. | Bytes |
| `node_memory_MemFree_bytes` | Memoria RAM libre del nodo. | Bytes |
| `ram_active_gb` | Memoria RAM activa convertida a GB. | GB |
| `ram_free_gb` | Memoria RAM libre convertida a GB. | GB |
| `node_hwmon_temp_celsius_mean` | Temperatura promedio de sensores hardware del nodo. | °C |
| `node_hwmon_temp_celsius_max` | Temperatura máxima de sensores hardware del nodo. | °C |
| `node_thermal_zone_temp_mean` | Temperatura promedio de zonas térmicas del nodo. | °C |
| `node_thermal_zone_temp_max` | Temperatura máxima de zonas térmicas del nodo. | °C |
| `nvidia_gpu_memory_used_bytes_sum` | Memoria GPU utilizada. | Bytes |
| `gpu_memory_used_gb` | Memoria GPU utilizada convertida a GB. | GB |
| `nvidia_gpu_temperature_celsius_mean` | Temperatura promedio de GPU NVIDIA. | °C |
| `nvidia_gpu_temperature_celsius_max` | Temperatura máxima de GPU NVIDIA. | °C |
| `nvidia_gpu_power_usage_milliwatts_mean` | Potencia promedio de GPU NVIDIA. | Miliwatts |
| `gpu_power_watts_mean` | Potencia promedio de GPU convertida a watts. | Watts |
| `gpu_power_watts_max` | Potencia máxima de GPU convertida a watts. | Watts |
| `nvidia_gpu_duty_cycle_mean` | Uso promedio de la GPU. | Porcentaje (%) |
| `nvidia_gpu_duty_cycle_max` | Uso máximo de la GPU. | Porcentaje (%) |
| `node_disk_read_bytes_total_sum_delta` | Bytes leídos desde disco entre mediciones. | Bytes |
| `node_disk_written_bytes_total_sum_delta` | Bytes escritos en disco entre mediciones. | Bytes |
| `node_network_receive_bytes_total_sum_delta` | Bytes recibidos por red entre mediciones. | Bytes |
| `node_network_transmit_bytes_total_sum_delta` | Bytes transmitidos por red entre mediciones. | Bytes |
| `node_energy_kwh_est` | Energía estimada consumida por el nodo. | kWh |
| `gpu_energy_kwh_est` | Energía estimada consumida por GPU. | kWh |
| `co2_kg_est` | Emisiones estimadas de CO₂ calculadas desde la energía estimada. | kg CO₂ estimado |
| `slurm_id` | Identificador del job SLURM. | ID |
| `start_date` | Fecha y hora de inicio del job. | Fecha/hora |
| `end_date` | Fecha y hora de finalización del job. | Fecha/hora |
| `job_duration_hours` | Duración del job. | Horas |
| `state` | Estado final del job. | Categórico |
| `nodetypes` | Tipo de nodo usado por el job. | Categórico |
| `numnodes` | Número de nodos utilizados por el job. | Cantidad |
| `numcores` | Número de cores utilizados por el job. | Cantidad |
| `slurm_nodes` | Lista de nodos asociados al job. | Categórico / lista |


## Revisión del dataset

El notebook `Revison_data.ipynb` valida que el dataset final esté listo para la etapa de visualización.

En esta revisión se verifican dimensiones, columnas, tipos de datos, valores nulos, valores negativos, duplicados, rango temporal y consistencia entre las mediciones y los jobs SLURM.


## Estado actual

El dataset final ya fue generado y revisado. La siguiente etapa corresponde al diseño y construcción de visualizaciones para analizar consumo energético, temperatura y eficiencia operativa en servidores de un data center HPC.
