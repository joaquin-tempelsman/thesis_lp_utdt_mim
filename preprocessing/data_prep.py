import math
import pandas as pd
import os
import numpy as np
import seaborn as sns
import itertools
from datetime import datetime
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
from skfda.representation.interpolation import SplineInterpolation
from skfda.representation.grid import FDataGrid
import itertools
import logging
from preprocessing.DolarNormalizer import DolarNormalizer

log = logging.getLogger("logger")


def write_line_to_file(path, line):
    with open(path, "a") as f:
        f.write(line)


def get_stock_inicial_test(PARAMS, output):
    for edad_animal, clase in itertools.product(
        range(-1, PARAMS["meses_max_animales"] + 1), range(1, PARAMS["clases"] + 1)
    ):
        if edad_animal == 1:
            stock_init = 1
        else:
            stock_init = 0

        valores = [edad_animal, clase, stock_init, "\n"]
        line = "\t".join(str(x) for x in valores)
        write_line_to_file(output, line)


def get_stock_inicial_from_parte_diario(
    FECHA_INICIO_MODELO,
    clases,
    meses_max_animales,
    parte_diario_path,
    output,
    intervalos,
):
    #### - ARMA STOCK INICIAL CON 0 STOCK PARA TODOS LOS VALORES POSIBLES

    collect_df = pd.DataFrame()
    for edad_animal, clase in itertools.product(
        range(-1, meses_max_animales + 1), range(1, clases + 1)
    ):
        collect_df = pd.concat(
            [
                collect_df,
                pd.Series({"edad": edad_animal, "clase": clase, "stock": 0})
                .to_frame()
                .T,
            ]
        )

    # LEVANTO EL PARTE DIARIO Y REEMPLAZO LOS VALORES QUE SI TENGO STOCK EN EDADES DISTRIBUIDAS DENTRO DE UN RANGO UNIFORMEMENTE
    # PARA CADA CATEOGRIA

    # DISTRIBUYE ESTOCASTICAMENTE LOS ANIMALES ENTRE LOS DOS PRIMEROVS VALORES DE LA LISTA
    # EL TERCER VALOR ES LA CLASE A LA QUE PERTENECE.
    FECHA_INICIO_MODELO = pd.to_datetime(FECHA_INICIO_MODELO, format="%d/%m/%Y")

    stock_row, parte_diario_cols = get_stock_row(parte_diario_path, FECHA_INICIO_MODELO)

    assert not stock_row.empty, f"{FECHA_INICIO_MODELO} FOR PARTE DIARIO IS EMPTY"

    df_collect_parte_diario = pd.DataFrame()

    categorias = [
        col
        for col in parte_diario_cols
        if col not in ("ESTAB.", "FECHA", "TOROS", "TORITOS", "TOTAL")
    ]

    for cat in categorias:
        if math.isnan(stock_row[cat]):
            stock_row[cat] = 0

        if cat == "VACAS":
            edades_random = truncated_normal(
                60,
                10,
                intervalos[cat][0],
                intervalos[cat][1],
                size=int(stock_row[cat].values[0]),
            ).astype(int)
        else:
            edades_random = np.random.random_integers(
                intervalos[cat][0], intervalos[cat][1], int(stock_row[cat].values[0])
            )
        data = pd.DataFrame(
            {"edad": edades_random, "clase": intervalos[cat][2], "stock": 1}
        )
        df_collect_parte_diario = pd.concat([df_collect_parte_diario, data])

    df_collect_parte_diario_agg = df_collect_parte_diario.groupby(
        ["edad", "clase"]
    ).sum()

    for index, row in df_collect_parte_diario_agg.reset_index().iterrows():
        collect_df.loc[
            (collect_df["edad"] == row.edad) & (collect_df["clase"] == row.clase),
            "stock",
        ] = row.stock

    for index, row in collect_df.iterrows():
        list_row = list(row) + ["\n"]
        line = "\t".join(str(x) for x in list_row)
        write_line_to_file(output, line)
    return stock_row


