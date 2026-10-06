# Pruebas

## Pruebas automáticas

Se ejecutan desde la raíz del proyecto, con el entorno virtual activado:

```bash
pytest
```

`pytest.ini` agrega `src/` al `pythonpath`, así que las pruebas importan los módulos
directamente. Tardan unos 3 segundos.

| Prueba | Qué comprueba | Por qué importa |
|---|---|---|
| `test_preparar_descarta_duales_totales_y_no_estaciones` | Con un Excel en miniatura: se descartan las filas Dual, la de totales, las vacías, las de no estaciones (50006) y las franjas fuera de horario, y se suman los accesos. | El CSV final ya no tiene la columna `Fase`; esta prueba no necesita el Excel real. |
| `test_dataset_tiene_121_estaciones` | El dataset tiene 121 estaciones, ninguna es 50006 ni 40004 y no hay valores vacíos. | Una fila de totales o una "estación" que no lo es cambiaría los tercios. |
| `test_clases_balanceadas_en_cada_estacion` | En cada estación, cada nivel es aproximadamente 1/3 de las franjas. | Confirma que la clase se calculó como tercios por estación. |
| `test_sin_fuga_de_informacion` | Ni `validaciones`, ni `nivel_demanda`, ni `nombre`, ni `codigo` están entre las variables de entrada. | Con `validaciones` el árbol tendría la respuesta; con el nombre, reglas ilegibles. |
| `test_fechas_de_entrenamiento_y_prueba_no_se_cruzan` | Entrenamiento hasta el 24 de agosto y prueba desde el 25, sin días en común. | Probar con días que el árbol ya vio inflaría la exactitud. |
| `test_arbol_supera_linea_base` | El árbol supera por más de 0,2 a la línea base. | La línea base responde siempre *baja* y acierta 0,273; el árbol obtiene 0,543. |
| `test_festivos_son_7_y_17_de_agosto` | Los únicos días marcados como festivos son el 7 y el 17 de agosto. | Un festivo mal marcado cambia las reglas de domingo/festivo. |

Resultado actual:

```
7 passed
```

## Pruebas del programa

Casos ejecutados con `python src/main.py`. Al iniciar, el programa siempre muestra:

```
Entrenando el árbol...
Exactitud en prueba (25 al 31 de agosto): 0.543
Línea base (siempre la clase más frecuente): 0.273
```

### Caso 1. Hora pico de la mañana en un día de prueba

Objetivo: comprobar una predicción en la regla de hora pico, con un día que el árbol no
vio al entrenar.

Entrada: opción `2`, estación `americas`, número `1` (Portal Américas), día `25`
(martes), hora `07:15`.

Resultado esperado: el camino pasa por `hora <= 8.62` en un día hábil no festivo y la
predicción es *alta*. El programa muestra el nivel real e indica que es un día de prueba.

Resultado obtenido:

```
Portal Américas (05000), martes 25 de agosto, 07:15
Predicción: alta
Camino de reglas:
  hora <= 19.38
  dia_semana <= 5.50
  es_festivo = 0
  hora <= 8.62
Nivel real: alta (2411 validaciones, día de prueba)
```

La predicción coincide con el nivel real.

[Captura 1]

### Caso 2. La misma estación y hora en domingo

Objetivo: comprobar que el día de la semana cambia el camino del árbol.

Entrada: opción `2`, estación `americas`, número `1` (Portal Américas), día `30`
(domingo), hora `07:15`.

Resultado esperado: el camino toma la rama `dia_semana > 5.50` (domingo) y la
predicción deja de ser *alta*.

Resultado obtenido:

```
Portal Américas (05000), domingo 30 de agosto, 07:15
Predicción: media
Camino de reglas:
  hora <= 19.38
  dia_semana > 5.50
  hora <= 8.38
  es_portal = 1
Nivel real: baja (287 validaciones, día de prueba)
```

El camino cambia como se esperaba. La predicción (*media*) no coincide con el nivel real
(*baja*): la regla de domingo temprano en portales sobrestima esta franja.

[Captura 2]

### Caso 3. Día festivo

Objetivo: comprobar que un festivo que cae en día hábil sigue la rama de festivo.

