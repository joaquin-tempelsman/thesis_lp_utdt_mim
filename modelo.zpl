#####----------- PARAMETROS -----------######

# Meses de duracion del ejercicio
param max_periods := read "model_inputs/parametros.dat" as "2n" skip 1 use 1;

# vida maxima permitida de los animales
param animal_max_age := read "model_inputs/parametros.dat" as "2n" skip 2 use 1;

# ventas max por mes
param max_sell_qty_monthly := read "model_inputs/parametros.dat" as "2n" skip 3 use 1;

# venta min por mes
param venta_min := read "model_inputs/parametros.dat" as "2n" skip 4 use 1;

# vender c1 c2 antes de X mes
param sell_c1_c2_before := read "model_inputs/parametros.dat" as "2n" skip 5 use 1;


# meses posibles donde hay nacimientos
set meses_agosto_si := { read "model_inputs/agosto_si.dat" as "<1n>"};

# meses donde no hay nacimientos
set meses_agosto_no := { read "model_inputs/agosto_no.dat" as "<1n>"};

# meses venta no posible c1 c2
set momentos_venta_SI_c1_c2 := { read "model_inputs/momentos_venta_SI_c1_c2.dat" as "<1n>"};


# Conjunto de periodos
set T := { 1 .. max_periods };

# meses que puede tener un animal
set E := { -1 .. animal_max_age };

# clase del animal
set C := { 1, 2, 3};

# costo de los animales, en cada t,e,c
 param costo[T*E*C] := read "model_inputs/costos.dat" as "<1n,2n,3n> 4n";

# precio de los animales en cada periodo para cada genero
param precio[T*E*C] := read "model_inputs/precios.dat" as "<1n,2n,3n> 4n";

#do forall <t,e,c> in T*E*C with t == 24 and c == 1 and e > 22 and e < 25: print t, " ", e, " ", c, " ", precio[t,e,c];

# stock inicial para el periodo 0 
param stock_inicial[E*C] := read "model_inputs/stock_inicial.dat" as "<1n,2n> 3n";

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
#maximize fobj: sum <t,e,c> in T*E*C: (y[t,e,c] * precio[t,e,c]); #TESTING, NO COST


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
#    sum <e,c> in E*C: y[t,e,c] <= max_sell_qty_monthly;


# Variable binaria de ventas, v[t] vale 1 si hay ventas en el periodo t
var s[T] binary;

# venta minima si hay ventas, o cero si s[t] vale 0
subto venta_minima: forall <t> in T:
    sum <e,c> in E*C: y[t,e,c] * s[t] >= venta_min;


# No hay ventas en el periodo inicial
subto sinventasiniciales: forall <e,c> in E*C:
    y[0,e,c] == 0;

# Restriccion de ventas, no puedo vender mas de lo que tengo disponible.
subto ventas_liga_stock: forall <t,e,c> in T*E*C:
    y[t,e,c] <= x[t,e,c];

# this is replaced by restriction ventas_precio_cero_null
#subto periodos_venta_no_posible_c1_c2: forall <t,e,c> in T*(E\momentos_venta_SI_c1_c2)*C with c != 3 and t != max_periods:
#    y[t,e,c] == 0;

subto ventas_precio_cero_null: forall <t,e,c> in T*E*C:
    if (precio[t,e,c] <= 0) then y[t,e,c] == 0 end;


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

#Edad máxima clase 1 y 2, se venden antes.
#subto edad_max_c1_c2: forall <t,e,c> in T*E*C with c != 3 and e > sell_c1_c2_before: 
#    x[t,e,c] == 0;
   

######## - TRANSPASOS - #######

# limitamos la variable W de traspaso a no ser mayor a la diferencia entre stock y venta.
subto traspaso_liga_diff_stock_ventas: forall <t,e> in T*E:
    w[t,e] <= x[t,e,2] - y[t,e,2];
 
# No hay transpasos en el periodo inicial
subto sintranspasosiniciales: forall <e> in E:
   w[0,e] == 0;

#Pasaje a Clase 3, estrictamente a los  11 meses
subto traspasos_min_2_anos_edad: forall <t,e> in T*E with e !=11:
   w[t,e] == 0;


####### - NACIMIENTOS - #######

subto sin_nacimientos_iniciales: forall <c> in C: 
    n[0,c] == 0;

#nacen animales por cada c3 que tengas de mas de 2 años
subto nacimientos_c1: forall <t> in meses_agosto_si:
    n[t,1]   ==  sum <e> in E with e >= 24: x[t,e,3] * 0.45;

subto nacimientos_c2: forall <t> in meses_agosto_si:
    n[t,2]   ==  sum <e> in E with e >= 24: x[t,e,3] * 0.45;

subto limite_nacimientos_c1_c2: forall <t,c> in meses_agosto_no*C:
    n[t,c]   ==  0;

subto limite_nacimientos_c3: forall <t> in T:
    n[t,3]   == 0;




####### - CODIGO BORRADOR - #######

#subto nacimientos_c2b: forall <t,e> in T*E with t in semanas_agosto:
#    n[t,2]   == floor( x[t,e,3] * 0.95 / 2 );