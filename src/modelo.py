"""Paso 2: entrenar el árbol de decisión y leerlo como reglas.

Carga el dataset que genera preparar_datos.py, lo separa por fechas, entrena
el árbol y lo traduce a reglas SI ... ENTONCES que se pueden leer en voz alta.
"""
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

from preparar_datos import CLASE, RUTA_DATOS

# Variables de entrada: cuándo ocurre la franja (hora, día, festivo) y qué tipo
# de estación es (portal, transbordo, troncal).
# No entran:
# - validaciones: la clase se calcula a partir de ellas, así que el árbol
#   tendría la respuesta (fuga de información).
# - nombre y código de la estación: con 121 estaciones el árbol produciría
#   reglas ilegibles del tipo "estación = Calle 45 o Calle 57 o ...".
ATRIBUTOS = ["hora", "dia_semana", "es_festivo", "es_portal", "es_transbordo", "troncal"]

# Se entrena con el pasado (1 al 24 de agosto) y se prueba con la última semana
# (25 al 31), como se usaría en la realidad: para predecir días que aún no se ven.
ULTIMO_DIA_ENTRENAMIENTO = "2026-08-24"

# Con 4 niveles el árbol tiene como máximo 16 hojas: cabe en una diapositiva y
# cada regla se puede leer en voz alta.
PROFUNDIDAD = 4


def cargar_datos():
    """Lee el dataset procesado."""
    # El código se lee como texto para no perder el cero inicial (02001, no 2001).
    return pd.read_csv(RUTA_DATOS, dtype={"codigo": str})


def codificar(datos, columnas=None):
    """Devuelve la tabla de variables de entrada (X) lista para el árbol.

    Si se pasan columnas, la tabla queda con esas columnas y en ese orden.
    Sirve para codificar una consulta igual que los datos de entrenamiento.
    """
    # El árbol solo compara números, así que la troncal (texto) se convierte en
    # una columna 0/1 por troncal: "troncal_Zona B AutoNorte" = 1 si es de esa zona.
    X = pd.get_dummies(datos[ATRIBUTOS], columns=["troncal"], dtype=int)
    # Con una sola fila, get_dummies solo crea la columna de su troncal. reindex
    # agrega las demás en 0, en el mismo orden con que se entrenó el árbol.
    return X if columnas is None else X.reindex(columns=columnas, fill_value=0)


def separar(datos):
    """Devuelve X_ent, X_prueba, y_ent, y_prueba, separados por fecha."""
    X = codificar(datos)
    y = datos[CLASE]
    # Las fechas están en formato AAAA-MM-DD, así que se pueden comparar como texto.
    entrenamiento = datos["fecha"] <= ULTIMO_DIA_ENTRENAMIENTO
    return X[entrenamiento], X[~entrenamiento], y[entrenamiento], y[~entrenamiento]


def entrenar(X, y, profundidad=PROFUNDIDAD):
    """Entrena y devuelve el árbol de decisión."""
    # criterion="entropy": en cada nodo se elige el atributo con mayor ganancia
    # de información, el mismo criterio de ID3/C4.5 (Palma Méndez, cap. 17).
    # max_depth es una prepoda: detiene el crecimiento para que el árbol siga
    # siendo explicable y no se sobreajuste. random_state fija el desempate
    # entre atributos igual de buenos, así todos obtenemos el mismo árbol.
    arbol = DecisionTreeClassifier(criterion="entropy", max_depth=profundidad, random_state=42)
    return arbol.fit(X, y)


def reglas(arbol):
    """Devuelve el árbol completo como texto."""
    # Cada camino de la raíz a una hoja es una regla SI ... ENTONCES clase.
    return export_text(arbol, feature_names=list(arbol.feature_names_in_))


def explicar(arbol, fila):
    """Devuelve las condiciones que cumplió una fila hasta llegar a su hoja.

    fila es un DataFrame de una sola fila, codificado con codificar().
    Ejemplo: ["hora <= 19.38", "dia_semana <= 5.50", "es_festivo = 0", "hora <= 8.62"]
    """
    nodos = arbol.decision_path(fila).indices  # nodos visitados, de la raíz a la hoja
    condiciones = []
    for nodo in nodos[:-1]:  # el último nodo es la hoja, que ya no pregunta nada
        columna = arbol.feature_names_in_[arbol.tree_.feature[nodo]]
        umbral = arbol.tree_.threshold[nodo]
        valor = fila[columna].iloc[0]
        if columna.startswith(("es_", "troncal_")):
            # Columnas 0/1: "es_festivo = 0" se lee mejor que "es_festivo <= 0.50".
            condiciones.append(f"{columna} = {valor}")
        elif valor <= umbral:
            condiciones.append(f"{columna} <= {umbral:.2f}")
        else:
            condiciones.append(f"{columna} > {umbral:.2f}")
    return condiciones
