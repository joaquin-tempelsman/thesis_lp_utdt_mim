import math
import pandas as pd
import os
import numpy as np
import seaborn as sns
import itertools
import json
from datetime import datetime


def write_line_to_file(path, line):
    with open(path,'a') as f:
        f.write(line)

def get_stock_inicial_from_parte_diario(FECHA_INICIO_MODELO,
                                        clases,
                                        meses_max_animales,
                                        parte_diario_path='partediario_test.csv',
                                        output='stock_inicial.dat'
                                 ):

    #### - ARMA STOCK INICIAL CON 0 STOCK PARA TODOS LOS VALORES POSIBLES
    

    if os.path.exists(output):
        os.remove(output)

    collect_df = pd.DataFrame()
    for edad_animal, clase in itertools.product(range(-1,meses_max_animales + 1), range(1,clases+1)):
        collect_df = pd.concat([collect_df,pd.Series({'edad':edad_animal, 'clase': clase,'stock':0}).to_frame().T])

    # LEVANTO EL PARTE DIARIO Y REEMPLAZO LOS VALORES QUE SI TENGO STOCK EN EDADES DISTRIBUIDAS DENTRO DE UN RANGO UNIFORMEMENTE
    # PARA CADA CATEOGRIA

    # DISTRIBUYE ESTOCASTICAMENTE LOS ANIMALES ENTRE LOS DOS PRIMEROVS VALORES DE LA LISTA
    # EL TERCER VALOR ES LA CLASE A LA QUE PERTENECE. 
    intervalos = {
    'VACAS': [37, 96,3],
    'VAQ 1-2': [12, 17,2],
    'VAQ. 1-2 Servicio': [12, 36,3],
    'VAQ. 2-3': [36,96,3],
    'NOVILLOS': [25, 36,1],
    'NOVILLITOS': [12, 24,1],
    'TERNEROS': [6, 17,1],
    'TERNERAS': [6, 11,2],
    'OREJANO_MACHOS': [0, 5,1],
    'OREJANO_HEMBRAS': [0, 5,2]
    }

    df_stock_parte = pd.read_csv(parte_diario_path, usecols= [x for x in range(0,15)])
    df_stock_parte.rename(columns= {'MACHOS':'OREJANO_MACHOS', 'HEMBRAS':'OREJANO_HEMBRAS'}, inplace=True)
    categorias = [col for col in df_stock_parte.columns if col not in ('ESTAB.','FECHA','TOROS','TORITOS','TOTAL')]

    #limpiar casos anomalos
    df_stock_parte.loc[119, 'FECHA'] = '11/15/2014'
    df_stock_parte.loc[356, 'FECHA'] = '6/28/2019'

    df_stock_parte['FECHA'] = pd.to_datetime(df_stock_parte['FECHA'], format='%m/%d/%Y')

    #### - LEER STOCK DIARIO Y REEMPLAZAR STOCK INICIAL CON VALORES REALES - ####
    row = df_stock_parte.loc[df_stock_parte['FECHA'] == FECHA_INICIO_MODELO]

    df_collect_parte_diario = pd.DataFrame()
    for cat in categorias:
        if math.isnan(row[cat]):
            row[cat] = 0
        edades_random = np.random.random_integers(intervalos[cat][0], intervalos[cat][1], int(row[cat].values[0]))
        data = pd.DataFrame({'edad':edades_random, 'clase':intervalos[cat][2], 'stock':1})
        df_collect_parte_diario = pd.concat([df_collect_parte_diario, data])
            
    df_collect_parte_diario_agg = df_collect_parte_diario.groupby(['edad','clase']).sum()

    for index, row in df_collect_parte_diario_agg.reset_index().iterrows():
        collect_df.loc[(collect_df['edad'] == row.edad) & (collect_df['clase'] == row.clase), 'stock'] = row.stock

    for index, row in collect_df.iterrows():
        row = list(row) + ['\n']
        line = '\t'.join(str(x) for x in row)
        write_line_to_file(output, line)