def get_precios_scrapped(fecha_inicio, input):
    df_scrapping = pd.read_csv(input)

    df_scrapping["periodo"] = round(
        (
            pd.to_datetime(df_scrapping["periodo_inicio"], format="%d/%m/%Y")
            - pd.to_datetime(fecha_inicio, format="%d/%m/%Y")
        )
        / np.timedelta64(1, "M"),
        0,
    ).astype(int)

    append_list = []
    for index, row in df_scrapping.iterrows():
        clean_row = [
            row["VAQUILLONAS270"].split(",")[2],
            row["VAQUILLONAS391"].split(",")[2],
            row["NOVILLITOS300"].split(",")[2],
            row["NOVILLITOS391"].split(",")[2],
        ]

        clean_row = [x[3:] if len(x) > 3 else x for x in clean_row]
        clean_row.append(row["periodo_inicio"])

        append_list.append(clean_row)

    df_precios = pd.DataFrame(
        data=append_list,
        columns=[
            "VAQUILLONAS270",
            "VAQUILLONAS391",
            "NOVILLITOS300",
            "NOVILLITOS391",
            "PERIODO_INICIO",
        ],
    )
    df_precios["PERIODO_INICIO"] = pd.to_datetime(
        df_precios["PERIODO_INICIO"], format="%d/%m/%Y"
    )

    cols_to_numeric = [
        "VAQUILLONAS270",
        "VAQUILLONAS391",
        "NOVILLITOS300",
        "NOVILLITOS391",
    ]
    df_precios[cols_to_numeric] = df_precios[cols_to_numeric].apply(pd.to_numeric)

    columns = ["VAQUILLONAS270", "VAQUILLONAS391", "NOVILLITOS300", "NOVILLITOS391"]

    # ! manual fix for missing values at the end of period. I give a 2% monthly increase in price
    for counter, value in enumerate(range(101, 109)):
        for col in columns:
            df_precios.loc[value, col] = round(df_precios.loc[value - 1, col] * 1.02)
        df_precios.loc[value, "PERIODO_INICIO"] = df_precios.loc[
            value - 1, "PERIODO_INICIO"
        ] + pd.DateOffset(months=1)

        df_precios["YYYYMM"] = df_precios.PERIODO_INICIO.dt.strftime("%Y%m")

    return df_precios


def plot_precios(df_precios):
    # plot precios v1 scrapping
    df_melt = df_precios.drop(columns=["YYYYMM"])
    df_melt = df_melt.melt(
        value_vars=[x for x in df_melt.columns if x != ["PERIODO_INICIO"]],
        id_vars="PERIODO_INICIO",
        var_name="categoria",
        value_name="precio_x_kg",
    )
    df_melt.sort_values(by="PERIODO_INICIO", inplace=True)
    df_melt["precio_x_kg"] = df_melt["precio_x_kg"].astype(int)
    g = sns.lineplot(
        data=df_melt, x="PERIODO_INICIO", y="precio_x_kg", hue="categoria"
    ).set_title("Precios scrapped")


def precios_scrapped_to_dat(
    df_precios,
    PARAMS,
    PATH_DAT_FILES,
    peso_prom_dict,
):
    periodos_modelo = PARAMS["periodos_modelo"]
    clases = PARAMS["clases"]
    meses_max_animales = PARAMS["meses_max_animales"]
    fecha_inicio = PARAMS["fecha_inicio"]
    path_to_file_precios = PATH_DAT_FILES["precios"]

    df_precios_cut = df_precios[
        df_precios["PERIODO_INICIO"] >= pd.to_datetime(fecha_inicio, format="%d/%m/%Y")
    ]
    df_precios_cut["periodo_mes_modelo"] = np.arange(1, len(df_precios_cut) + 1)

    # verifico que este la info de precios necesasria para todos los periodos del modelo
    assert max(df_precios_cut.periodo_mes_modelo) >= periodos_modelo

    # datos sacados de kg prom por cabeza de pagina "venta de cabezas - la cepa"
    peso_prom_destete = peso_prom_dict["peso_prom_destete"]
    peso_prom_vaquillonas = peso_prom_dict["peso_prom_vaquillonas"]
    peso_prom_novillitos = peso_prom_dict["peso_prom_novillitos"]
    peso_prom_vaquillonas_pesados = peso_prom_dict["peso_prom_vaquillonas_pesados"]
    peso_prom_novillos_pesados = peso_prom_dict["peso_prom_novillos_pesados"]

    precios_append = []
    for periodo, edad_animal, clase in itertools.product(
        range(1, periodos_modelo + 1),
        range(-1, meses_max_animales + 1),
        range(1, clases + 1),
    ):
        row = df_precios_cut.loc[df_precios_cut["periodo_mes_modelo"] == periodo]

        try:
            # destete
            if (edad_animal in [6, 7, 8]) & (clase in [1, 2]):
                if clase == 1:
                    precio = (
                        float(row["NOVILLITOS300"])
                        * peso_prom_destete
                        * PARAMS["multiplicador_destete"]
                    )
                if clase == 2:
                    precio = (
                        float(row["NOVILLITOS300"])
                        * peso_prom_destete
                        * PARAMS["multiplicador_destete"]
                    )

            # momento 1 16.5 meses
            elif (edad_animal in [16, 17, 18]) & (clase in [1, 2]):
                if clase == 1:
                    precio = float(row["VAQUILLONAS270"]) * peso_prom_vaquillonas
                if clase == 2:
                    precio = float(row["NOVILLITOS300"]) * peso_prom_novillitos

            # momento 2
            elif (edad_animal in [30, 31, 32, 33, 34, 35, 36]) & (clase in [1, 2]):
                if clase == 1:
                    precio = (
                        float(row["VAQUILLONAS391"]) * peso_prom_vaquillonas_pesados
                    )
                if clase == 2:
                    precio = float(row["NOVILLITOS391"]) * peso_prom_novillos_pesados

            # elif clase == 3 & (periodo == periodos_modelo):
            elif (clase == 3) & (edad_animal >= PARAMS["venta_c3_from"]):
                precio = (
                    int(row["VAQUILLONAS270"])
                    * peso_prom_vaquillonas
                    * PARAMS["multiplicador_c3"]
                )

            else:
                precio = 0

            precio = round(precio)

        except TypeError:
            log.info(f"ERROR  {row}, {periodo}")
            break
        # -------------------#

        valores = [periodo, edad_animal, clase, precio, "\n"]
        line = "\t".join(str(x) for x in valores)
        write_line_to_file(path_to_file_precios, line)

        # get fecha max y min en row para obtener periodo de precios mapeados
        # para en get data cortar el linieplot entre esos periodos
        precios_append.append(row["PERIODO_INICIO"].values[0])

    precios_append = pd.Series(precios_append)
    precio_min_max = {
        "fecha_min": datetime.strftime(precios_append.min(), "%d/%m/%Y"),
        "fecha_max": datetime.strftime(precios_append.max(), "%d/%m/%Y"),
    }

    return precio_min_max


