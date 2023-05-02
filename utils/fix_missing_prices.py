import pandas as pd

# this script was meant to be used only once, keeping it here in case i need to fix the data again

df_collect = pd.DataFrame()
with open("data/precios_missing_16062022_150123.txt", "r") as f:
    capture_lines = False
    for line in f:
        line = line.strip()  # Remove leading/trailing whitespace
        if line == "Fecha Inicial":
            capture_lines = True
            count = 0
            continue  # Start reading the next line
        if capture_lines:
            if count < 50:  # Capture only the next 50 lines
                # Check if the line meets the conditions

                if count == 0:
                    fecha = line

                if "NOVILLOS Esp.Joven" in line:
                    novillos_exp_joven_avg = int(line.split(" ")[8].split(",")[0])

                if "NOVILLOS Regular h 430" in line:
                    novillos_regular_avg = int(line.split(" ")[8].split(",")[0])

                count += 1
            else:
                serie = pd.Series(
                    [fecha, novillos_exp_joven_avg, novillos_regular_avg],
                    index=["fecha", "novillos_exp_joven_avg", "novillos_regular_avg"],
                )
                # print(fecha, novillos_exp_joven_avg, novillos_regular_avg)
                df_collect = pd.concat([df_collect, serie.to_frame().T])
                capture_lines = False

df_collect