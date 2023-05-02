from utils.build_data_modules import *
from utils.config import *

import warnings

warnings.filterwarnings("ignore")

COST_TEST = True
INITIAL_STOCK_TEST = True

delete_files(PATHS)

write_params_file(PATHS, PARAMS, SALES_PERIODS)

if COST_TEST:
    df_cost_plot = costs_to_dat_test(
        PATHS, PARAMS["periodos_modelo"], PARAMS["meses_max_animales"], PARAMS["clases"]
    )
else:
    costs_interpolator = get_interplolator(
        PARAMS, output_plot_path="data/realistic_costs.png"
    )
    costs_to_dat_realistic(costs_interpolator, PATHS, PARAMS)


df_precios = get_precios_scrapped(
    fecha_inicio=PARAMS["fecha_inicio"], input="data/scrapping_df3 - scrapping_df3.csv"
)

precios_scrapped_to_dat(
    df_precios,
    periodos_modelo=PARAMS["periodos_modelo"],
    clases=PARAMS["clases"],
    meses_max_animales=PARAMS["meses_max_animales"],
    peso_prom_dict=PESOS_PROMEDIO,
    path_to_file_precios=PATHS["precios"],
    fecha_inicio=PARAMS["fecha_inicio"],
)

if INITIAL_STOCK_TEST:
    get_stock_inicial_test(PARAMS, PATHS["stock_inicial"])

else:
    get_stock_inicial_from_parte_diario(
        PARAMS["fecha_parte_diario_inicio"],
        PARAMS["clases"],
        PARAMS["meses_max_animales"],
        parte_diario_path="data/datos experimento tesis  - parte_diario completo.csv",
        output=PATHS["stock_inicial"],
        intervalos=intervalos_madurez,
    )


df_ventas = get_ventas_inicial_from_parte_diario(
    parte_diario_path="data/datos experimento tesis  - parte_diario completo.csv"
)


# iteramos por cada venta en el parte diario y la pesificamos usando el precio mas cercano
# en el dataset de precios scrappeados. Obtenemos una nueva columna en df_ventas con la venta en pesos para ese dia
df_ventas = calculate_daily_sales(df_ventas, df_precios)
df_ventas.to_csv("data/ventas_pesos.csv")