def get_ventas_inicial_from_parte_diario(parte_diario_path):
    pos_cols_ventas = [x for x in range(25, 34)]
    pos_cols_ventas.extend([1])

    ventas_df = pd.read_csv(parte_diario_path, usecols=pos_cols_ventas)
    ventas_df.rename(
        columns={"MACHOS": "OREJANO_MACHOS", "HEMBRAS": "OREJANO_HEMBRAS"}, inplace=True
    )
    ventas_df = ventas_df.fillna(0)

    # limpiar casos anomalos
    ventas_df.loc[119, "FECHA"] = "11/15/2014"
    ventas_df.loc[356, "FECHA"] = "6/28/2019"
    ventas_df["FECHA"] = pd.to_datetime(ventas_df["FECHA"], format="%m/%d/%Y")
    ventas_df.rename(
        columns={
            "VENTAS": "COMENTARIO",
            "?": "SIN_ASIGNAR",
            "vacas": "VACAS",
            "vaquillonas": "VAQUILLONAS270",
            "novillos": "NOVILLITOS391",
            "novillitos": "NOVILLITOS300",
            "toros": "TOROS",
            "terneros": "TERNEROS_DESTETE",
            "terneras": "TERNERAS_DESTETE",
        },
        inplace=True,
    )

    return ventas_df


def get_precios_del_periodo(periodo, df_precios):
    closest_price = abs((df_precios.PERIODO_INICIO - periodo)).sort_values(
        ascending=True
    )
    if closest_price[closest_price.index[0]] > pd.Timedelta("15 days"):
        log.debug(f"WARNING: diferencia de precio mayor a 15 dias for {periodo}")
    precios_periodo = df_precios.iloc[closest_price.index[0]]

    return precios_periodo


def clear_model_inputs(file_paths):
    for file in file_paths.values():
        if os.path.exists(file):
            os.remove(file)


def costs_to_dat_test(PATH_DAT_FILES, periodos_modelo, meses_max_animales, clases):
    collect_costos = []

    with open(PATH_DAT_FILES["costos"], "w") as f:
        for periodo, edad_animal, clase in itertools.product(
            range(1, periodos_modelo + 1),
            range(-1, meses_max_animales + 1),
            range(1, clases + 1),
        ):
            # a mayor edad del animal, el impacto es positivo pero decreciente en funcion del tiempo
            # a medida que avanzan los periodos, es menos costoso mantener a un animal
            costo = 1 + edad_animal * 0.25

            if math.isinf(costo) | math.isnan(costo):
                costo = 1
            # else:
            if clase == 3:
                costo = 0

            # ! WARNING
            costo = 0
            valores = [periodo, edad_animal, clase, costo, "\n"]
            line = "\t".join(str(x) for x in valores)
            f.write(line)

            # plot costos
            collect_costos.append(
                {
                    "periodo": periodo,
                    "costo": costo,
                    "edad": edad_animal,
                    "clase": clase,
                }
            )

    df_costos = pd.DataFrame(collect_costos)

    return df_costos


