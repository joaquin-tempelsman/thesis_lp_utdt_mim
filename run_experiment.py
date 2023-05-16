import logging
import os
import warnings
import json
from preprocessing.config import PARAMS, PATH_DAT_FILES, PESOS_PROMEDIO, path_parte_diario, path_scrapped_prices_df, intervalos_madurez
from preprocessing.generate_LP_inputs import build_LP_inputs
from preprocessing.analyze_business_variant import business_variant
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

delete_log_files('lp_logs')

exp_grid = {0 : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '01/01/2022'},
            1 : {'fecha_inicio': '07/06/2019', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '01/06/2022'},
            2 : {'fecha_inicio': '01/03/2020', 'periodos_modelo': 24, 'fecha_fin_ejercicio': '01/01/2023'},
            3 : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 36, 'fecha_fin_ejercicio': '01/01/2023'},
            4 : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 48, 'fecha_fin_ejercicio': '01/01/2023'},
            5 : {'fecha_inicio': '18/01/2019', 'periodos_modelo': 42, 'fecha_fin_ejercicio': '01/01/2023'},
}

for experiment, items in exp_grid.items():
   
    PARAMS['fecha_inicio'] = items['fecha_inicio']
    PARAMS['periodos_modelo'] = items['periodos_modelo']
    PARAMS['fecha_fin_ejercicio'] = items['fecha_fin_ejercicio']

    initial_stock_cost = build_LP_inputs(PARAMS, PATH_DAT_FILES, path_scrapped_prices_df, PESOS_PROMEDIO, path_parte_diario, intervalos_madurez, COST_TEST=False, INITIAL_STOCK_TEST=False)
    exp_grid[experiment]['lp_stock_history_cost'] = initial_stock_cost
    
    # run LP
    os.system(f"sudo docker exec scipTeach2 scip -f modelo.zpl -l lp_logs/exp_{experiment}.log")

    # compare with business variant data
    business_excercise = business_variant(PARAMS, PESOS_PROMEDIO, path_parte_diario, path_scrapped_prices_df)
    exp_grid[experiment]['business_results'] = business_excercise


with open("lp_logs/experiments_results.json", "w") as json_file:
    json.dump(exp_grid, json_file)

