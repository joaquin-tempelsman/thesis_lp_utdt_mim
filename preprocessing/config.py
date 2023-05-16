version = "0.09"
clases = 3
periodos_modelo = 20  # 1 año
meses_max_animales = 12 * 10  # 10 años, impacta en reproductoras
ventas_max_por_mes = 100
ventas_min_por_mes = 10
#fecha_inicio = "01/04/2019"  # este valor se usa para tomar un stock inicial, y para pasar precios desde el periodo 0 a el final del modelo
fecha_parte_diario_inicio = "01/04/2019"
sell_c1_c2_before = 37
path_parte_diario = "data/datos experimento tesis  - parte_diario completo.csv"
path_scrapped_prices_df = "data/scrapping_df3 - scrapping_df3.csv"

VENTA_DESTETE = [6, 7, 8]
VENTA_NOVILLO_VAQUILLONA = [16, 17, 18]
VENTA_PESADOS = [30, 31, 32, 33, 34, 35, 36]

peso_prom_destete = 164
peso_prom_vaquillonas = 314
peso_prom_novillitos = 367
peso_prom_vaquillonas_pesados = 433
peso_prom_novillos_pesados = 438

usd_18_04_2023 = 397.2
costos_meses_usd_c1_c2 = {
    0: (55000 /2) / usd_18_04_2023,
    6: 55000 / usd_18_04_2023,
    17: 94000 / usd_18_04_2023,
    21: 128000 / usd_18_04_2023,
}
costos_c3_mes = 12
c1_c2_over_21 = 21  # pasados los 21, para clase 1 y 2, el costo diario es el maximo dado el limite sup de meses en la funcion
multiplicador_destete = 1.2  # precio venta 20% mas que el precio del novillito
multiplicador_c3 = 0.5  # precio de venta 50% de VAQUILLONAS270

intervalos_madurez = {
    "VACAS": [37, 96, 3],
    "VAQ 1-2": [12, 17, 2],
    "VAQ. 1-2 Servicio": [12, 36, 3],
    "VAQ. 2-3": [36, 96, 3],
    "NOVILLOS": [25, 36, 1],
    "NOVILLITOS": [12, 24, 1],
    "TERNEROS": [6, 17, 1],
    "TERNERAS": [6, 11, 2],
    "OREJANO_MACHOS": [0, 5, 1],
    "OREJANO_HEMBRAS": [0, 5, 2],
}

indice_prenez = 0.9

SALES_PERIODS = {
    "venta_destete": VENTA_DESTETE,
    "venta_novillo_vaquillona": VENTA_NOVILLO_VAQUILLONA,
    "venta_pesados": VENTA_PESADOS,
}

PESOS_PROMEDIO = {
    "peso_prom_destete": peso_prom_destete,
    "peso_prom_vaquillonas": peso_prom_vaquillonas,
    "peso_prom_novillitos": peso_prom_novillitos,
    "peso_prom_vaquillonas_pesados": peso_prom_vaquillonas_pesados,
    "peso_prom_novillos_pesados": peso_prom_novillos_pesados,
}

PARAMS = {
    "version": version,
    "periodos_modelo": periodos_modelo,
    "meses_max_animales": meses_max_animales,
    "clases": clases,
    "ventas_max_por_mes": ventas_max_por_mes,
    "ventas_min_por_mes": ventas_min_por_mes,
    "fecha_parte_diario_inicio" : fecha_parte_diario_inicio,
    "fecha_parte_diario_inicio": fecha_parte_diario_inicio,
    "costos_meses_usd_c1_c2": costos_meses_usd_c1_c2,
    "costos_c3": costos_c3_mes,
    "c1_c2_over_21": c1_c2_over_21,
    "sell_c1_c2_before": sell_c1_c2_before,
    "multiplicador_destete": multiplicador_destete,
    "multiplicador_c3": multiplicador_c3,
    "SALES_PERIODS": SALES_PERIODS,
    "PESOS_PROMEDIO": PESOS_PROMEDIO,
}

# ! WARNING, this will be regenerated out when running build_model_inputs.py
# ! dont add other files here
PATH_DAT_FILES = {
    "parameters": "model_inputs/parametros.dat",
    "agosto_si": "model_inputs/agosto_si.dat",
    "agosto_no": "model_inputs/agosto_no.dat",
    "costos": "model_inputs/costos.dat",
    "momentos_venta_SI_c1_c2": "model_inputs/momentos_venta_SI_c1_c2.dat",
    "precios": "model_inputs/precios.dat",
    "stock_inicial": "model_inputs/stock_inicial.dat",
}


