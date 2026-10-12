"""Programa interactivo para consultar el árbol.

Al iniciar entrena el árbol y muestra su exactitud frente a la línea base.
Después ofrece un menú para ver las reglas o consultar una estación en un día y
una hora de agosto de 2026. La consulta muestra la predicción, el camino de
reglas que llevó a ella y el nivel real de esa franja, si existe en los datos.

Uso: python src/main.py
"""
import unicodedata
from datetime import date

from evaluacion import linea_base
from modelo import ULTIMO_DIA_ENTRENAMIENTO, cargar_datos, codificar, entrenar, explicar, reglas, separar
from preparar_datos import FESTIVOS

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def sin_tildes(texto):
    """Pasa el texto a minúsculas sin tildes, para que "americas" encuentre "Portal Américas"."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


# Las funciones pedir_* lanzan ValueError con un mensaje para el usuario cuando
# la entrada no sirve. main() lo atrapa y vuelve al menú sin que el programa se caiga.

def pedir_numero(mensaje, minimo, maximo):
    """Pide un entero entre minimo y maximo."""
    texto = input(mensaje).strip()
    if not texto.isdigit() or not minimo <= int(texto) <= maximo:
        raise ValueError(f"escriba un número entre {minimo} y {maximo}.")
    return int(texto)


def pedir_estacion(estaciones):
    """Busca por parte del nombre y devuelve la fila de la estación elegida."""
    buscado = sin_tildes(input("Parte del nombre de la estación: ").strip())
    if not buscado:
        raise ValueError("escriba al menos una letra.")
    encontradas = estaciones[estaciones["nombre"].map(sin_tildes).str.contains(buscado, regex=False)]
    if encontradas.empty:
        raise ValueError(f"ninguna estación contiene '{buscado}'.")
    if len(encontradas) > 1:
        for i, nombre in enumerate(encontradas["nombre"], start=1):
            print(f"  {i}. {nombre}")
        return encontradas.iloc[pedir_numero("Número de la estación: ", 1, len(encontradas)) - 1]
    return encontradas.iloc[0]


def pedir_hora():
    """Pide una hora HH:MM y devuelve (horas, minutos)."""
    # Solo franjas de 15 minutos dentro del horario del dataset (05:00 a 21:45).
    horas, _, minutos = input("Hora (HH:MM, de 05:00 a 21:45): ").strip().partition(":")
    if not (horas.isdigit() and minutos.isdigit()):
        raise ValueError("use el formato HH:MM, por ejemplo 07:15.")
    horas, minutos = int(horas), int(minutos)
    if minutos not in (0, 15, 30, 45) or not 5 <= horas + minutos / 60 <= 21.75:
        raise ValueError("la hora debe ser una franja de 15 minutos entre 05:00 y 21:45.")
    return horas, minutos


def consultar(datos, arbol):
    """Pide estación, día y hora; muestra la predicción, su explicación y el nivel real."""
    estacion = pedir_estacion(datos.drop_duplicates("codigo"))
    dia = pedir_numero("Día de agosto (1-31): ", 1, 31)
    horas, minutos = pedir_hora()
    fecha = f"2026-08-{dia:02d}"
    intervalo = f"{horas:02d}:{minutos:02d}"

    # Fila con los datos fijos de la estación (troncal, portal, transbordo) y el
    # momento consultado, codificada igual que en el entrenamiento.
    fila = estacion.to_frame().T
    fila["hora"] = horas + minutos / 60
    fila["dia_semana"] = date(2026, 8, dia).weekday()
    fila["es_festivo"] = int(fecha in FESTIVOS)
    X = codificar(fila, arbol.feature_names_in_)

    print(f"\n{estacion['nombre']} ({estacion['codigo']}), {DIAS[fila["dia_semana"].iloc[0]]} "
          f"{dia} de agosto, {intervalo}" + (" (festivo)" if fila["es_festivo"].iloc[0] else ""))
    print(f"Predicción: {arbol.predict(X)[0]}")
    print("Camino de reglas:")
    for condicion in explicar(arbol, X):
        print(f"  {condicion}")

    real = datos[(datos["codigo"] == estacion["codigo"]) & (datos["fecha"] == fecha)
                 & (datos["intervalo"] == intervalo)]
    if real.empty:
        print("Nivel real: no hay datos de esa franja.")
    else:
        # Si el día fue de entrenamiento, el árbol ya vio ese dato y acertar tiene menos mérito.
        parte = "entrenamiento" if fecha <= ULTIMO_DIA_ENTRENAMIENTO else "prueba"
        print(f"Nivel real: {real['nivel_demanda'].iloc[0]} "
              f"({real['validaciones'].iloc[0]} validaciones, día de {parte})")


def main():
    """Entrena el árbol y atiende el menú hasta que el usuario elige salir."""
    print("Entrenando el árbol...")
    datos = cargar_datos()
    X_ent, X_prueba, y_ent, y_prueba = separar(datos)
    arbol = entrenar(X_ent, y_ent)
    print(f"Exactitud en prueba (25 al 31 de agosto): {arbol.score(X_prueba, y_prueba):.3f}")
    print(f"Línea base (siempre la clase más frecuente): {linea_base(X_ent, y_ent, X_prueba, y_prueba):.3f}")

    while True:
        print("\n1. Ver las reglas del árbol\n2. Consultar una estación\n0. Salir")
        opcion = input("Opción: ").strip()
        if opcion == "1":
            print(reglas(arbol))
        elif opcion == "2":
            try:
                consultar(datos, arbol)
            except ValueError as error:
                # Una entrada inválida cancela la consulta y vuelve al menú.
                print(f"Entrada inválida: {error}")
        elif opcion == "0":
            break
        else:
            print("Opción no válida: escriba 1, 2 o 0.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C o Ctrl+D: salir sin mostrar un error.
        print()