def get_interplolator(PARAMS, output_plot_path=False):
    DataGrid = FDataGrid(
        list(PARAMS["costos_meses_usd_c1_c2_pre_norm"].values()),
        list(PARAMS["costos_meses_usd_c1_c2_pre_norm"].keys()),
    )

    # Plot the total cost on the primary y-axis
    DataGrid.interpolation = SplineInterpolation(
        interpolation_order=3,
        monotone=True,
    )
    monthly_cost = DataGrid.derivative()

    log.info("save accumulated costs to PARAMS")

    # adding the intercept of the non derivative base function
    PARAMS["costos_meses_usd_c1_c2"][6] = float(
        monthly_cost.evaluate(eval_points=[x for x in range(7)]).sum()
        + DataGrid.evaluate(0)
    )
    PARAMS["costos_meses_usd_c1_c2"][17] = float(
        monthly_cost.evaluate(eval_points=[x for x in range(18)]).sum()
        + DataGrid.evaluate(0)
    )
    PARAMS["costos_meses_usd_c1_c2"][21] = float(
        monthly_cost.evaluate(eval_points=[x for x in range(22)]).sum()
        + DataGrid.evaluate(0)
    )
    PARAMS["costos_meses_usd_c1_c2"]["intercept"] = float(DataGrid.evaluate(0))
    log.info(PARAMS["costos_meses_usd_c1_c2"])

    if output_plot_path:
        fig, ax1 = plt.subplots()
        DataGrid.plot(axes=ax1, label="accumulated cost curve")
        DataGrid.scatter(axes=ax1, c="C1")
        ax1.set_xlabel("months")
        ax1.set_ylabel("accumulated cost")

        # Plot the monthly cost on the secondary y-axis
        ax2 = ax1.twinx()
        monthly_cost.plot(axes=ax2, label="monthly cost curve", c="C6")
        ax2.set_ylabel("monthly cost")

        # Show the legend
        fig.legend()

        fig.savefig(output_plot_path, dpi=300, bbox_inches="tight")

    return monthly_cost


def get_month_cost(periods: list, interpolator, PARAMS):
    cost = (
        interpolator.evaluate(
            eval_points=periods,  # max cost for c1 and c2
        ).sum()
        + PARAMS["costos_meses_usd_c1_c2"]["intercept"]
    )
    return float(cost)


def costs_to_dat_realistic(Interpolator, PATH_DAT_FILES, PARAMS):
    with open(PATH_DAT_FILES["costos"], "w") as f:
        for periodo, edad_animal, clase in itertools.product(
            range(1, PARAMS["periodos_modelo"] + 1),
            range(-1, PARAMS["meses_max_animales"] + 1),
            range(1, PARAMS["clases"] + 1),
        ):
            if edad_animal == -1:
                costo = 0
            elif (clase == 3) & (edad_animal > 12):
                costo = PARAMS["c3_costs"]["monthly_cost_over_12"]
            elif edad_animal == 0:
                costo = (
                    Interpolator.evaluate(0)
                    + PARAMS["costos_meses_usd_c1_c2"]["intercept"]
                )

            elif edad_animal > 21:
                costo = 0 # este costo es cero porque el engorde ya se pago para el modelo

            else:
                costo = Interpolator.evaluate(eval_points=[edad_animal]).min()

            costo = max(0, costo)

            valores = [periodo, edad_animal, clase, float(costo), "\n"]
            line = "\t".join(str(x) for x in valores)
            f.write(line)


def delete_files(file_paths):
    for file in file_paths.values():
        if os.path.exists(file):
            os.remove(file)


