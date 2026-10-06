# Pruebas

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

## Prueba manual del programa

`python src/main.py` se probó con entradas inválidas (letras en vez de números, día 40,
hora 7:10, estación inexistente, texto vacío, opción de menú desconocida y
Ctrl+D). En todos los casos muestra un mensaje y vuelve al menú, o sale sin error.
