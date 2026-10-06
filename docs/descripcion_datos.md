# Descripción de los datos

## Archivos

- `data/raw/08_TM_Resumen_de_Validaciones_Troncales_al_31_de_Agosto_del_2026_Intervalo_15_Mint.xlsx`:
  archivo original de TransMilenio (hoja *Validaciones Tullave*). Una fila por estación,
  acceso e intervalo; una columna por día.
- `data/processed/dataset_demanda.csv`: dataset con el que se entrena el árbol.
  253.394 filas, una por estación y franja de 15 minutos.
- `data/estaciones.csv`: catálogo de las 121 estaciones troncales (código, nombre, línea,
  troncal, si es portal y si es de transbordo).

Fuente: validaciones mensuales del sistema troncal por franjas de 15 minutos, publicadas por
TRANSMILENIO S.A. en <https://storage.googleapis.com/validaciones_tmsa/validaciones_mensuales.html>
(sección ValidacionTroncal, año 2026, agosto).

## Cómo se construye el CSV

`python src/preparar_datos.py` hace la limpieza. Los pasos están numerados y explicados en
los comentarios de la función `preparar` en [src/preparar_datos.py](../src/preparar_datos.py).
Al final comprueba que queden exactamente 121 estaciones.

## Cobertura

- Periodo: 1 al 31 de agosto de 2026 (31 días).
- Festivos: 7 de agosto (Batalla de Boyacá) y 17 de agosto (Asunción).
- Horario: franjas de 05:00 a 21:45 (68 por día).
- Estaciones: 121. La estación `08100` (Portal Tunal Cable, del TransMiCable) solo tiene 14 franjas por día; las demás tienen 68.
- No hay valores vacíos.

## Estaciones que no están en el dataset

El dataset no tiene todas las estaciones troncales del sistema. La troncal Caracas
aparece con solo 2 estaciones y la AutoNorte con 8. No están, por ejemplo, Portal Norte,
Héroes ni Av. Jiménez.

Esas estaciones sí vienen en el Excel, pero solo en filas cuya `Fase` es "Dual", y
`preparar_datos.py` descarta todas las filas de esa fase. En el Excel de agosto hay 32
estaciones troncales en esa situación (más un corral y un bicicletero), con 13,7 millones
de validaciones en el mes. Entre ellas están Portal Norte, Portal El Dorado, Portal Sur,
Calle 100, Toberín, Héroes, Av. Jiménez y las estaciones temporales de la Caracas.
Ninguna coincide con las 121 del dataset.

Las conclusiones de este trabajo aplican a las 121 estaciones del dataset, no a todo
TransMilenio.

## Columnas

| Columna | Tipo | Descripción | ¿Atributo del árbol? |
|---|---|---|---|
| `fecha` | texto | Día (AAAA-MM-DD). | No |
| `dia_semana` | entero | 0 = lunes … 6 = domingo. | Sí |
| `es_festivo` | 0/1 | 1 si el día es festivo. | Sí |
| `intervalo` | texto | Inicio de la franja (`HH:MM`). | No (se usa `hora`) |
| `hora` | decimal | La franja en horas: 07:15 → 7,25. | Sí |
| `codigo` | texto | Código de la estación (con cero inicial). | No |
| `nombre` | texto | Nombre de la estación. | No |
| `troncal` | texto | Zona/troncal (14 valores). | Sí (como 14 columnas 0/1) |
| `es_portal` | 0/1 | 1 si la estación es un portal (4 estaciones). | Sí |
| `es_transbordo` | 0/1 | 1 si es estación de transbordo (5 estaciones). | Sí |
| `validaciones` | entero | Entradas registradas en la franja. | No: de ella sale la clase |
| `nivel_demanda` | texto | Clase a predecir: baja, media o alta. | Es la clase |

## Cómo se define `nivel_demanda`

Para cada estación por separado, sus franjas se ordenan por número de validaciones y
se dividen en tres partes iguales (terciles):

- tercio inferior → `baja`
- tercio del medio → `media`
- tercio superior → `alta`

Por eso las tres clases tienen casi el mismo tamaño (≈ 84.500 filas cada una) y el azar
acertaría 1 de cada 3. También por eso "alta" significa *alta para esa estación*:
100 validaciones puede ser demanda alta en una estación pequeña y baja en un portal.

Se verificó con los datos: recalcular los terciles por estación reproduce el 100 % de las
etiquetas.