def write_params_file(PATH_DAT_FILES, PARAMS):
    # Write parameters to file
    with open(PATH_DAT_FILES["parameters"], "w") as f:
        f.write("model params\n")
        f.write(f"max_periods {PARAMS['periodos_modelo']}\n")
        f.write(f"max_age_allowed {PARAMS['meses_max_animales']}\n")
        f.write(f"max_sell_qty_monthly {PARAMS['ventas_max_por_mes']}\n")
        f.write(f"min_sell_qty_monthly {PARAMS['ventas_min_por_mes']}\n")
        f.write(f"sell_c1_c2_before {PARAMS['sell_c1_c2_before']}\n")
        f.write(f"mantain_stock_c3_at_end {PARAMS['mantain_c3_stock']}\n")
        f.write(f"end_c3_stock_as {PARAMS['c3_stock_at_end']}\n")

    # Write August birth data to file
    with open(PATH_DAT_FILES["agosto_si"], "w") as f_yes, open(
        PATH_DAT_FILES["agosto_no"], "w"
    ) as f_no:
        start_date = pd.to_datetime(PARAMS["fecha_inicio"], format="%d/%m/%Y")

        date_dict = {
            (start_date + pd.DateOffset(months=i)).strftime("%Y-%m-%d"): (i, 1)
            if (start_date + pd.DateOffset(months=i)).month == 8
            else (i, 0)
            for i in range(PARAMS["periodos_modelo"] + 1)
        }

        for key, value in date_dict.items():
            if value[1] == 1:
                f_yes.write(f"{value[0]}\n")
            else:
                f_no.write(f"{value[0]}\n")

    SALES_PERIODS = PARAMS["SALES_PERIODS"]

    # Write sale periods data to file
    with open(PATH_DAT_FILES["momentos_venta_SI_c1_c2"], "w") as f:
        venta_destete = SALES_PERIODS["venta_destete"]
        venta_novillo_vaquillona = SALES_PERIODS["venta_novillo_vaquillona"]
        venta_pesados = SALES_PERIODS["venta_pesados"]
        venta_all = venta_destete + venta_novillo_vaquillona + venta_pesados
        for mes in [
            x for x in range(0, PARAMS["meses_max_animales"]) if x in venta_all
        ]:
            f.write(f"{mes}\n")


def write_costs_file_test(PATH_DAT_FILES, periodos_modelo, meses_max_animales, clases):
    collect_costos = []

    with open(PATH_DAT_FILES["costos"], "w") as f:
        for periodo, edad_animal, clase in itertools.product(
            range(1, periodos_modelo + 1),
            range(-1, meses_max_animales + 1),
            range(1, clases + 1),
        ):
            # a mayor edad del animal, el impacto es positivo pero decreciente en funcion del tiempo
            # a medida que avanzan los periodos, es menos costoso mantener a un animal
            costo = 1 + edad_animal * 0.25

            if math.isinf(costo) | math.isnan(costo):
                costo = 1
            # else:
            if clase == 3:
                costo = 0

            # ! WARNING
            costo = 0
            valores = [periodo, edad_animal, clase, costo, "\n"]
            line = "\t".join(str(x) for x in valores)
            f.write(line)

            # plot costos
            collect_costos.append(
                {
                    "periodo": periodo,
                    "costo": costo,
                    "edad": edad_animal,
                    "clase": clase,
                }
            )

    df_costos = pd.DataFrame(collect_costos)

    return df_costos