def get_precios_scrapped(fecha_inicio,
                        input='scrapping_df3 - scrapping_df3.csv'):

    df_scrapping = pd.read_csv(input)

    
    df_scrapping['periodo'] = round((pd.to_datetime(df_scrapping['periodo_inicio']) - pd.to_datetime(fecha_inicio)) /np.timedelta64(1, 'M'),0).astype(int)

    append_list = []
    for index, row in df_scrapping.iterrows():
        clean_row = [row['VAQUILLONAS270'].split(',')[2],
        row['VAQUILLONAS391'].split(',')[2],
        row['NOVILLITOS300'].split(',')[2],
        row['NOVILLITOS391'].split(',')[2]]
        
        clean_row = [x[3:] if len(x) > 3 else x for x in clean_row]
        clean_row.append(row['periodo_inicio'])
        
        append_list.append(clean_row)

    df_precios = pd.DataFrame(data=append_list, columns=['VAQUILLONAS270','VAQUILLONAS391','NOVILLITOS300','NOVILLITOS391','PERIODO_INICIO'])
    df_precios['PERIODO_INICIO'] =pd.to_datetime(df_precios['PERIODO_INICIO'])

    cols_to_numeric = ['VAQUILLONAS270','VAQUILLONAS391','NOVILLITOS300','NOVILLITOS391']
    df_precios[cols_to_numeric] = df_precios[cols_to_numeric].apply(pd.to_numeric)
    df_precios['YYYYMM'] = df_precios.PERIODO_INICIO.dt.strftime('%Y%m')

    return df_precios

def plot_precios(df_precios):

    # plot precios v1 scrapping
    df_melt = df_precios.drop(columns=['YYYYMM'])
    df_melt = df_melt.melt(value_vars=[x for x in df_melt.columns if x != ['PERIODO_INICIO']], id_vars='PERIODO_INICIO', var_name='categoria', value_name='precio_x_kg')
    df_melt.sort_values(by='PERIODO_INICIO', inplace=True)
    df_melt['precio_x_kg'] = df_melt['precio_x_kg'].astype(int)
    g = sns.lineplot(data=df_melt, x='PERIODO_INICIO', y='precio_x_kg', hue='categoria').set_title('Precios scrapped')

