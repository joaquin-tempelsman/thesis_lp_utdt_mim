
import pandas as pd

#manual fetch data from https://www.ambito.com/contenidos/dolar-informal-historico.html
df = pd.read_csv('data/usd_b.csv', parse_dates=['date'], dayfirst=True, dtype={'sell': float, 'buy': float, 'avg': float})
df.sort_values(by='date',ascending=True,inplace=True)
df.set_index(df['date'], inplace=True)

# generate a new dataframe with all dates
df_all_dates = pd.DataFrame(index=pd.date_range(start=df.date.min(), end=df.date.max(), freq='D'))
df_all_dates = df_all_dates.join(df.set_index('date'), how='left')
df_all_dates.ffill(inplace=True)
df_all_dates.to_csv('data/usd_b_fill.csv')
