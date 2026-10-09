"""Paso 1: convertir el Excel de TransMilenio en un dataset limpio.

Entrada: el Excel de validaciones de agosto de 2026 (data/raw/) y el catálogo
data/estaciones.csv.
Salida: data/processed/dataset_demanda.csv, con una fila por estación, día y
franja de 15 minutos, y la clase nivel_demanda (baja, media o alta).

Uso: python src/preparar_datos.py
"""
from datetime import time
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RUTA_EXCEL = RAIZ / "data" / "raw" / "08_TM_Resumen_de_Validaciones_Troncales_al_31_de_Agosto_del_2026_Intervalo_15_Mint.xlsx"
RUTA_ESTACIONES = RAIZ / "data" / "estaciones.csv"
RUTA_DATOS = RAIZ / "data" / "processed" / "dataset_demanda.csv"

# Corral Carrera 77 y Bicicletero Mirador del Paraíso registran validaciones,
# pero no son estaciones.
NO_SON_ESTACIONES = ["50006", "40004"]
# Festivos de agosto de 2026: Batalla de Boyacá (7) y Asunción de la Virgen (17).
FESTIVOS = ["2026-08-07", "2026-08-17"]

CLASE = "nivel_demanda"
# Niveles de demanda de menor a mayor. Este orden también hace que la matriz de
# confusión se lea fácil en evaluacion.py.
CLASES = ["baja", "media", "alta"]


def preparar(crudo):
    """Convierte la tabla cruda del Excel en el dataset del modelo.

    Recibe la hoja del Excel tal como la lee pandas y devuelve un DataFrame con
    una fila por estación, día y franja de 15 minutos.
    """
    # 1. Limpiar. La primera columna está vacía y "Total general" es una suma,
    # no un día. También se quitan las filas vacías, la fila de totales y las
    # filas de la fase "Dual". Esas filas son sobre todo rutas duales, pero también
    # traen algunas estaciones troncales (ver docs/descripcion_datos.md).
    crudo = crudo.iloc[:, 1:].drop(columns="Total general").dropna(how="all")
    crudo = crudo[~crudo["Fase"].isin(["Total general", "Dual"])]
    # "(05000) Portal Américas" -> "05000". Se guarda como texto para no perder
    # el cero inicial. El nombre y la troncal se toman después de estaciones.csv.
    crudo["codigo"] = crudo["Estación"].str.extract(r"\((\d+)\)", expand=False)
    crudo = crudo[~crudo["codigo"].isin(NO_SON_ESTACIONES)]

    # 2. De formato ancho a largo: cada una de las 31 columnas de días pasa a
    # ser una fila (estación, acceso, intervalo, fecha, validaciones).
    largo = crudo.melt(
        id_vars=["Fase", "Línea", "Estación", "Acceso de Estación", "Intervalo", "codigo"],
        var_name="fecha", value_name="validaciones",
    )

    # 3. Sumar los accesos de cada estación. Una celda vacía significa que ese
    # día no hubo validaciones, y sum() la cuenta como 0.
    # Agrupar en este orden deja el CSV ordenado por estación, fecha e intervalo.
    datos = largo.groupby(["codigo", "fecha", "Intervalo"], as_index=False)["validaciones"].sum()
    datos = datos.rename(columns={"Intervalo": "intervalo"})
    datos["validaciones"] = datos["validaciones"].astype(int)

    # 4. Solo de 05:00 a 21:45, la franja en que operan todas las estaciones
    # todos los días. Fuera de ella hay estaciones cerradas o que abren solo
    # algunos días; esas franjas casi vacías saldrían "baja" sin que el árbol
    # aprenda nada de ellas.
    datos = datos[datos["intervalo"].between(time(5, 0), time(21, 45))].copy()

    # 5. Variables de entrada: lo que se sabe de una franja antes de que ocurra.
    fecha = pd.to_datetime(datos["fecha"])
    datos["fecha"] = fecha.dt.strftime("%Y-%m-%d")
    datos["dia_semana"] = fecha.dt.dayofweek  # 0 = lunes, 6 = domingo
    datos["es_festivo"] = datos["fecha"].isin(FESTIVOS).astype(int)
    datos["hora"] = [t.hour + t.minute / 60 for t in datos["intervalo"]]  # 7:15 -> 7.25
    datos["intervalo"] = [t.strftime("%H:%M") for t in datos["intervalo"]]

    # 6. Clase: tercios de las validaciones de cada estación por separado, para
    # que "alta" quiera decir "alta para esa estación". Un portal siempre tiene
    # más gente que una estación pequeña. rank(method="first") desempata los
    # valores repetidos; sin él, qcut falla cuando un corte cae en un empate.
    datos[CLASE] = datos.groupby("codigo")["validaciones"].transform(
        lambda v: pd.qcut(v.rank(method="first"), 3, labels=CLASES)
    ).astype(str)

    # 7. Unir con el catálogo de estaciones (nombre, troncal, portal, transbordo).
    estaciones = pd.read_csv(RUTA_ESTACIONES, dtype={"codigo": str})
    datos = datos.merge(estaciones, on="codigo", validate="many_to_one")

    # El nombre, el código y las validaciones se conservan para que el CSV se
    # pueda leer y revisar, aunque el árbol no los use.
    return datos[["fecha", "dia_semana", "es_festivo", "intervalo", "hora", "codigo", "nombre",
                  "troncal", "es_portal", "es_transbordo", "validaciones", CLASE]]


if __name__ == "__main__":
    # Los encabezados están en la fila 7 del Excel; pandas cuenta desde 0, por eso header=6.
    datos = preparar(pd.read_excel(RUTA_EXCEL, sheet_name="Validaciones Tullave", header=6))
    # Si sale otro número, el Excel cambió o se coló algo que no es una estación.
    assert datos["codigo"].nunique() == 121, datos["codigo"].nunique()
    datos.to_csv(RUTA_DATOS, index=False)

    print(f"Filas: {len(datos)}")
    print(f"Estaciones: {datos['codigo'].nunique()}")
    print(f"Fechas: {datos['fecha'].min()} a {datos['fecha'].max()}")
    print(datos[CLASE].value_counts())
