import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob


def calc_real_return(idx, cpi, asset_dict, avg_dict, lookback_period=60):
    # idx_col, ret_col = idx.columns[:-3], idx.columns[-3:]
    asset_ls = [asset_dict[i] for i in idx.columns]
    avg_ls = pd.DataFrame(np.array([avg_dict[i] for i in asset_ls]).reshape(1, -1), columns=idx.columns)
    # infl_adj = idx.loc[:, idx_col].div(cpi.loc[:, idx_col])
    infl_adj = idx.div(cpi)
    # ret = infl_adj / infl_adj.iloc[0, :]
    monthly_ret = infl_adj.pct_change().apply(lambda x: np.log(1+x))
    # monthly_ret = pd.concat([monthly_ret, idx.loc[:, ret_col].div(cpi.loc[:, ret_col].pct_change()+1)], axis=1).apply(lambda x: np.log(1+x))
    excess_ret = pd.concat([avg_ls, monthly_ret.rolling(lookback_period).mean() * 12], axis=0)
    ir = excess_ret.iloc[1:, :].sub(excess_ret.iloc[0, :]) / (monthly_ret.rolling(lookback_period).std() * np.sqrt(12))
    return ir.dropna(how='all')


def construct_asset_dict(asset_ls):
    class_dict = {}
    for asset in asset_ls:
        if 'Eq' in asset:
            class_dict[asset] = 'Equity'
        elif 'Bond' in asset:
            class_dict[asset] = 'Bond'
        elif asset in ['Gold', 'Oil', 'TRCommodity']:
            class_dict[asset] = 'Commodity'
        else:
            class_dict[asset] = 'Alt'
    return class_dict


def construct_country_ls(asset_ls, countries=['US','UK','Japan','German']):
    country_ls = []
    for asset in asset_ls:
        if asset.split('Eq')[0] in countries:
            country_ls.append(asset.split('Eq')[0])
        elif asset.split('Bond')[0] in countries:
            country_ls.append( asset.split('Bond')[0])
        else:
            country_ls.append('US')
    return country_ls


def get_data(file_location, source=None):
    # get the data, clean it, merge it
    if source == 'GFD':
        df = pd.read_csv(file_location, index_col='Date', skiprows=2)['Close']
    else:
        df = pd.read_csv(file_location, index_col=0)#.dropna()
    df.index = pd.DatetimeIndex(df.index)
    df = df.sort_index(ascending=True)
    return df


idx_df = get_data('data/combined_dataset_new.csv')#.loc['1933-06-30':, :]
cpiFiles = glob.glob("data/Others/*CPI.csv")
cpi_dict = {}
for file_ in cpiFiles:
    country = file_.split('/')[-1].split('CPI.csv')[0]
    cpi_dict[country] = get_data(file_, source='GFD')#.loc['1933-06-30':]
cpi_df = pd.concat(cpi_dict, axis=1)
country_ls = construct_country_ls(idx_df.columns)
cpi_df = cpi_df.loc[:, country_ls].resample('M').last()
cpi_df.columns = idx_df.columns
asset_dict = construct_asset_dict(idx_df.columns)
avg_dict = {'Equity':0.05, 'Bond': 0.02, 'Commodity':0.0, 'Alt':0.035}
ir_df = calc_real_return(idx_df, cpi_df, asset_dict, avg_dict)
print(ir_df.head())
# ir_df.plot()
# plt.show()
ir_df.to_csv('results/real_return.csv')