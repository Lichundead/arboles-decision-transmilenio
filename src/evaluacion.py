"""Paso 3: medir qué tan bien predice el árbol, compararlo y dibujarlo.

Todas las métricas se calculan con la semana de prueba (25 al 31 de agosto),
que el árbol no vio al entrenar.

Uso: python src/evaluacion.py (imprime el informe y guarda las figuras en docs/figuras/)
"""
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.tree import plot_tree

from modelo import entrenar
from preparar_datos import CLASES, RAIZ

CARPETA_FIGURAS = RAIZ / "docs" / "figuras"


def linea_base(X_ent, y_ent, X_prueba, y_prueba):
    """Devuelve la exactitud de un modelo que siempre responde la clase más frecuente."""
    # Este "modelo" no mira los atributos. El árbol solo vale la pena si le gana.
    base = DummyClassifier(strategy="most_frequent").fit(X_ent, y_ent)
    return base.score(X_prueba, y_prueba)


def evaluar(arbol, X_prueba, y_prueba):
    """Imprime el reporte por clase y la matriz de confusión; devuelve la exactitud."""
    predicciones = arbol.predict(X_prueba)
    # Precisión y exhaustividad (recall) por clase: muestran en qué clase se equivoca más.
    print(classification_report(y_prueba, predicciones, labels=CLASES))
    # Filas = clase real, columnas = clase predicha. La diagonal son los aciertos.
    matriz = confusion_matrix(y_prueba, predicciones, labels=CLASES)
    print(pd.DataFrame(matriz, index=CLASES, columns=CLASES))
    # Exactitud: fracción de franjas bien clasificadas.
    return arbol.score(X_prueba, y_prueba)


def comparar_profundidades(X_ent, y_ent, X_prueba, y_prueba):
    """Devuelve hojas, exactitud y F1 macro en prueba para profundidades de 2 a 6.

    Por exactitud, la profundidad 4 sale peor que la 2 y la 3. Esa exactitud
    engaña: los árboles de profundidad 2 y 3 casi nunca predicen "media" y
    aciertan sobre todo diciendo "alta" o "baja". El F1 macro calcula el F1 de
    cada clase y los promedia, así que castiga a un árbol que ignora una de
    las tres. Con F1 macro, la 4 es la primera profundidad en que el árbol usa
    las tres clases.
    """
    # Cada nivel más duplica las hojas (reglas) que hay que explicar. La tabla
    # muestra cuánto se gana a cambio.
    filas = []
    for profundidad in range(2, 7):
        arbol = entrenar(X_ent, y_ent, profundidad)
        predicciones = arbol.predict(X_prueba)
        filas.append({
            "profundidad": profundidad,
            "hojas": arbol.get_n_leaves(),
            "exactitud_prueba": round(accuracy_score(y_prueba, predicciones), 3),
            "f1_macro": round(f1_score(y_prueba, predicciones, average="macro"), 3),
        })
    return pd.DataFrame(filas)


def dibujar_arbol(arbol):
    """Guarda docs/figuras/arbol.png con los tres primeros niveles del árbol."""
    # El árbol completo no se lee en una imagen. Las ramas recortadas aparecen como "(...)".
    # En cada caja, "value" son las proporciones en orden alfabético: [alta, baja, media].
    fig, ax = plt.subplots(figsize=(30, 9))
    plot_tree(arbol, max_depth=3, feature_names=arbol.feature_names_in_,
              class_names=arbol.classes_, filled=True, impurity=False,
              proportion=True, fontsize=10, ax=ax)
    fig.savefig(CARPETA_FIGURAS / "arbol.png", bbox_inches="tight")
    plt.close(fig)


def dibujar_matriz(arbol, X_prueba, y_prueba):
    """Guarda docs/figuras/matriz_confusion.png."""
    grafico = ConfusionMatrixDisplay.from_estimator(arbol, X_prueba, y_prueba, labels=CLASES, cmap="Blues")
    grafico.ax_.set(xlabel="Clase predicha", ylabel="Clase real")
    grafico.figure_.savefig(CARPETA_FIGURAS / "matriz_confusion.png", bbox_inches="tight")
    plt.close(grafico.figure_)


if __name__ == "__main__":
    from modelo import cargar_datos, separar

    X_ent, X_prueba, y_ent, y_prueba = separar(cargar_datos())
    arbol = entrenar(X_ent, y_ent)

    exactitud = evaluar(arbol, X_prueba, y_prueba)
    print(f"\nExactitud del árbol:  {exactitud:.3f}")
    print(f"Exactitud línea base: {linea_base(X_ent, y_ent, X_prueba, y_prueba):.3f}\n")

    # Cuánto reduce la entropía cada variable en todo el árbol (entre todas suman 1).
    # Una importancia de 0 significa que el árbol nunca pregunta por esa variable.
    importancias = pd.Series(arbol.feature_importances_, index=arbol.feature_names_in_)
    print("Importancia de las variables:")
    print(importancias.sort_values(ascending=False).round(3).to_string(), "\n")

    print("Exactitud y F1 macro según la profundidad:")
    print(comparar_profundidades(X_ent, y_ent, X_prueba, y_prueba).to_string(index=False))

    dibujar_arbol(arbol)
    dibujar_matriz(arbol, X_prueba, y_prueba)
    print(f"\nFiguras guardadas en {CARPETA_FIGURAS}")
