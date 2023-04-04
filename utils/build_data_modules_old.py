
import os
import itertools
import pandas as pd

def write_line_to_file(path, line):
    with open(path,'a') as f:
        f.write(line)

def get_stock_inicial_v0(output_path,
                         clases,
                         meses_max_animales,
                         edad_animal):

    #path_to_file_stock_inicial = 'modelos/mod_{version}/stock_inicial.dat'.format(version=version)
    path_to_file_stock_inicial = output_path

    if os.path.exists(path_to_file_stock_inicial):
        os.remove(path_to_file_stock_inicial)

    for edad_animal, clase in itertools.product(range(-1,meses_max_animales + 1), range(1,clases+1)):
        
        if (edad_animal == 0) & ((clase == 1) | (clase == 2)):
            stock = 10
            
        elif (edad_animal == 0) & (clase == 3):
            stock = 1

        else:
            stock = 0


        valores = [edad_animal,clase,stock,'\n']
        line = '\t'.join(str(x) for x in valores)
        write_line_to_file(output_path, line)



def get_precios_v0(output_path,
                   clases,
                   meses_max_animales,
                   edad_animal,
                   periodos_modelo):

    collect_precios = []



    if os.path.exists(output_path):
        os.remove(output_path)

    for periodo, edad_animal, clase in itertools.product(range(1,periodos_modelo +1), range(-1,meses_max_animales + 1), range(1,clases+1)):

        #destete    
        if edad_animal ==  6:
            precio = 600

        #momento 1
        elif (edad_animal == 16) or (edad_animal == 17):
            precio = 500 + edad_animal * 5

        #momento 2
        elif (edad_animal == 21) or (edad_animal == 22):
            precio = 500 + edad_animal * 4 # INCREMENTO!

        else:
            precio = 0

        # clase reproductora toma precio al final de su ciclo de vida
        if clase == 3:
            precio = max(25, 100 - edad_animal * 0.5)
            
        #if clase == 3 and edad_animal < semanas_max_animales:
        #    precio = 1 # INCREMENTO

        

        #-------------------#

        valores = [periodo,edad_animal,clase,precio,'\n']
        line = '\t'.join(str(x) for x in valores)
        write_line_to_file(output_path, line)

        collect_precios.append({'periodo': periodo , 'precio': precio, 'edad':edad_animal, 'clase':clase})
    collect_precios = pd.DataFrame(collect_precios)