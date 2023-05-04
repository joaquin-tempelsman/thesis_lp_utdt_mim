import math
import pandas as pd
import os
import numpy as np
import seaborn as sns
import itertools
from datetime import datetime
from matplotlib import pyplot as plt
from skfda.representation.interpolation import SplineInterpolation
from skfda.representation.grid import FDataGrid
import itertools

from preprocessing.DolarNormalizer import DolarNormalizer



def write_line_to_file(path, line):
    with open(path, "a") as f:
        f.write(line)

def get_stock_inicial_test(PARAMS, output):
    
    for edad_animal, clase in itertools.product(
        range(-1, PARAMS['meses_max_animales'] + 1), range(1, PARAMS['clases'] + 1)
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

    df_stock_parte = pd.read_csv(parte_diario_path, usecols=[x for x in range(0, 15)])
    df_stock_parte.rename(
        columns={"MACHOS": "OREJANO_MACHOS", "HEMBRAS": "OREJANO_HEMBRAS"}, inplace=True
    )
    categorias = [
        col
        for col in df_stock_parte.columns
        if col not in ("ESTAB.", "FECHA", "TOROS", "TORITOS", "TOTAL")
    ]

    # limpiar casos anomalos
    df_stock_parte.loc[119, "FECHA"] = "11/15/2014"
    df_stock_parte.loc[356, "FECHA"] = "6/28/2019"

    df_stock_parte["FECHA"] = pd.to_datetime(df_stock_parte["FECHA"], format="%m/%d/%Y")

    #### - LEER STOCK DIARIO Y REEMPLAZAR STOCK INICIAL CON VALORES REALES - ####
    row = df_stock_parte.loc[df_stock_parte["FECHA"] == FECHA_INICIO_MODELO]

    df_collect_parte_diario = pd.DataFrame()
    for cat in categorias:
        if math.isnan(row[cat]):
            row[cat] = 0
        edades_random = np.random.random_integers(
            intervalos[cat][0], intervalos[cat][1], int(row[cat].values[0])
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
        row = list(row) + ["\n"]
        line = "\t".join(str(x) for x in row)
        write_line_to_file(output, line)


def get_precios_scrapped(fecha_inicio, input="scrapping_df3 - scrapping_df3.csv"):
    df_scrapping = pd.read_csv(input)

    df_scrapping["periodo"] = round(
        (pd.to_datetime(df_scrapping["periodo_inicio"]) - pd.to_datetime(fecha_inicio))
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
    df_precios["PERIODO_INICIO"] = pd.to_datetime(df_precios["PERIODO_INICIO"])

    cols_to_numeric = [
        "VAQUILLONAS270",
        "VAQUILLONAS391",
        "NOVILLITOS300",
        "NOVILLITOS391",
    ]
    df_precios[cols_to_numeric] = df_precios[cols_to_numeric].apply(pd.to_numeric)
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
    periodos_modelo,
    clases,
    meses_max_animales,
    peso_prom_dict,
    path_to_file_precios,
    fecha_inicio,
):
    df_precios_cut = df_precios[
        df_precios["PERIODO_INICIO"] >= pd.to_datetime(fecha_inicio)
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
            if edad_animal in [6, 7, 8]:
                if clase == 1:
                    precio = float(row["VAQUILLONAS270"]) * peso_prom_destete * 1.15
                if clase == 2:
                    precio = float(row["NOVILLITOS300"]) * peso_prom_destete * 1.15

            # momento 1 16.5 meses
            elif edad_animal in [16, 17, 18]:
                if clase == 1:
                    precio = float(row["VAQUILLONAS270"]) * peso_prom_vaquillonas
                if clase == 2:
                    precio = float(row["NOVILLITOS300"]) * peso_prom_novillitos

            # momento 2
            elif edad_animal in [30, 31, 32, 33, 34, 35, 36]:
                if clase == 1:
                    precio = float(row["VAQUILLONAS391"]) * peso_prom_vaquillonas_pesados
                if clase == 2:
                    precio = float(row["NOVILLITOS391"]) * peso_prom_novillos_pesados

            else:
                precio = 0

            # clase reproductora toma precio por kilo 50% de vaquiillonas y solo valua al final del juego
            if (clase == 3) & (periodo == periodos_modelo):
                precio = int(row["VAQUILLONAS270"]) * peso_prom_vaquillonas * 0.5

            precio = round(precio)

        except TypeError:
            print("ERROR", row, periodo)
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
        print(f"WARNING: diferencia de precio mayor a 15 dias for {periodo}")
    precios_periodo = df_precios.iloc[closest_price.index[0]]

    return precios_periodo

def clear_model_inputs(file_paths):
    for file in file_paths.values():
        if os.path.exists(file):
            os.remove(file)


def write_params_file(PATHS, PARAMS, SALES_PERIODS):
    # Write parameters to file
    with open(PATHS["parameters"], "w") as f:
        f.write("model params\n")
        f.write(f"max_periods {PARAMS['periodos_modelo']}\n")
        f.write(f"max_age_allowed {PARAMS['meses_max_animales']}\n")
        f.write(f"max_sell_qty_monthly {PARAMS['ventas_max_por_mes']}\n")

    # Write August birth data to file
    with open(PATHS["agosto_si"], "w") as f_yes, open(PATHS["agosto_no"], "w") as f_no:
        num = 8
        for semanas in range(PARAMS["periodos_modelo"] + 1):
            if semanas % num == 0:
                f_yes.write(f"{semanas}\n")
                num += 8
            else:
                f_no.write(f"{semanas}\n")

    # Write sale periods data to file
    with open(PATHS["momentos_venta_SI_c1_c2"], "w") as f:
        venta_destete = SALES_PERIODS["venta_destete"]
        venta_novillo_vaquillona = SALES_PERIODS["venta_novillo_vaquillona"]
        venta_pesados = SALES_PERIODS["venta_pesados"]
        venta_all = venta_destete + venta_novillo_vaquillona + venta_pesados
        for mes in [
            x for x in range(0, PARAMS["meses_max_animales"]) if x in venta_all
        ]:
            f.write(f"{mes}\n")


def costs_to_dat_test(PATHS, periodos_modelo, meses_max_animales, clases):
    collect_costos = []

    with open(PATHS["costos"], "w") as f:
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


def calculate_daily_sales(df_ventas, df_precios):
    for index, row in df_ventas.iterrows():
        precios = get_precios_del_periodo(row.FECHA, df_precios)
        sub_tot_VAQUILLONAS270 = row["VAQUILLONAS270"] * precios["VAQUILLONAS270"]
        sub_tot_NOVILLITOS391 = row["NOVILLITOS391"] * precios["NOVILLITOS391"]
        sub_tot_NOVILLITOS300 = row["NOVILLITOS300"] * precios["NOVILLITOS300"]
        # sub_tot_VACAS = row['VACAS'] * precios['VACAS']
        # sub_tot_TOROS = row['TOROS'] * precios['TOROS']
        # sub_tot_TERNEROS_DESTETE = row['TERNEROS_DESTETE'] * precios['TERNEROS_DESTETE']
        # sub_tot_TERNERAS_DESTETE = row['TERNERAS_DESTETE'] * precios['TERNERAS_DESTETE']
        VENTA_TOT_DIA = (
            sub_tot_VAQUILLONAS270
            + sub_tot_NOVILLITOS391
            + sub_tot_NOVILLITOS300
            #    sub_tot_VACAS +
            #    sub_tot_TOROS +
            #    sub_tot_TERNEROS_DESTETE +
            #    sub_tot_TERNERAS_DESTETE
        )
        df_ventas.loc[index, "VENTA_PESOS"] = VENTA_TOT_DIA

    return df_ventas


def get_interplolator(PARAMS, output_plot_path=None):
    DataGrid = FDataGrid(list(PARAMS['costos_meses_ars_c1_c2'].values()), list(PARAMS['costos_meses_ars_c1_c2'].keys()))

    # Plot the total cost on the primary y-axis
    DataGrid.interpolation = SplineInterpolation(
        interpolation_order=3,
        monotone=True,
    )

    if output_plot_path:
        fig, ax1 = plt.subplots()
        DataGrid.plot(axes=ax1, label="accumulated cost curve")
        DataGrid.scatter(axes=ax1, c="C1")
        ax1.set_xlabel("months")
        ax1.set_ylabel("accumulated cost")

        # Plot the monthly cost on the secondary y-axis
        ax2 = ax1.twinx()
        monthly_cost = DataGrid.derivative()
        monthly_cost.plot(axes=ax2, label="monthly cost curve", c="C6")
        ax2.set_ylabel("monthly cost")

        # Show the legend
        fig.legend()

        fig.savefig(output_plot_path, dpi=300, bbox_inches="tight")

        return DataGrid


def costs_to_dat_realistic(Interpolator, PATHS, PARAMS):
    with open(PATHS["costos"], "w") as f:
        for periodo, edad_animal, clase in itertools.product(
            range(1, PARAMS["periodos_modelo"] + 1),
            range(-1, PARAMS["meses_max_animales"] + 1),
            range(1, PARAMS["clases"] + 1),
        ):
            if edad_animal == -1:
                costo = 0

            elif edad_animal > 21:
                costo = Interpolator.evaluate(
                    derivative=1,
                    extrapolation="periodic",
                    eval_points=[PARAMS['c1_c2_over_21']],
                ).min()

            elif clase == 3:
                costo = Interpolator.evaluate(
                    derivative=1,
                    extrapolation="periodic",
                    eval_points=[PARAMS['costos_c3']],
                ).min()

            else:
                costo = Interpolator.evaluate(
                    derivative=1, extrapolation="periodic", eval_points=[edad_animal]
                ).min()

            valores = [periodo, edad_animal, clase, int(costo), "\n"]
            line = "\t".join(str(x) for x in valores)
            f.write(line)



def delete_files(file_paths):
    for file in file_paths.values():
        if os.path.exists(file):
            os.remove(file)


def write_params_file(PATHS, PARAMS, SALES_PERIODS):
    # Write parameters to file
    with open(PATHS["parameters"], "w") as f:
        f.write("model params\n")
        f.write(f"max_periods {PARAMS['periodos_modelo']}\n")
        f.write(f"max_age_allowed {PARAMS['meses_max_animales']}\n")
        f.write(f"max_sell_qty_monthly {PARAMS['ventas_max_por_mes']}\n")

    # Write August birth data to file
    with open(PATHS["agosto_si"], "w") as f_yes, open(PATHS["agosto_no"], "w") as f_no:
        num = 8
        for semanas in range(PARAMS["periodos_modelo"] + 1):
            if semanas % num == 0:
                f_yes.write(f"{semanas}\n")
                num += 8
            else:
                f_no.write(f"{semanas}\n")

    # Write sale periods data to file
    with open(PATHS["momentos_venta_SI_c1_c2"], "w") as f:
        venta_destete = SALES_PERIODS["venta_destete"]
        venta_novillo_vaquillona = SALES_PERIODS["venta_novillo_vaquillona"]
        venta_pesados = SALES_PERIODS["venta_pesados"]
        venta_all = venta_destete + venta_novillo_vaquillona + venta_pesados
        for mes in [
            x for x in range(0, PARAMS["meses_max_animales"]) if x in venta_all
        ]:
            f.write(f"{mes}\n")


def write_costs_file_test(PATHS, periodos_modelo, meses_max_animales, clases):
    collect_costos = []

    with open(PATHS["costos"], "w") as f:
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


def calculate_daily_sales(df_ventas, df_precios):
    for index, row in df_ventas.iterrows():
        precios = get_precios_del_periodo(row.FECHA, df_precios)
        sub_tot_VAQUILLONAS270 = row["VAQUILLONAS270"] * precios["VAQUILLONAS270"]
        sub_tot_NOVILLITOS391 = row["NOVILLITOS391"] * precios["NOVILLITOS391"]
        sub_tot_NOVILLITOS300 = row["NOVILLITOS300"] * precios["NOVILLITOS300"]
        # sub_tot_VACAS = row['VACAS'] * precios['VACAS']
        # sub_tot_TOROS = row['TOROS'] * precios['TOROS']
        # sub_tot_TERNEROS_DESTETE = row['TERNEROS_DESTETE'] * precios['TERNEROS_DESTETE']
        # sub_tot_TERNERAS_DESTETE = row['TERNERAS_DESTETE'] * precios['TERNERAS_DESTETE']
        VENTA_TOT_DIA = (
            sub_tot_VAQUILLONAS270
            + sub_tot_NOVILLITOS391
            + sub_tot_NOVILLITOS300
            #    sub_tot_VACAS +
            #    sub_tot_TOROS +
            #    sub_tot_TERNEROS_DESTETE +
            #    sub_tot_TERNERAS_DESTETE
        )
        df_ventas.loc[index, "VENTA_PESOS"] = VENTA_TOT_DIA

    return df_ventas

def prices_to_usd_b(df_prices_ars, usd_b_path, cols_to_normalize):
    dln = DolarNormalizer(usd_b_path)

    df_prices_ars['usd_b'] = df_prices_ars.apply(lambda x: dln.mean_last_n_days(x['PERIODO_INICIO'], 7), axis=1)
    
    df_prices_ars[cols_to_normalize] = df_prices_ars[cols_to_normalize].div(df_prices_ars['usd_b'], axis=0)

    return df_prices_ars