def append_daily_income_and_cost(
    df_ventas, df_precios, PARAMS, PESOS_PROMEDIO, costs_interpolator
):
    df_ventas = df_ventas.loc[
        (df_ventas.FECHA >= PARAMS["fecha_inicio"])
        & (df_ventas.FECHA <= PARAMS["fecha_fin_ejercicio"])
    ]
    for index, row in df_ventas.iterrows():
        precios = get_precios_del_periodo(row.FECHA, df_precios)

        # SALES_EARNINGS
        earned_VAQUILLONAS270 = (
            row["VAQUILLONAS270"]
            * precios["VAQUILLONAS270"]
            * PESOS_PROMEDIO["peso_prom_vaquillonas"]
        )
        earned_NOVILLITOS391 = (
            row["NOVILLITOS391"]
            * precios["NOVILLITOS391"]
            * PESOS_PROMEDIO["peso_prom_novillos_pesados"]
        )
        earned_NOVILLITOS300 = (
            row["NOVILLITOS300"]
            * precios["NOVILLITOS300"]
            * PESOS_PROMEDIO["peso_prom_novillitos"]
        )
        # earned_TOROS = row['TOROS'] * precios['TOROS']

        earned_VACAS = row["VACAS"] * (
            precios["VAQUILLONAS270"] * 0.5 * PESOS_PROMEDIO["peso_prom_vaquillonas"]
        )

        earned_TERNEROS_DESTETE = (
            row["TERNEROS_DESTETE"]
            * precios["NOVILLITOS300"]
            * PARAMS["multiplicador_destete"]
            * PESOS_PROMEDIO["peso_prom_destete"]
        )
        earned_TERNERAS_DESTETE = (
            row["TERNERAS_DESTETE"]
            * precios["NOVILLITOS300"]
            * PARAMS["multiplicador_destete"]
            * PESOS_PROMEDIO["peso_prom_destete"]
        )

        VENTA_TOT_DIA = (
            earned_VAQUILLONAS270
            + earned_NOVILLITOS391
            + earned_NOVILLITOS300
            + earned_VACAS
            # +    earned_TOROS
            + earned_TERNEROS_DESTETE
            + earned_TERNERAS_DESTETE
        )

        df_ventas.loc[index, "VENTA_VALOR"] = VENTA_TOT_DIA

        # SALES COSTS
        cost_VAQUILLONAS270 = (
            row["VAQUILLONAS270"] * PARAMS["costos_meses_usd_c1_c2"][17]
        )
        cost_NOVILLITOS391 = row["NOVILLITOS391"] * PARAMS["costos_meses_usd_c1_c2"][21]

        cost_NOVILLITOS300 = row["NOVILLITOS300"] * PARAMS["costos_meses_usd_c1_c2"][17]

        cost_VACAS = row["VACAS"] * get_month_cost(
            [x for x in range(13)] + [12] * (24),
            costs_interpolator,
            PARAMS,
        )

        # cost_TOROS = row['TOROS'] *

        cost_TERNEROS_DESTETE = (
            row["TERNEROS_DESTETE"] * PARAMS["costos_meses_usd_c1_c2"][6]
        )
        cost_TERNERAS_DESTETE = (
            row["TERNERAS_DESTETE"] * PARAMS["costos_meses_usd_c1_c2"][6]
        )

        COSTO_TOT_DIA = (
            cost_VAQUILLONAS270
            + cost_NOVILLITOS391
            + cost_NOVILLITOS300
            + cost_VACAS
            # +    cost_TOROS
            + cost_TERNEROS_DESTETE
            + cost_TERNERAS_DESTETE
        )

        df_ventas.loc[index, "COSTO_VALOR"] = float(COSTO_TOT_DIA)

    df_ventas["MARGIN"] = df_ventas["VENTA_VALOR"] - df_ventas["COSTO_VALOR"]

    df_ventas.to_csv('test.csv')

    return df_ventas


def prices_to_usd_b(df_prices_ars, usd_b_path, cols_to_normalize, n=7):
    dln = DolarNormalizer(usd_b_path)

    log.info(f"using mean {n} days for USD_B normalization")
    df_prices_ars["usd_b"] = df_prices_ars.apply(
        lambda x: dln.mean_last_n_days(x["PERIODO_INICIO"], n), axis=1
    )

    df_prices_ars[cols_to_normalize] = df_prices_ars[cols_to_normalize].div(
        df_prices_ars["usd_b"], axis=0
    )

    return df_prices_ars


def get_stock_row(parte_diario_path, FECHA_INICIO_MODELO):
    df_stock_parte = pd.read_csv(parte_diario_path, usecols=[x for x in range(0, 15)])
    df_stock_parte.rename(
        columns={"MACHOS": "OREJANO_MACHOS", "HEMBRAS": "OREJANO_HEMBRAS"}, inplace=True
    )

    # limpiar casos anomalos
    df_stock_parte.loc[119, "FECHA"] = "11/15/2014"
    df_stock_parte.loc[356, "FECHA"] = "6/28/2019"

    df_stock_parte["FECHA"] = pd.to_datetime(df_stock_parte["FECHA"], format="%m/%d/%Y")

    #### - LEER STOCK DIARIO Y REEMPLAZAR STOCK INICIAL CON VALORES REALES - ####
    row = df_stock_parte.loc[df_stock_parte["FECHA"] == FECHA_INICIO_MODELO]

    return row, df_stock_parte.columns


