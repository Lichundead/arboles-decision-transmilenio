# Árboles de decisión: demanda en estaciones de TransMilenio

Trabajo de Inteligencia Artificial sobre el capítulo 17 de Palma Méndez (2008),
*Aprendizaje de árboles y reglas de decisión*. Un árbol de decisión clasifica la demanda
de una estación troncal de TransMilenio en una franja de 15 minutos como baja, media o
alta. Usa entropía (ganancia de información, como ID3/C4.5) y tiene 4 niveles, de modo
que sus 16 reglas se pueden leer y explicar.

## Requisitos

- Python 3.11 o superior.
- Las librerías de [requirements.txt](requirements.txt), con versiones fijas: pandas,
  scikit-learn, openpyxl, matplotlib y pytest.

## Instalación

Desde la carpeta del proyecto, se crea un entorno virtual y se instalan las dependencias.

Linux y macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En la consola clásica de Windows (cmd), el entorno se activa con `.venv\Scripts\activate.bat`.
Si PowerShell no deja ejecutar el script de activación, se habilita para el usuario con
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Los comandos siguientes suponen que el entorno está activado.

## Ejecución

| Comando | Qué hace |
|---|---|
| `python src/main.py` | Programa interactivo. Entrena el árbol, muestra su exactitud y permite ver las reglas o consultar una estación, un día y una hora. |
| `python src/evaluacion.py` | Informe: reporte por clase, matriz de confusión, importancia de variables, comparación de profundidades. Guarda las figuras en [docs/figuras/](docs/figuras/). |
| `python src/preparar_datos.py` | Regenera `data/processed/dataset_demanda.csv` a partir del Excel original. |
| `pytest` | Corre las 7 pruebas (unos 3 segundos). Están descritas en [docs/pruebas.md](docs/pruebas.md). |

El CSV procesado ya está en el repositorio, así que `main.py`, `evaluacion.py` y las pruebas
funcionan sin el Excel. Para correr `preparar_datos.py` hay que descargar el Excel (ver
[Datos](#datos)) y guardarlo como
`data/raw/08_TM_Resumen_de_Validaciones_Troncales_al_31_de_Agosto_del_2026_Intervalo_15_Mint.xlsx`.

El modelo no se guarda en ningún archivo. Cada programa lo entrena de nuevo, lo que tarda
unos segundos.

Ejemplo de consulta en `main.py`:

```
Parte del nombre de la estación: americas
  1. Portal Américas
  2. Av. Américas - Av. Boyacá
  3. Américas - Cr.53
Número de la estación: 1
Día de agosto (1-31): 25
Hora (HH:MM, de 05:00 a 21:45): 07:15

Portal Américas (05000), martes 25 de agosto, 07:15
Predicción: alta
Camino de reglas:
  hora <= 19.38
  dia_semana <= 5.50
  es_festivo = 0
  hora <= 8.62
Nivel real: alta (2411 validaciones, día de prueba)
```

## Datos

TRANSMILENIO S.A. publica las validaciones mensuales del sistema troncal por franjas de
15 minutos en su portal de datos abiertos:
<https://storage.googleapis.com/validaciones_tmsa/validaciones_mensuales.html>
(sección ValidacionTroncal, año 2026, agosto). La entidad también aparece en el portal
de datos abiertos de Bogotá: <https://datosabiertos.bogota.gov.co/organization/transmilenio>.

Este trabajo usa el mes de agosto de 2026: 121 estaciones, franjas de 05:00 a 21:45 y
253.394 filas. Las columnas y la definición de la clase (tercios de validaciones por
estación) están en [docs/descripcion_datos.md](docs/descripcion_datos.md).

## Arquitectura

Cada archivo de `src/` es un paso del proceso y lo explica un integrante del grupo.

```
Excel de TransMilenio + data/estaciones.csv
        |
        v
preparar_datos.py   limpia, suma accesos, crea variables y la clase
        |
        v
data/processed/dataset_demanda.csv
        |
        v
modelo.py           carga, separa por fecha, entrena, reglas y explicación
        |
        +--> evaluacion.py   métricas, línea base, importancias, figuras
        +--> main.py         programa interactivo
```

| Archivo | Funciones principales |
|---|---|
| [src/preparar_datos.py](src/preparar_datos.py) | `preparar` |
| [src/modelo.py](src/modelo.py) | `cargar_datos`, `codificar`, `separar`, `entrenar`, `reglas`, `explicar` |
| [src/evaluacion.py](src/evaluacion.py) | `linea_base`, `evaluar`, `importancias`, `comparar_profundidades`, `dibujar_arbol`, `dibujar_matriz` |
| [src/main.py](src/main.py) | `consultar`, `main` |
| [tests/test_demanda.py](tests/test_demanda.py) | 7 pruebas |

El árbol se entrena con los días 1 al 24 de agosto y se prueba con los días 25 al 31,
que no ve durante el entrenamiento. Sus variables de entrada son `hora`, `dia_semana`,
`es_festivo`, `es_portal`, `es_transbordo` y `troncal` (14 columnas 0/1). Las
validaciones no entran porque de ellas sale la clase. El nombre y el código de la
estación tampoco, porque producirían reglas ilegibles.

## Resultados

En la semana de prueba el árbol acierta el 54,3 % de las franjas. La línea base, que
siempre responde "baja" (la clase más frecuente en entrenamiento), acierta el 27,3 %.

| Condición | Demanda que predice |
|---|---|
| Lunes a sábado no festivo, hasta las 8:30 | alta |
| Lunes a sábado no festivo, de 8:45 a 19:15 | media |
| Domingo o festivo, hasta las 19:15 | baja (media en portales temprano y en Ciudad Bolívar) |
| Desde las 19:30 | baja (con excepciones por troncal) |

Las variables que más pesan son `hora` (0,40), `dia_semana` (0,32) y `es_festivo` (0,26).
Las troncales y `es_portal` suman menos de 0,03, y el árbol nunca usa `es_transbordo`.

El error más común es la hora pico de la tarde, que el árbol marca como media cuando es
alta: acierta solo el 29 % de las franjas altas. La semana de prueba no tiene festivos,
así que las reglas de festivo no se evalúan.

Exactitud en prueba según la profundidad:

| Profundidad | Hojas | Exactitud |
|---|---|---|
| 2 | 4 | 0,570 |
| 3 | 8 | 0,572 |
| 4 | 16 | 0,543 |
| 5 | 32 | 0,579 |
| 6 | 62 | 0,594 |

Las figuras están en [docs/figuras/arbol.png](docs/figuras/arbol.png) y
[docs/figuras/matriz_confusion.png](docs/figuras/matriz_confusion.png). En el dibujo del
árbol, `value` da las proporciones de cada clase en orden alfabético: alta, baja, media.