Entrada: opción `2`, estación `ricaurte`, número `2` (Ricaurte, troncal Calle 13), día
`7` (viernes, Batalla de Boyacá), hora `07:15`.

Resultado esperado: el encabezado marca el día como festivo, el camino pasa por
`es_festivo = 1` y la predicción es *baja*, aunque sea hora pico en un viernes.

Resultado obtenido:

```
Ricaurte (12003), viernes 7 de agosto, 07:15 (festivo)
Predicción: baja
Camino de reglas:
  hora <= 19.38
  dia_semana <= 5.50
  es_festivo = 1
  troncal_Zona Z Av. Cali Sur = 0
Nivel real: baja (11 validaciones, día de entrenamiento)
```

La predicción coincide con el nivel real. El 7 de agosto es un día de entrenamiento, así
que el árbol ya había visto este dato.

[Captura 3]

### Caso 4. Ver las reglas del árbol

Objetivo: comprobar que la opción 1 muestra el árbol completo.

Entrada: opción `1`.

Resultado esperado: el árbol en texto, con 4 niveles y 16 hojas, empezando por
`hora <= 19.38`.

Resultado obtenido:

```
|--- hora <= 19.38
|   |--- dia_semana <= 5.50
|   |   |--- es_festivo <= 0.50
|   |   |   |--- hora <= 8.62
|   |   |   |   |--- class: alta
|   |   |   |--- hora >  8.62
|   |   |   |   |--- class: media
|   |   |--- es_festivo >  0.50
|   |   |   |--- troncal_Zona Z Av. Cali Sur <= 0.50
|   |   |   |   |--- class: baja
|   |   |   |--- troncal_Zona Z Av. Cali Sur >  0.50
|   |   |   |   |--- class: baja
|   |--- dia_semana >  5.50
|   |   |--- hora <= 8.38
|   |   |   |--- es_portal <= 0.50
|   |   |   |   |--- class: baja
|   |   |   |--- es_portal >  0.50
|   |   |   |   |--- class: media
|   |   |--- hora >  8.38
|   |   |   |--- troncal_Zona T Ciudad Bolívar <= 0.50
|   |   |   |   |--- class: baja
|   |   |   |--- troncal_Zona T Ciudad Bolívar >  0.50
|   |   |   |   |--- class: media
|--- hora >  19.38
|   |--- hora <= 20.38
|   |   |--- dia_semana <= 5.50
|   |   |   |--- troncal_Zona E NQS Central <= 0.50
|   |   |   |   |--- class: baja
|   |   |   |--- troncal_Zona E NQS Central >  0.50
|   |   |   |   |--- class: media
|   |   |--- dia_semana >  5.50
|   |   |   |--- troncal_Zona Z Av. Cali Sur <= 0.50
|   |   |   |   |--- class: baja
|   |   |   |--- troncal_Zona Z Av. Cali Sur >  0.50
|   |   |   |   |--- class: baja
|   |--- hora >  20.38
|   |   |--- troncal_Zona Z Av. Cali Sur <= 0.50
|   |   |   |--- troncal_Zona A Caracas <= 0.50
|   |   |   |   |--- class: baja
|   |   |   |--- troncal_Zona A Caracas >  0.50
|   |   |   |   |--- class: media
|   |   |--- troncal_Zona Z Av. Cali Sur >  0.50
|   |   |   |--- dia_semana <= 4.50
|   |   |   |   |--- class: media
|   |   |   |--- dia_semana >  4.50
|   |   |   |   |--- class: baja
```

Se muestran las 16 hojas. Después el programa vuelve al menú.

[Captura 4]

### Caso 5. Entradas inválidas

Objetivo: comprobar que el programa no se cae con entradas incorrectas y vuelve al menú.

Entradas, en una misma sesión:

1. Opción `2`, estación `portal norte`, que no está en el dataset.
2. Opción `2`, estación `americas`, número `1`, día `25`, hora `7.15` (formato inválido).
3. Opción `9`, que no existe en el menú.

Resultado esperado: un mensaje para cada error y el menú de nuevo después de cada uno.

