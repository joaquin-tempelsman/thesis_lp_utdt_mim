import pandas as pd
import numpy as np
import warnings
import plotly.express as px

warnings.filterwarnings('ignore')

def read_text_file(file_name):
    with open(file_name, "r") as f:
        return f.read()


def get_line_number_with_string(file_name, string):
    with open(file_name, "r") as f:
        for i, line in enumerate(f):
            if string in line:
                return i


def select_line_number(raw, line_nr):
    return raw.split("\n")[line_nr]

def read_scip_log(log_file_path):
    Log_df = pd.DataFrame()

    raw = read_text_file(log_file_path)
    results_line_nr = get_line_number_with_string(
        log_file_path, "================================="
    )


    # once per log
    objective_value = select_line_number(raw, results_line_nr + 2).split(" ")[-1]


    row_from = (
        get_line_number_with_string(log_file_path, "=================================") + 3
    )
    row_to = get_line_number_with_string(log_file_path, "Statistics") - 2

    # multiple times per log
    for line_nr in range(row_from, row_to + 1):
        variable = select_line_number(raw, line_nr).split(" ")[0]
        value = select_line_number(raw, line_nr).split(" ")[-2]
        unit_impact_on_obj_func = select_line_number(raw, line_nr).split(" ")[-1][6:-1]
        row_data = pd.Series(
            {
                "variable": variable,
                "value": value,
                "unit_impact_on_obj_func": unit_impact_on_obj_func,
            }
        )
        Log_df = pd.concat([Log_df, pd.DataFrame([row_data])], ignore_index=True)
    
    return Log_df

def format_log_df(Log_df):

    Log_df["var"] = Log_df["variable"].str.split("#").str[0]
    Log_df["t"] = Log_df["variable"].str.split("#").str[1]
    Log_df["age"] = Log_df["variable"].str.split("#").str[2]
    Log_df["class"] = Log_df["variable"].str.split("#").str[3]

    Log_df = Log_df[["t", "var", "age", "class", "value", "unit_impact_on_obj_func"]]
    Log_df = Log_df.loc[Log_df["var"].isin(["x", "y", "w", "n"])]
    Log_df["t"] = Log_df["t"].astype(int)
    Log_df["age"] = Log_df["age"].astype(int)
    Log_df["value"] = Log_df["value"].astype(float)
    Log_df["unit_impact_on_obj_func"] = Log_df["unit_impact_on_obj_func"].astype(float)
    Log_df["impact_on_obj_func"] = Log_df["value"] * Log_df["unit_impact_on_obj_func"]
    Log_df["class"] = Log_df["class"].astype(str)

    # agregamos artificialmente filas de venta 0 en t0 (igulamente estan restringidas) para la correcta visualizacion simetrica de los barplots
    Log_df = pd.concat(
        [
            Log_df,
            pd.DataFrame(
                [
                    pd.Series(
                        {
                            "t": 0,
                            "var": "y",
                            "age": 0,
                            "class": "1",
                            "value": 0,
                            "unit_impact_on_obj_func": 0.0,
                            "impact_on_obj_func": 0,
                        }
                    )
                ]
            ),
        ],
        ignore_index=True,
    )
    Log_df = pd.concat(
        [
            Log_df,
            pd.DataFrame(
                [
                    pd.Series(
                        {
                            "t": 0,
                            "var": "y",
                            "age": 0,
                            "class": "2",
                            "value": 0,
                            "unit_impact_on_obj_func": 0.0,
                            "impact_on_obj_func": 0,
                        }
                    )
                ]
            ),
        ],
        ignore_index=True,
    )
    Log_df = pd.concat(
        [
            Log_df,
            pd.DataFrame(
                [
                    pd.Series(
                        {
                            "t": 0,
                            "var": "y",
                            "age": 0,
                            "class": "3",
                            "value": 0,
                            "unit_impact_on_obj_func": 0.0,
                            "impact_on_obj_func": 0,
                        }
                    )
                ]
            ),
        ],
        ignore_index=True,
    )
    Log_df.sort_values(by="class", inplace=True)

    return Log_df