def quote_stock(prices, stock_row, PESOS_PROMEDIO, costs_interpolator, PARAMS):
    ix = stock_row.index[0]
    stock_row = stock_row.to_dict()

    # QTY * PRICE * AVG_WEIGHT
    VACAS_sell = int(stock_row["VACAS"][ix]) * (
        prices["VAQUILLONAS270"] * 0.5 * PESOS_PROMEDIO["peso_prom_vaquillonas"]
    )
    VAQ12_sell = int(stock_row["VAQ 1-2"][ix]) * (
        prices["VAQUILLONAS270"] * PESOS_PROMEDIO["peso_prom_vaquillonas"]
    )
    VAQ12s_sell = int(stock_row["VAQ. 1-2 Servicio"][ix]) * (
        prices["VAQUILLONAS270"] * 0.5 * PESOS_PROMEDIO["peso_prom_vaquillonas"]
    )
    VAQ23_sell = int(stock_row["VAQ. 2-3"][ix]) * (
        prices["VAQUILLONAS270"] * 0.5 * PESOS_PROMEDIO["peso_prom_vaquillonas"]
    )
    NOVILLOS_sell = int(stock_row["NOVILLOS"][ix]) * (
        prices["NOVILLITOS391"] * PESOS_PROMEDIO["peso_prom_novillos_pesados"]
    )
    NOVILLITOS_sell = int(stock_row["NOVILLITOS"][ix]) * (
        prices["NOVILLITOS300"] * PESOS_PROMEDIO["peso_prom_novillitos"]
    )

    TERNEROS_sell = int(stock_row["TERNEROS"][ix]) * (
        prices["NOVILLITOS300"]
        * PARAMS["multiplicador_destete"]
        * PESOS_PROMEDIO["peso_prom_destete"]
    )
    TERNERAS_sell = int(stock_row["TERNERAS"][ix]) * (
        prices["NOVILLITOS300"]
        * PARAMS["multiplicador_destete"]
        * PESOS_PROMEDIO["peso_prom_destete"]
    )

    # ! assumption
    OREJANO_MACHOS_sell = stock_row["OREJANO_MACHOS"][ix] * (
        prices["NOVILLITOS300"]
        * PARAMS["multiplicador_destete"]
        * PESOS_PROMEDIO["peso_prom_destete"]
    )
    OREJANO_HEMBRAS_sell = stock_row["OREJANO_HEMBRAS"][ix] * (
        prices["NOVILLITOS300"]
        * PARAMS["multiplicador_destete"]
        * PESOS_PROMEDIO["peso_prom_destete"]
    )

    # COST
    VACAS_cost = (get_month_cost(
        [x for x in range(13)],
        costs_interpolator,
        PARAMS,
    ) + PARAMS['c3_costs']['monthly_cost_over_12'] * 48) * int(stock_row["VACAS"][ix])

    VAQ12_cost =  PARAMS["costos_meses_usd_c1_c2"][17] * int(stock_row["VAQ 1-2"][ix])

    VAQ12s_cost = (get_month_cost(
        [x for x in range(13)],
        costs_interpolator,
        PARAMS,
    ) + PARAMS['c3_costs']['monthly_cost_over_12'] * 18) * int(stock_row["VAQ. 1-2 Servicio"][ix])

    VAQ23_cost = (get_month_cost(
        [x for x in range(13)],
        costs_interpolator,
        PARAMS,
    ) + PARAMS['c3_costs']['monthly_cost_over_12'] * 24) * int(stock_row["VAQ. 2-3"][ix])

    NOVILLOS_cost = PARAMS["costos_meses_usd_c1_c2"][21] * int(
        stock_row["NOVILLOS"][ix]
    )
    NOVILLITOS_cost = PARAMS["costos_meses_usd_c1_c2"][17] * int(
        stock_row["NOVILLITOS"][ix]
    )
    TERNEROS_cost = PARAMS["costos_meses_usd_c1_c2"][6] * int(stock_row["TERNEROS"][ix])
    TERNERAS_cost = PARAMS["costos_meses_usd_c1_c2"][6] * int(stock_row["TERNERAS"][ix])
    OREJANO_MACHOS_cost = get_month_cost(
        [x for x in range(6)], costs_interpolator, PARAMS
    ) * int(stock_row["OREJANO_MACHOS"][ix])
    OREJANO_HEMBRAS_cost = get_month_cost(
        [x for x in range(6)], costs_interpolator, PARAMS
    ) * int(stock_row["OREJANO_HEMBRAS"][ix])

    categories = [
        ("VACAS", VACAS_sell, VACAS_cost, int(stock_row["VACAS"][ix])),
        ("VAQ 1-2", VAQ12_sell, VAQ12_cost, int(stock_row["VAQ 1-2"][ix])),
        (
            "VAQ. 1-2 Servicio",
            VAQ12s_sell,
            VAQ12s_cost,
            int(stock_row["VAQ. 1-2 Servicio"][ix]),
        ),
        ("VAQ. 2-3", VAQ23_sell, VAQ23_cost, int(stock_row["VAQ. 2-3"][ix])),
        ("NOVILLOS", NOVILLOS_sell, NOVILLOS_cost, int(stock_row["NOVILLOS"][ix])),
        (
            "NOVILLITOS",
            NOVILLITOS_sell,
            NOVILLITOS_cost,
            int(stock_row["NOVILLITOS"][ix]),
        ),
        ("TERNEROS", TERNEROS_sell, TERNEROS_cost, int(stock_row["TERNEROS"][ix])),
        ("TERNERAS", TERNERAS_sell, TERNERAS_cost, int(stock_row["TERNERAS"][ix])),
        (
            "OREJANO_MACHOS",
            OREJANO_MACHOS_sell,
            OREJANO_MACHOS_cost,
            int(stock_row["OREJANO_MACHOS"][ix]),
        ),
        (
            "OREJANO_HEMBRAS",
            OREJANO_HEMBRAS_sell,
            OREJANO_HEMBRAS_cost,
            int(stock_row["OREJANO_HEMBRAS"][ix]),
        ),
    ]

    df_final_stock_value = pd.DataFrame(
        categories, columns=["cat", "sell_value", "cost", "qty"]
    )
    df_final_stock_value["revenue"] = (
        df_final_stock_value["sell_value"] - df_final_stock_value["cost"]
    )
    
    df_final_stock_value['avg_cost'] = df_final_stock_value['cost'] / df_final_stock_value['qty']

    return df_final_stock_value