Resultado obtenido:

```
Entrada inválida: ninguna estación contiene 'portal norte'.
Entrada inválida: use el formato HH:MM, por ejemplo 07:15.
Opción no válida: escriba 1, 2 o 0.
```

Cada mensaje aparece seguido del menú, y la opción `0` cierra el programa sin error.
También se probaron un día fuera de rango (`40`), la hora `7:10` (no es una franja de 15
minutos), texto vacío como estación y Ctrl+D, con el mismo comportamiento.

[Captura 5]

## Interpretación de resultados

Números de `python src/evaluacion.py` sobre la semana de prueba (25 al 31 de agosto,
57.218 franjas):

| Clase | Precisión | Exhaustividad | F1 | Franjas |
|---|---|---|---|---|
| baja | 0,74 | 0,70 | 0,72 | 15.602 |
| media | 0,43 | 0,71 | 0,54 | 19.275 |
| alta | 0,60 | 0,29 | 0,39 | 22.341 |

Exactitud del árbol: 0,543. Línea base: 0,273.

Matriz de confusión (filas = clase real, columnas = clase predicha):

| | baja | media | alta |
|---|---|---|---|
| baja | 10.864 | 2.674 | 2.064 |
| media | 3.234 | 13.743 | 2.298 |
| alta | 606 | 15.297 | 6.438 |

### Por qué la exhaustividad de "alta" es baja

El árbol solo llega a *alta* por un camino: `hora <= 8.62`, `dia_semana <= 5.50` y
`es_festivo = 0`, es decir, la hora pico de la mañana (hasta la franja de las 8:30) de
lunes a sábado no festivos. Las franjas de la tarde de esos mismos días caen en
`hora > 8.62`, cuya hoja es *media*. Por eso la hora pico de la tarde, que en la
realidad es *alta*, sale como *media*: de las 22.341 franjas altas, 15.297 se predicen
como *media* y solo 6.438 como *alta* (exhaustividad 0,29). Ese mismo error explica la
precisión baja de *media* (0,43), que recibe muchas franjas que en realidad son altas.

### Por qué el tipo de estación casi no importa

Importancia de las variables:

| Variable | Importancia |
|---|---|
| `hora` | 0,398 |
| `dia_semana` | 0,317 |
| `es_festivo` | 0,256 |
| `troncal_Zona Z Av. Cali Sur` | 0,010 |
| `troncal_Zona E NQS Central` | 0,006 |
| `troncal_Zona T Ciudad Bolívar` | 0,006 |
| `troncal_Zona A Caracas` | 0,005 |
| `es_portal` | 0,003 |
| `es_transbordo` y las otras 10 troncales | 0,000 |

Hora, día y festivo suman 0,971. Las troncales suman 0,027 y `es_portal` 0,003;
`es_transbordo` vale 0. Esto viene de cómo se definió la clase: los tercios se calculan
para cada estación por separado, así que cada estación se compara consigo misma. Un
portal y una estación pequeña tienen cada uno un tercio de franjas altas, y esas franjas
caen más o menos a las mismas horas en todas. El árbol aprende ese patrón horario común,
y saber de qué tipo es la estación casi no ayuda a separar las clases.

### Por qué profundidad 4

| Profundidad | Hojas | Exactitud | F1 macro |
|---|---|---|---|
| 2 | 4 | 0,570 | 0,462 |
| 3 | 8 | 0,572 | 0,467 |
| 4 | 16 | 0,543 | 0,548 |
| 5 | 32 | 0,579 | 0,587 |
| 6 | 62 | 0,594 | 0,604 |

Por exactitud, la profundidad 4 sale peor que la 2 y la 3. Pero el árbol de profundidad
2 nunca predice *media* y el de profundidad 3 la predice en 126 de 57.218 franjas;
aciertan diciendo *alta* o *baja*. El F1 macro promedia el F1 de las tres clases y
castiga ese comportamiento: la profundidad 4 es la primera que usa las tres clases y su
F1 macro sube de 0,467 a 0,548. Las profundidades 5 y 6 siguen mejorando, pero con 32 y
62 hojas el árbol deja de poder explicarse regla por regla.
