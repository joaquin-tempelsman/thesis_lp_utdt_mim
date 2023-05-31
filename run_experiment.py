import logging
import os
import warnings
import json
from preprocessing.config import (
    PARAMS,
    PATH_DAT_FILES,
    PESOS_PROMEDIO,
    path_parte_diario,
    path_scrapped_prices_df,
    intervalos_madurez,
)
from preprocessing.generate_LP_inputs import build_LP_inputs
from preprocessing.generate_business_variant import business_variant
from preprocessing.data_prep import delete_log_files

warnings.filterwarnings("ignore")

log = logging.getLogger("logger")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(message)s")
fh = logging.FileHandler("test.log", mode="w", encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

delete_log_files("lp_logs")
exp_grid = {
    # # variable prices - end of the world extra slack
    '2019_24periods_12eow_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 36, 'eow': 24 , 'fecha_fin_ejercicio': '08/01/2021', 'fix_prices': False, "mantain_c3_stock": 0},
    'm2019_24periods_12eow_real_prices' : {'fecha_inicio': '07/06/2019', 'periodos_modelo': 36, 'eow': 24  , 'fecha_fin_ejercicio': '03/06/2021', 'fix_prices': False, "mantain_c3_stock": 0},
    '2020_24periods_12eow_real_prices' : {'fecha_inicio': '03/01/2020', 'periodos_modelo': 36, 'eow': 24 , 'fecha_fin_ejercicio': '06/01/2022', 'fix_prices': False, "mantain_c3_stock": 0},
    '2019_36periods_12eow_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 48, 'eow': 36 , 'fecha_fin_ejercicio': '06/01/2022', 'fix_prices': False, "mantain_c3_stock": 0},
    '2019_42periods_6eow_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 48, 'eow': 42 , 'fecha_fin_ejercicio': '02/06/2022', 'fix_prices': False, "mantain_c3_stock": 0},
    '2019_48periods_0eow_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 48, 'eow': 48 , 'fecha_fin_ejercicio': '05/01/2023', 'fix_prices': False, "mantain_c3_stock": 0},    
    
    # variable prices - restriction to mantain c3 stock from period 0 on end
    '2019_24periods_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '08/01/2021', 'fix_prices': False, "mantain_c3_stock": 1},
    'm2019_24periods_real_prices' : {'fecha_inicio': '07/06/2019', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '03/06/2021', 'fix_prices': False, "mantain_c3_stock": 1},
    '2020_24periods_real_prices' : {'fecha_inicio': '03/01/2020', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '06/01/2022', 'fix_prices': False, "mantain_c3_stock": 1},
    '2019_36periods_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 36, 'fecha_fin_ejercicio': '06/01/2022', 'fix_prices': False, "mantain_c3_stock": 1},
    '2019_42period_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 42, 'fecha_fin_ejercicio': '02/06/2022', 'fix_prices': False, "mantain_c3_stock": 1},
    '2019_48period_real_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 48, 'fecha_fin_ejercicio': '05/01/2023', 'fix_prices': False, "mantain_c3_stock": 1},

    # # fix prices (non comparable to business)  - restriction to mantain c3 stock from period 0 on end
    # '2019_24periods_fix_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '08/01/2021', 'fix_prices': True, "mantain_c3_stock": 1},
    # 'm2019_24periods_fix_prices' : {'fecha_inicio': '07/06/2019', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '03/06/2021', 'fix_prices': True, "mantain_c3_stock": 1},
    # '2020_24periods_fix_prices' : {'fecha_inicio': '03/01/2020', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '06/01/2022', 'fix_prices': True, "mantain_c3_stock": 1},
    # '2019_36periods_fix_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 36, 'fecha_fin_ejercicio': '06/01/2022', 'fix_prices': True, "mantain_c3_stock": 1},
    # '2019_42period_fix_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 42, 'fecha_fin_ejercicio': '02/06/2022', 'fix_prices': True, "mantain_c3_stock": 1},
    # '2019_48period_fix_prices' : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 48, 'fecha_fin_ejercicio': '05/01/2023', 'fix_prices': True, "mantain_c3_stock": 1},
}

for experiment, items in exp_grid.items():
    PARAMS["fecha_inicio"] = items["fecha_inicio"]
    PARAMS["periodos_modelo"] = items["periodos_modelo"]
    PARAMS["fecha_fin_ejercicio"] = items["fecha_fin_ejercicio"]
    PARAMS["mantain_c3_stock"] = items["mantain_c3_stock"]
    
    if PARAMS["mantain_c3_stock"] == 1:
        pass

    (
        exp_grid[experiment]["lp_stock_history_cost"],
        df_precios,
    ) = build_LP_inputs(
        PARAMS,
        PATH_DAT_FILES,
        path_scrapped_prices_df,
        PESOS_PROMEDIO,
        path_parte_diario,
        intervalos_madurez,
        COST_TEST=False,
        INITIAL_STOCK_TEST=False,
        fix_prices=items["fix_prices"],
    )

    #run LP
    os.system(
       f"sudo docker exec scipTeach2 scip -f modelo.zpl -l lp_logs/{experiment}.log"
    )

    # compare with business variant data
    business_excercise, df_ventas, df_final_stock_value = business_variant(
        PARAMS, PESOS_PROMEDIO, path_parte_diario, path_scrapped_prices_df
    )
    exp_grid[experiment]["business_results"] = business_excercise
    df_final_stock_value.to_csv(f"lp_logs/df_final_stock_value_{experiment}.csv")

    # ! required by explore_results.ipynb
    pfix = items['fix_prices']
    df_precios.to_csv(f"lp_logs/df_precios_fix{pfix}.csv")


log.info("saving experiment results at lp_logs/experiments_results.json")
with open("lp_logs/experiments_results.json", "w") as json_file:
    json.dump(exp_grid, json_file)

log.info("saving experiment params at lp_logs/params.json")
with open("lp_logs/params.json", "w") as json_file:
    json.dump(PARAMS, json_file)