def operations_plots(Log_df, periodos_modelo):

    # maximos/minimos para rangos del eje Y
    x_max = Log_df.loc[Log_df["var"] == "x"].value.max()
    x_min = Log_df.loc[Log_df["var"] == "x"].value.min()
    y_max = Log_df.loc[Log_df["var"] == "y"].value.max()
    y_min = Log_df.loc[Log_df["var"] == "y"].value.min()

    stock_t0 = Log_df.loc[(Log_df["var"] == "x") & (Log_df["t"] == 0)].sort_values(
        by=["class", "age"]
    )
    fig0 = px.bar(
        stock_t0,
        x="class",
        y="value",
        color="age",
        color_continuous_scale="brwnyl",
        title="stock inicial por clase",
        range_x=[0, 2],
        range_y=[0, stock_t0.groupby("class").sum().max()["value"]],
    )

    fig0.update_traces(width=0.8)
    fig0.update_layout(
        height=500,
        width=600,
        xaxis_title="Clases",
        yaxis_title="stock",
    )
    fig0.show()

    stock_tn = Log_df.loc[
        (Log_df["var"].isin(["x", "y"])) & (Log_df["t"] == periodos_modelo)
    ].sort_values(by=["class", "age"])

    stock_tn["value"] = np.where(
        stock_tn["var"] == "y", stock_tn["value"] * -1, stock_tn["value"]
    )
    stock_tn = stock_tn.groupby(["t", "age", "class"]).sum().reset_index()
    fign = px.bar(
        stock_tn,
        x="class",
        y="value",
        color="age",
        color_continuous_scale="brwnyl",
        title="stock final por clase",
        range_x=[0, 2],
        range_y=[0, stock_tn.groupby("class").sum().max()["value"]],
    )
    fign.update_traces(width=0.8)
    fign.update_layout(
        height=500,
        width=600,
        xaxis_title="Clases",
        yaxis_title="stock",
    )
    fign.show()

    stock = Log_df.loc[(Log_df["var"] == "x")]
    fig1 = px.bar(
        stock,
        x="t",
        y="value",
        color="age",
        color_continuous_scale="brwnyl",
        facet_col="class",
        title="stock por edad y clase",
        range_x=[0, periodos_modelo],
        range_y=[0, x_max],
    )


    fig1.update_traces(width=1)
    fig1.update_layout(
        xaxis_title="tiempo",
        xaxis2_title="tiempo",
        xaxis3_title="tiempo",
        yaxis_title="cantidad",
    )
    fig1.show()

    ventas = Log_df.loc[(Log_df["var"] == "y")]

    fig2 = px.bar(
        ventas,
        x="t",
        y="value",
        color="age",
        color_continuous_scale="Blugrn",
        facet_col="class",
        title="ventas por edad y clase",
        range_x=[0, periodos_modelo],
        range_y=[0, y_max],
    )
    fig2.update_traces(width=2)
    fig2.update_layout(
        xaxis_title="tiempo",
        xaxis2_title="tiempo",
        xaxis3_title="tiempo",
        yaxis_title="cantidad",
    )
    fig2.show()

    trasp_df = Log_df.loc[Log_df["var"] == "w"].sort_values(by="t")
    nacimientos_df = (
        Log_df.loc[Log_df["var"] == "n"].sort_values(by="t").drop("class", axis=1)
    )
    nacimientos_df = nacimientos_df.rename(columns={"age": "class"})
    nacimientos_df["class"] = nacimientos_df["class"].astype(str)

    try:
        # nacimientos barplot
        fig4 = px.bar(
            x=nacimientos_df.t,
            y=nacimientos_df.value,
            range_x=[-5, periodos_modelo],
            color=nacimientos_df["class"],
            title="nacimientos por clase",
            color_discrete_sequence=px.colors.qualitative.T10,
        )
        fig4.update_traces(width=2)
        fig4.update_layout(
            height=500, width=600, xaxis_title="tiempo", yaxis_title="cantidad"
        )
        fig4.show()
    except ValueError:
        pass

    try:
        # traspasos barplot
        fig3 = px.bar(
            x=trasp_df.t,
            y=trasp_df.value,
            range_x=[-5, periodos_modelo],
            title="traspasos de clase 2 a 3",
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig3.update_traces(width=2)
        fig3.update_layout(
            height=500, width=600, xaxis_title="tiempo", yaxis_title="cantidad"
        )
        fig3.show()
    except ValueError:
        pass

def objective_function_plots(Log_df, periodos_modelo):

    group_obj_func = Log_df.groupby(["var", "t"])["impact_on_obj_func"].sum().reset_index()

    # total value per period
    obj_sum = (
        group_obj_func.groupby("t")
        .sum()
        .rename(columns={"impact_on_obj_func": "impact_on_obj_func"})
    )
    obj_sum["var"] = "total"
    obj_sum.reset_index(inplace=True)

    # CUIDADO, AGREGO EL TOTAL COMO UNA VARIABLE MAS, NO USAR PARA OTRAS COSAS
    # PORQUE TIENE INFORMACION DUPLICADA
    group_obj_func_2 = pd.concat([group_obj_func, obj_sum], axis=0)
    group_obj_func_2 = group_obj_func_2.loc[group_obj_func_2.impact_on_obj_func != 0]
    fig = px.line(
        x=group_obj_func_2.t,
        y=group_obj_func_2.impact_on_obj_func,
        color=group_obj_func_2["var"],
        range_x=[-5, periodos_modelo],
        title="variacion de funcion de ganancia",
    )
    fig.update_layout(xaxis_title="tiempo", yaxis_title="impacto funcion objetivo")
    fig.show()

    cumsum_df = group_obj_func.groupby("t").sum().reset_index()
    cumsum_df["cumsum_obj_func"] = cumsum_df["impact_on_obj_func"].cumsum()
    fig2 = px.line(
        cumsum_df, x="t", y="cumsum_obj_func", title="ganancia acumulada en el tiempo"
    )
    fig2.update_layout(xaxis_title="tiempo", yaxis_title="funcion objetivo acumulada")
    fig2.show()