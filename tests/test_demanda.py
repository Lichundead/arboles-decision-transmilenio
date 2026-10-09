"""Pruebas del proyecto. Se ejecutan con: pytest

Cada prueba revisa una decisión del trabajo; docs/pruebas.md explica por qué importa cada una.
"""
from datetime import datetime, time

import pandas as pd

from evaluacion import linea_base
from modelo import cargar_datos, entrenar, separar
from preparar_datos import NO_SON_ESTACIONES, preparar

# Los datos se cargan y separan una sola vez para todas las pruebas.
datos = cargar_datos()
X_ent, X_prueba, y_ent, y_prueba = separar(datos)


def test_preparar_descarta_duales_totales_y_no_estaciones():
    # El CSV final ya no tiene la columna Fase, así que la limpieza se prueba
    # con un Excel en miniatura que tiene el mismo formato que el real.
    sabado = datetime(2026, 8, 1)
    columnas = ["Unnamed: 0", "Fase", "Línea", "Estación", "Acceso de Estación", "Intervalo",
                sabado, "Total general"]
    estacion = "(02001) Centro Comercial Santa Fe"
    filas = [
        [None, "I", "(33) Zona B", estacion, "Acceso A", time(6, 0), 10, 0],
        [None, "I", "(33) Zona B", estacion, "Acceso B", time(6, 0), 5, 0],  # se suma al acceso A
        [None, "I", "(33) Zona B", estacion, "Acceso A", time(7, 0), 1, 0],
        [None, "I", "(33) Zona B", estacion, "Acceso A", time(8, 0), 100, 0],
        [None, "I", "(33) Zona B", estacion, "Acceso A", time(4, 45), 3, 0],  # fuera de horario
        [None, "Dual", "(33) Zona B", estacion, "Acceso A", time(6, 0), 999, 0],
        [None, "I", "(99) X", "(50006) Corral Carrera 77", "Acceso A", time(6, 0), 999, 0],
        [None, "Total general", None, None, None, None, 999, 0],
        [None] * 8,
    ]
    resultado = preparar(pd.DataFrame(filas, columns=columnas))
    assert resultado["intervalo"].tolist() == ["06:00", "07:00", "08:00"]
    assert resultado["validaciones"].tolist() == [15, 1, 100]  # sin el 999 de Dual ni de totales


def test_dataset_tiene_121_estaciones():
    assert datos["codigo"].nunique() == 121
    assert not datos["codigo"].isin(NO_SON_ESTACIONES).any()
    assert datos.notna().all().all()  # una fila de totales dejaría código o nombre vacíos


def test_clases_balanceadas_en_cada_estacion():
    # La clase son los tercios de cada estación: cerca de 1/3 de cada nivel.
    proporciones = datos.groupby("codigo")["nivel_demanda"].value_counts(normalize=True)
    assert len(proporciones) == 121 * 3
    assert ((proporciones - 1 / 3).abs() < 0.02).all()


def test_sin_fuga_de_informacion():
    # Ni la respuesta (validaciones, nivel) ni la identidad de la estación.
    for prohibida in ["validaciones", "nivel_demanda", "nombre", "codigo"]:
        assert not any(columna.startswith(prohibida) for columna in X_ent.columns)


def test_fechas_de_entrenamiento_y_prueba_no_se_cruzan():
    fechas_ent = set(datos.loc[X_ent.index, "fecha"])
    fechas_prueba = set(datos.loc[X_prueba.index, "fecha"])
    assert fechas_ent.isdisjoint(fechas_prueba)
    assert max(fechas_ent) == "2026-08-24" and min(fechas_prueba) == "2026-08-25"


def test_arbol_supera_linea_base():
    # La línea base responde siempre la clase más frecuente, sin mirar los datos.
    arbol = entrenar(X_ent, y_ent)
    assert arbol.score(X_prueba, y_prueba) > linea_base(X_ent, y_ent, X_prueba, y_prueba) + 0.2


def test_festivos_son_7_y_17_de_agosto():
    festivos = set(datos.loc[datos["es_festivo"] == 1, "fecha"])
    assert festivos == {"2026-08-07", "2026-08-17"}