def business_exercise_value(
    df_ventas, df_precios, PARAMS, path_parte_diario, PESOS_PROMEDIO, costs_interpolator
):
    fecha_fin_ejercicio = pd.to_datetime(
        PARAMS["fecha_fin_ejercicio"], format="%d/%m/%Y"
    )

    ## -- sales to value -- ##
    df_ventas_cut = df_ventas[
        (df_ventas["FECHA"] >= PARAMS["fecha_inicio"])
        & (df_ventas["FECHA"] <= fecha_fin_ejercicio)
    ]

    ## -- stock to value -- ##
    init_date = fecha_fin_ejercicio
    end_stock_row = None

    # iterate day by day until data exist in stock diario file
    while end_stock_row is None or end_stock_row[0].empty:
        end_stock_row = get_stock_row(path_parte_diario, fecha_fin_ejercicio)
        fecha_fin_ejercicio = fecha_fin_ejercicio + relativedelta(days=1)
    end_stock_row = end_stock_row[0].fillna(0)

    assert not end_stock_row.empty, f"{fecha_fin_ejercicio} FOR PARTE DIARIO IS EMPTY"

    log.info(
        f"moved {(fecha_fin_ejercicio - init_date).days} from {init_date} to find data in stock diario file"
    )

    prices_final_period = get_precios_del_periodo(
        fecha_fin_ejercicio, df_precios
    ).to_dict()

    df_final_stock_value = quote_stock(
        prices_final_period, end_stock_row, PESOS_PROMEDIO, costs_interpolator, PARAMS
    )

    # get stock value + sales value grand total
    grand_total = df_final_stock_value["revenue"].sum() + df_ventas_cut["MARGIN"].sum()

    log.info(
        f"""
    BUSINESS stock value: {df_final_stock_value['revenue'].sum()}
    BUSINESS sales value: {df_ventas_cut['MARGIN'].sum()}
    BUSINESS grand total: {grand_total}
             """
    )

    output_dict = {
        "stock_cost_sum": df_final_stock_value["cost"].sum(),
        "stock_revenue_sum": df_final_stock_value["revenue"].sum(),
        'stock_sell_sum': df_final_stock_value["sell_value"].sum(),
        "sales_margin": df_ventas_cut["MARGIN"].sum(),
        "grand_total": grand_total,
    }

    return output_dict, df_final_stock_value


def delete_log_files(path):
    # Get a list of all files in the specified path
    files = os.listdir(path)

    # Iterate over each file in the path
    for file_name in files:
        file_path = os.path.join(path, file_name)

        # Delete the log file
        os.remove(file_path)


def apply_contant_prices(df_precios):
    cols = {
        "VAQUILLONAS270": 1.75,
        "VAQUILLONAS391": 1.625,
        "NOVILLITOS300": 1.875,
        "NOVILLITOS391": 1.81,
    }

    for index, row in df_precios.iterrows():
        for col in cols.keys():
            df_precios.loc[index, col] = cols[col]

    return df_precios


def truncated_normal(mean, std, lower_bound, upper_bound, size=1):
    samples = []
    while len(samples) < size:
        x = np.random.normal(mean, std)
        if lower_bound <= x <= upper_bound:
            samples.append(x)
    return np.array(samples)
