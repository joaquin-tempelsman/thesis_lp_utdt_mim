from preprocessing.build_data_modules import *
from preprocessing.config import *
import logging
import warnings
warnings.filterwarnings("ignore")


log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
fh = logging.FileHandler('test.log', mode='w', encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)



COST_TEST = False
INITIAL_STOCK_TEST = False


PARAMS['fecha_fin_ejercicio'] = pd.to_datetime(PARAMS['fecha_inicio'], format='%d/%m/%Y')  + relativedelta(months=+PARAMS['periodos_modelo'])
log.info(f"experiment from {PARAMS['fecha_inicio']} to {PARAMS['fecha_fin_ejercicio']}")

log.info(f"cleaning .dat files from {PATH_DAT_FILES}")
clear_model_inputs(PATH_DAT_FILES)

## LP SETTINGS ##
# [max_periods, max_age_allowed, max_sell_qty_monthlY, ...]
log.info(f"creating parameters.dat file")
write_params_file(PATH_DAT_FILES, PARAMS, SALES_PERIODS)

### COSTS ###

if COST_TEST:
    log.info(f"building costs.dat test mode ON")
    df_cost_plot = costs_to_dat_test(
        PATH_DAT_FILES,
        PARAMS["periodos_modelo"],
        PARAMS["meses_max_animales"],
        PARAMS["clases"],
    )
else:
    log.info(f"building costs.dat realistic")
    costs_interpolator = get_interplolator(PARAMS, output_plot_path=None)
    costs_to_dat_realistic(costs_interpolator, PATH_DAT_FILES, PARAMS)

### PRICES ###
log.info(f"getting prices from historical scrapped data")
df_precios = get_precios_scrapped(
    fecha_inicio=PARAMS["fecha_inicio"], input=path_scrapped_prices_df
)

log.info(f"prices to USD B")
df_precios = prices_to_usd_b(
    df_prices_ars=df_precios,
    usd_b_path="data/usd_b_fill.csv",
    cols_to_normalize=[
        "VAQUILLONAS270",
        "VAQUILLONAS391",
        "NOVILLITOS300",
        "NOVILLITOS391",
    ],
)

log.info(f"writing prices.dat file")
precios_scrapped_to_dat(
    df_precios,
    PARAMS,
    PATH_DAT_FILES,
    PESOS_PROMEDIO,
)

### INITIAL STOCK ###

if INITIAL_STOCK_TEST:
    log.info(f"building stock_inicial.dat test mode ON")
    get_stock_inicial_test(PARAMS, PATH_DAT_FILES["stock_inicial"])

else:
    log.info(f"building stock_inicial.dat realistic")
    initial_stock_row = get_stock_inicial_from_parte_diario(
        PARAMS["fecha_parte_diario_inicio"],
        PARAMS["clases"],
        PARAMS["meses_max_animales"],
        parte_diario_path=path_parte_diario,
        output=PATH_DAT_FILES["stock_inicial"],
        intervalos=intervalos_madurez,
    )
    log.info(f"get initial stock COST to add it to business variant for comparison")
    # get initial stock cost only (no income)
    prices_initial_period = get_precios_del_periodo(pd.to_datetime(fecha_inicio, format='%d/%m/%Y'), df_precios).to_dict()
    initial_stock_cost = quote_stock(prices_initial_period, initial_stock_row, PESOS_PROMEDIO, costs_interpolator)['cost'].sum()
    

### PROCESS BUSINESS SALES TO BUILD UP EXPERIMENT ###
log.info(f"get business sales qty per category during the exercise")
df_ventas = get_ventas_inicial_from_parte_diario(parte_diario_path=path_parte_diario)


# iteramos por cada venta en el parte diario y la pesificamos usando el precio mas cercano
# en el dataset de precios scrappeados. Obtenemos una nueva columna en df_ventas con la venta en usd para ese dia y el costo de esa venta
log.info(f"add cost and income to business sales")
df_ventas = append_daily_income_and_cost(df_ventas, df_precios, PARAMS, PESOS_PROMEDIO)

log.info(f"combine sales and final stock value to get final business value")
business_grand_total = business_exercise_value(df_ventas, df_precios, PARAMS, path_parte_diario, PESOS_PROMEDIO, costs_interpolator)


log.info(f"MODEL initial stock cost: {initial_stock_cost}")