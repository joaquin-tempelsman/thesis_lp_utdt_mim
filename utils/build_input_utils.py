import os
import itertools
import math
import pandas as pd
from utils.build_data_modules import get_precios_del_periodo


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
    with open(PATHS["momentos_venta_no_posible_c1_c2"], "w") as f:
        venta_destete = SALES_PERIODS["venta_destete"]
        venta_novillo_vaquillona = SALES_PERIODS["venta_novillo_vaquillona"]
        venta_pesados = SALES_PERIODS["venta_pesados"]
        venta_all = venta_destete + venta_novillo_vaquillona + venta_pesados
        for mes in [
            x for x in range(0, PARAMS["meses_max_animales"]) if x not in venta_all
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
