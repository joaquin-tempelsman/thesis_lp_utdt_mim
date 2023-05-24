import logging

log = logging.getLogger('logger')
from preprocessing.data_prep import (
    get_precios_scrapped,
    prices_to_usd_b,
    get_ventas_inicial_from_parte_diario,
    append_daily_income_and_cost,
    business_exercise_value,
    get_interplolator,
)

def business_variant(PARAMS, PESOS_PROMEDIO, path_parte_diario, path_scrapped_prices_df):

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

    ### PROCESS BUSINESS SALES TO BUILD UP EXPERIMENT ###
    log.info(f"get business sales qty per category during the exercise")
    df_ventas = get_ventas_inicial_from_parte_diario(parte_diario_path=path_parte_diario)


    # iteramos por cada venta en el parte diario y la pesificamos usando el precio mas cercano
    # en el dataset de precios scrappeados. Obtenemos una nueva columna en df_ventas con la venta en usd para ese dia y el costo de esa venta
    log.info(f"add cost and income to business sales")
    df_ventas = append_daily_income_and_cost(df_ventas, df_precios, PARAMS, PESOS_PROMEDIO)

    costs_interpolator = get_interplolator(PARAMS, output_plot_path=None)

    log.info(f"combine sales and final stock value to get final business value")
    business_grand_total_dict = business_exercise_value(
        df_ventas, df_precios, PARAMS, path_parte_diario, PESOS_PROMEDIO, costs_interpolator
    )

    return business_grand_total_dict