def precios_scrapped_to_dat(df_precios,
                            periodos_modelo,
                            clases,
                            meses_max_animales,
                            peso_prom_dict,
                            path_to_file_precios= 'precios.dat',
                            fecha_inicio = '30/06/2020',
                            path_to_precios_fecha_max_min = 'precios_fecha_max_min.json'
                            ):

  

    df_precios_cut = df_precios[df_precios['PERIODO_INICIO'] >= pd.to_datetime(fecha_inicio)]
    df_precios_cut['periodo_mes_modelo'] = np.arange(1, len(df_precios_cut) + 1)

    # verifico que este la info de precios necesasria para todos los periodos del modelo
    assert max(df_precios_cut.periodo_mes_modelo) >= periodos_modelo

    # datos sacados de kg prom por cabeza de pagina "venta de cabezas - la cepa"
    peso_prom_destete = peso_prom_dict['peso_prom_destete']  
    peso_prom_vaquillonas = peso_prom_dict['peso_prom_vaquillonas'] 
    peso_prom_novillitos = peso_prom_dict['peso_prom_novillitos'] 
    peso_prom_vaquillonas_pesados = peso_prom_dict['peso_prom_vaquillonas_pesados'] 
    peso_prom_novillos_pesados = peso_prom_dict['peso_prom_novillos_pesados'] 

    

    #path_to_file_precios = 'modelos/mod_{version}/precios.dat'.format(version=version)
    path_to_file_precios = 'precios.dat'

    if os.path.exists(path_to_file_precios):
        os.remove(path_to_file_precios)

    precios_append = []
    for periodo, edad_animal, clase in itertools.product(range(1,periodos_modelo +1), range(-1,meses_max_animales + 1), range(1,clases+1)):
        row = df_precios_cut.loc[df_precios_cut['periodo_mes_modelo'] == periodo]
        
        try:
            #destete    
            if edad_animal ==  6:
                if clase == 0:
                    precio = int(row['VAQUILLONAS270']) * peso_prom_destete * 1.15
                if clase == 1:
                    precio = int(row['NOVILLITOS300']) * peso_prom_destete * 1.15

            #momento 1 16.5 meses
            elif (edad_animal == 16) or (edad_animal == 17):
                if clase == 0:
                    precio = int(row['VAQUILLONAS270']) * peso_prom_vaquillonas
                if clase == 1:
                    precio = int(row['NOVILLITOS300']) * peso_prom_novillitos

                
            #momento 2
            elif (edad_animal == 21) or (edad_animal == 22):
                if clase == 0:
                    precio = int(row['VAQUILLONAS391']) * peso_prom_vaquillonas_pesados
                if clase == 1:
                    precio = int(row['NOVILLITOS391']) * peso_prom_novillos_pesados
                    
            else:
                precio = 0

            # clase reproductora toma precio por kilo 50% de vaquiillonas y solo valua al final del juego
            if (clase == 3) & (periodo == periodos_modelo):
                precio = int(row['VAQUILLONAS270']) * peso_prom_vaquillonas * 0.5

            precio = round(precio)

        except TypeError:
            print('ERROR',row, periodo)
            break
        #-------------------#
        
        

        valores = [periodo,edad_animal,clase,precio,'\n']
        line = '\t'.join(str(x) for x in valores)
        write_line_to_file(path_to_file_precios, line)
        
        #get fecha max y min en row para obtener periodo de precios mapeados
        #para en get data cortar el linieplot entre esos periodos
        precios_append.append(row['PERIODO_INICIO'].values[0])
  
    precios_append = pd.Series(precios_append)
    precio_min_max = {'fecha_min': datetime.strftime(precios_append.min(), '%d/%m/%Y'),
                        'fecha_max': datetime.strftime(precios_append.max(), '%d/%m/%Y')}

    if os.path.exists(path_to_precios_fecha_max_min):
        os.remove(path_to_precios_fecha_max_min)        

    with open(path_to_precios_fecha_max_min, 'w') as fp:
        json.dump(precio_min_max, fp)

    return precio_min_max
    
def get_ventas_inicial_from_parte_diario(parte_diario_path):

    pos_cols_ventas = [x for x in range(25,34)]
    pos_cols_ventas.extend([1])

    ventas_df = pd.read_csv(parte_diario_path, usecols =pos_cols_ventas)
    ventas_df.rename(columns= {'MACHOS':'OREJANO_MACHOS', 'HEMBRAS':'OREJANO_HEMBRAS'}, inplace=True)
    ventas_df = ventas_df.fillna(0)

    #limpiar casos anomalos
    ventas_df.loc[119, 'FECHA'] = '11/15/2014'
    ventas_df.loc[356, 'FECHA'] = '6/28/2019'
    ventas_df['FECHA'] = pd.to_datetime(ventas_df['FECHA'], format='%m/%d/%Y')
    ventas_df.rename(columns={
    'VENTAS':'COMENTARIO',
    '?': 'SIN_ASIGNAR',
    'vacas' : 'VACAS',
    'vaquillonas' : 'VAQUILLONAS270',
    'novillos' : 'NOVILLITOS391',
    'novillitos' : 'NOVILLITOS300',
    'toros' : 'TOROS',
    'terneros' : 'TERNEROS_DESTETE',
    'terneras' : 'TERNERAS_DESTETE'}
    ,
    inplace=True)

    return ventas_df

def get_precios_del_periodo(periodo, df_precios):
    closest_price = abs((df_precios.PERIODO_INICIO - periodo)).sort_values(ascending=True)
    if closest_price[closest_price.index[0]] > pd.Timedelta('15 days'):
        print(f'WARNING: diferencia de precio mayor a 15 dias for {periodo}')
    precios_periodo = df_precios.iloc[closest_price.index[0]]
    
    return precios_periodo