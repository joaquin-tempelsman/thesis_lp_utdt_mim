
import pandas as pd

class DolarNormalizer:
    def __init__(self, filename):
        # Load DataFrame from CSV file
        self.df = pd.read_csv(filename, index_col=0, parse_dates=True)
        
    def mean_last_n_days(self, date, n):
        to_date = pd.to_datetime(date)
        from_date = to_date - pd.Timedelta(days=n-1)
        df_slice = self.df[from_date:to_date]
        mean = df_slice['avg'].astype(int).mean()
        
        return mean
    
