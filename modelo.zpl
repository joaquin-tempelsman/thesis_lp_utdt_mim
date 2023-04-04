#####----------- PARAMETROS -----------######

# Meses de duracion del ejercicio
param Tiempo := read "parametros.dat" as "2n" skip 1 use 1;

# vida maxima permitida de los animales
param vida_animal := read "parametros.dat" as "2n" skip 2 use 1;

# ventas max por mes
param vida_animal := read "parametros.dat" as "2n" skip 3 use 1;

# meses posibles donde hay nacimientos
set meses_agosto_si := { read "agosto_si.dat" as "<1n>"};

# meses donde no hay nacimientos
set meses_agosto_no := { read "agosto_no.dat" as "<1n>"};

# meses venta no posible c1 c2
set set_meses_vta_no_posible_c1_c2 := { read "momentos_venta_no_posible_c1_c2.dat" as "<1n>"};

# Conjunto de periodos
set T := { 1 .. Tiempo };

# meses que puede tener un animal
set E := { -1 .. vida_animal };

# clase del animal
set C := { 1, 2, 3};

# nacimientos por mes. suponemos cantidad constante. k en total por mes por clase
param k := 1;

# costo de los animales, en cada t,e,c
 param costo[T*E*C] := read "costos.dat" as "<1n,2n,3n> 4n";

# precio de los animales en cada periodo para cada genero
param precio[T*E*C] := read "precios.dat" as "<1n,2n,3n> 4n";

#do forall <t,e,c> in T*E*C with t == 24 and c == 1 and e > 22 and e < 25: print t, " ", e, " ", c, " ", precio[t,e,c];

# stock inicial para el periodo 0 
param stock_inicial[E*C] := read "stock_inicial.dat" as "<1n,2n> 3n";

#####----------- DEFINICION VARIABLES -----------#####

# Variable de stock
var x[(T union {0}) * E * C] >= 0; # Esto ya especifica las restricciones de no negatividad

# Variable de ventas
var y[(T union {0}) * E * C] >= 0; # Esto ya especifica las restricciones de no negatividad

# Variable de traspaso de vacas clase 2 a clase 3
var w[(T union {0}) * E] >= 0; # Esto ya especifica las restricciones de no negatividad

# Variable de nacimientos
var n[(T union {0}) * C] >= 0; # Esto ya especifica las restricciones de no negatividad


#####----------- FUNCION OBJJETIVO -----------#####

# Funcion objetivo
maximize fobj: sum <t,e,c> in T*E*C: (y[t,e,c] * precio[t,e,c] - x[t,e,c] * costo[t,e,c]);


#####----------- RESTRICCIONES -----------#####

########## - FLUJO - ##########

# Ecuaciones de conservacion de flujo. Ligamos las variables de stock y venta

subto eq_flujo_clase1: forall <t,e> in T*E with e > 0:    
    x[t,e,1] == x[t-1,e-1,1] - y[t-1,e-1,1];

subto eq_flujo_clase2: forall <t,e> in T*E with e > 0:
    x[t,e,2] == x[t-1,e-1,2] - y[t-1,e-1,2] - w[t-1,e-1]; 

subto eq_flujo_clase3: forall <t,e> in T*E with e >= 0:
    x[t,e,3] == x[t-1,e-1,3] - y[t-1,e-1,3] + w[t-1,e-1]; 

subto eq_flujo_sem_cero: forall <t,c> in T*C with t > 0 and c != 3:
    x[t,0,c] == n[t,c]; 


########## - VENTAS - ##########

#Restricción venta maxima por periodo 
#subto ventamax: forall <t> in T:
#    sum <e,c> in E*C: y[t,e,c] <= ventas_max_mes;

# No hay ventas en el periodo inicial
subto sinventasiniciales: forall <e,c> in E*C:
    y[0,e,c] == 0;

# Restriccion de ventas, no puedo vender mas de lo que tengo disponible.
subto ventas_liga_stock: forall <t,e,c> in T*E*C:
    y[t,e,c] <= x[t,e,c];

#version manual que si funciona
#subto meses_venta_posible_c1_c2: forall    <t,e,c> in T*E*C with c != 3 and e !=7 and e !=9 and e !=12: NO RUN
subto periodos_venta_posible_c1_c2: forall <t,e,c> in T*(E\set_meses_vta_no_posible_c1_c2)*C with c != 3:
    y[t,e,c] == 0;


########## - STOCK - ##########

subto eq_stock_ini: forall <e,c> in E*C:
   x[0,e,c] == stock_inicial[e,c];

# Restricción cantidad de stock maximo por periodo 
#subto stockmax: forall <t> in T:
#    sum <e,c> in E*C: x[t,e,c] <= 10000;

# No hay stock en edad negativa. Sino este caso queda por fuera de la reestriccion
# de flujo y toma el valor maximo posible
subto no_stock_edad_neg: forall <t,c> in T*C:
    x[t,-1,c] == 0;

#Edad máxima clase 1 y 2, 21.5 meses - 86 semanas, se venden antes.
subto edad_max_c1_c2: forall <t,e,c> in T*E*C with c < 3 and e > 22: 
    x[t,e,c] == 0;
   

######## - TRANSPASOS - #######

# limitamos la variable W de traspaso a no ser mayor a la diferencia entre stock y venta.
subto traspaso_liga_diff_stock_ventas: forall <t,e> in T*E:
    w[t,e] <= x[t,e,2] - y[t,e,2];
 
# No hay transpasos en el periodo inicial
subto sintranspasosiniciales: forall <e> in E:
   w[0,e] == 0;

#Pasaje a Clase 3, mínimo 11 meses - 44 semanas.
subto traspasos_min_2_anos_edad: forall <t,e> in T*E with e < 11:
   w[t,e] == 0;


####### - NACIMIENTOS - #######

subto sin_nacimientos_iniciales: forall <c> in C: 
    n[0,c] == 0;

#nacen animales por cada c3 que tengas de mas de 2 años
subto nacimientos_c1: forall <t> in meses_agosto_si:
    n[t,1]   ==  sum <e> in E with e >= 24: x[t,e,3] / 2;

subto nacimientos_c2: forall <t> in meses_agosto_si:
    n[t,2]   ==  sum <e> in E with e >= 24: x[t,e,3] / 2;

subto limite_nacimientos_c1_c2: forall <t,c> in meses_agosto_no*C:
    n[t,c]   ==  0;

subto limite_nacimientos_c3: forall <t> in T:
    n[t,3]   == 0;




####### - CODIGO BORRADOR - #######

#subto nacimientos_c2b: forall <t,e> in T*E with t in semanas_agosto:
#    n[t,2]   == floor( x[t,e,3] * 0.95 / 2 );