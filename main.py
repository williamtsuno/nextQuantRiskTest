import pandas as pd

def read_portfolio(file_name: str, anonymize: bool = False) -> pd.DataFrame:
    # Define data types
    dtypes = {
        "Subfund_Code": "str",
        "Valuation_Date": "str",
        "Subfund_CCY": "str",
        "Asset_Code": "str",
        "Asset_CCY": "str",
        "Market_Value_in_Subfund_CCY": "float",
        "Asset_Class": "str",
        "Country_of_Risk": "str",
        "Sector": "str",
        "Is_Hedge": "bool",
    }
    # Read the CSV
    df = pd.read_csv(
        file_name,
        delimiter=",",
        dtype=dtypes,
        squeeze=True,
        engine="c",
        true_values=["Yes"],
        false_values=["No"],
        skipfooter=False,
    )
    # Parse dates
    df["Valuation_Date"] = pd.to_datetime(df["Valuation_Date"], format="%d/%m/%Y").dt.date # The error was in the format date
    # Anonymize subfund name
    if anonymize:
        portfolio["Subfund_Long_Name"] = portfolio["Subfund_Long_Name"].replace({"简": "subfund001"})
    return df

def read_country_region(file_name: str) -> pd.DataFrame:
    # Define data types
    dtypes = {
        "Country": "str",
        "Region": "str",
    }
    # Read the CSV
    df = pd.read_csv(
        file_name,
        delimiter=",",
        dtype=dtypes,
        squeeze=True,
        engine="c",
        true_values=["Yes"],
        false_values=["No"],
        skipfooter=False,
    )

    return df

def read_subfund_navs(file_name: str) -> pd.DataFrame:
   
    dtypes = {
        "Subfund_Code": "str",
        "Valuation_Date": "str",
        "NAV": "float",
    }

    df = pd.read_excel(
        file_name,
        dtype=dtypes,
        squeeze=True,
        true_values=["Yes"],
        false_values=["No"],
    )

    # Parse dates
    df["Valuation_Date"] = pd.to_datetime(df["Valuation_Date"], format="%Y/%m/%d").dt.date # The error was in the format date


    return df
    
def calculate_metrics(portfolio, exposureEUR = False):
    """
    This function calculates the following exposures in percentage: long, short, net and gross
    The metric is segregated by Subfundo, Validation date and Asset Class
    The exposures can be calculated in the Asset CCY or Subfund CCY
    
    Args():
    portfolio: DataFrame with the deals.
    exposureEUR: Boolean which calculates the metrics in EUR (converting all the currency to EUR) or in the Asset CCY.
    """
    ## Currencies in EUR
    EurUsd = 1.18
    EurCny = 7.63
    EurJpy = 129.70
    EurRub = 86.79
    
    portfolio = portfolio.drop(['Subfund_Long_Name', 'Is_Hedge'], axis=1)
    
    # Check if the exposure will be in EUR or in the asset CCY
    if exposureEUR == False:
        
        ###### group the total currency by subfund, Valuation date and Asset CCY.
        data_group_total = ['Subfund_Code', 'Valuation_Date', 'Asset_CCY']
        portfolio_totalCurrency = portfolio.copy()
        # Calculate the total value by CCY
        portfolio_totalCurrency['Market_Value_in_Subfund_CCY'] = portfolio['Market_Value_in_Subfund_CCY'].abs()
        portfolio_totalCurrency = portfolio_totalCurrency.groupby(data_group_total).sum()
        portfolio_totalCurrency = portfolio_totalCurrency.rename(columns = {'Market_Value_in_Subfund_CCY':'Total_CCY'})

        # Merge the portfolio with the total currency information. This information is needed to calculate the percentage
        portfolio = pd.merge(portfolio, portfolio_totalCurrency, on="Asset_CCY")
 
        # Define the features to group the information
        data_group = ['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Asset_CCY', 'Total_CCY']

        
        ###### Calculate the exposures
        # Metric - net exposure 
        portfolio_net = portfolio.groupby(data_group, as_index=False).sum()
        portfolio_net['ExposurePercentage_net'] = portfolio_net['Market_Value_in_Subfund_CCY']/portfolio_net['Total_CCY']*100
    
        # Metric - long exposure
        portfolio_long = portfolio[portfolio['Market_Value_in_Subfund_CCY']>0].groupby(data_group, as_index=False).sum()
        portfolio_long['ExposurePercentage_long'] = portfolio_long['Market_Value_in_Subfund_CCY']/portfolio_long['Total_CCY']*100
    
        # Metric - short exposure
        portfolio_short = portfolio[portfolio['Market_Value_in_Subfund_CCY']<0].groupby(data_group, as_index=False).sum()
        portfolio_short['ExposurePercentage_short'] = portfolio_short['Market_Value_in_Subfund_CCY']/portfolio_short['Total_CCY']*100
    
        # Metric - gross exposure
        portfolio_gross = portfolio.copy()
        portfolio_gross['Market_Value_in_Subfund_CCY'] = portfolio['Market_Value_in_Subfund_CCY'].abs()
        portfolio_gross = portfolio_gross.groupby(data_group, as_index=False).sum()
        portfolio_gross['ExposurePercentage_gross'] = portfolio_gross['Market_Value_in_Subfund_CCY']/portfolio_gross['Total_CCY']*100    
        
        # Merge data frames with the exposures
        result1 = pd.merge(portfolio_short, portfolio_gross, on=data_group, how="outer")
        result2 = pd.merge(portfolio_net, portfolio_long, on=data_group, how="outer")
        
        # Prepare the data frame with the correct information
        result = pd.merge(result1, result2, on=data_group, how="outer").fillna(0)
        result = result[['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Asset_CCY', 'ExposurePercentage_net', 'ExposurePercentage_long', 'ExposurePercentage_short', 'ExposurePercentage_gross']]
    
    else:
        
        portfolio_totalCurrency = portfolio.copy()
        
        # Convert all the CCY in EUR
        for i in range(portfolio.shape[0]):
            if portfolio['Asset_CCY'][i] == 'USD':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurUsd
            elif portfolio['Asset_CCY'][i] == 'CNY':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurCny
            elif portfolio['Asset_CCY'][i] == 'JPY':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurJpy
            elif portfolio['Asset_CCY'][i] == 'RUB':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurRub
            elif portfolio['Asset_CCY'][i] == 'EUR':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]
        
        ###### group the total currency by subfund and Valuation.
        data_group_total = ['Subfund_Code', 'Valuation_Date']
        
        
        # Calculate the total value by CCY
        portfolio_totalCurrency['Market_Value_in_Subfund_CCY'] = portfolio['EUR_CCY'].abs()
        portfolio_totalCurrency = portfolio_totalCurrency.groupby(data_group_total).sum()
        portfolio_totalCurrency = portfolio_totalCurrency.rename(columns = {'Market_Value_in_Subfund_CCY':'Total_CCY'})
        
        # Merge the portfolio with the total currency information. This information is needed to calculate the percentage
        portfolio = pd.merge(portfolio, portfolio_totalCurrency, on="Subfund_Code")
        
        # Define the features to group the information
        data_group = ['Subfund_Code', 'Valuation_Date', 'Asset_Class',  'Total_CCY']
        
        ###### Calculate the exposures
        # Metric - net exposure 
        portfolio_net = portfolio.groupby(data_group, as_index=False).sum()
        portfolio_net['ExposurePercentage_net'] = portfolio_net['EUR_CCY']/portfolio_net['Total_CCY']*100
    
        # Metric - long exposure
        portfolio_long = portfolio[portfolio['Market_Value_in_Subfund_CCY']>0].groupby(data_group, as_index=False).sum()
        portfolio_long['ExposurePercentage_long'] = portfolio_long['EUR_CCY']/portfolio_long['Total_CCY']*100
    
        # Metric - short exposure
        portfolio_short = portfolio[portfolio['Market_Value_in_Subfund_CCY']<0].groupby(data_group, as_index=False).sum()
        portfolio_short['ExposurePercentage_short'] = portfolio_short['EUR_CCY']/portfolio_short['Total_CCY']*100
    
        # Metric - gross exposure
        portfolio_gross = portfolio.copy()
        portfolio_gross['Market_Value_in_Subfund_CCY'] = portfolio['EUR_CCY'].abs()
        portfolio_gross = portfolio_gross.groupby(data_group, as_index=False).sum()
        portfolio_gross['ExposurePercentage_gross'] = portfolio_gross['EUR_CCY']/portfolio_gross['Total_CCY']*100    
    
        data_group = ['Subfund_Code', 'Valuation_Date', 'Asset_Class']
        
        # Merge data frames with the exposures
        result1 = pd.merge(portfolio_short, portfolio_gross, on=data_group, how="outer")
        result2 = pd.merge(portfolio_net, portfolio_long, on=data_group, how="outer")
        result = pd.merge(result1, result2, on=data_group, how="outer").fillna(0)
        result = result[['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'ExposurePercentage_net', 'ExposurePercentage_long', 'ExposurePercentage_short', 'ExposurePercentage_gross']]
        
    return result
    
    
def calculate_metrics_CountryRegion(country_region, portfolio, Asset_Class = ['Equity', 'Fixed Income'] , exposure = ['net', 'long', 'short', 'gross'], exposureEUR = False):
    
    """
    This function calculates the exposure by Country/region.
    The exposure can be calculated in the Asset CCY or in EUR.
    
    Args():
    country_region: Dataframe with 'Country' and 'Region'
    portfolio: Dataframe with the assets
    Asset_Class: List of the asset classes to be calculated for the exposure. Default value 'Equity','Fixed Income'
    exposureEUR: Boolean which calculates the metrics in EUR (converting all the currency to EUR) or in the Asset CCY
    """
    ## Currencies in EUR
    EurUsd = 1.18
    EurCny = 7.63
    EurJpy = 129.70
    EurRub = 86.79
        
    portfolio = portfolio.drop(['Subfund_Long_Name', 'Is_Hedge'], axis=1)

    # Check if the exposure will be in EUR or in the asset CCY
    if exposureEUR == False:
    
        ###### group the total currency by subfund, Valuation date and Asset CCY.
        data_group_total = ['Subfund_Code', 'Valuation_Date', 'Asset_CCY']
        portfolio_totalCurrency = portfolio.copy()
        # Calculate the total value by CCY
        portfolio_totalCurrency['Market_Value_in_Subfund_CCY'] = portfolio['Market_Value_in_Subfund_CCY'].abs()
        portfolio_totalCurrency = portfolio_totalCurrency.groupby(data_group_total).sum()
        portfolio_totalCurrency = portfolio_totalCurrency.rename(columns = {'Market_Value_in_Subfund_CCY':'Total_CCY'})

        # Merge the portfolio with the total currency information. This information is needed to calculate the percentage
        portfolio = pd.merge(portfolio, portfolio_totalCurrency, on="Asset_CCY")
    
        # Merge the data frame contry and region with portfolio
        result = pd.merge(country_region, portfolio, how='outer', left_on='Country', right_on='Country_of_Risk')
        
        ###### Check the assets
        # Check if there is some country that is in the portfolio and it will not be consider
        print('Countries not included in the list:  ')
        print(result[((result['Country'].isnull() == True) & (result['Asset_Class'] != 'Currency'))]['Country_of_Risk'])
        
        # Cash in the portfolio
        cash = result[((result['Country'].isnull() == True) & (result['Asset_Class'] == 'Currency'))]
    
        # Exclude the Countries that are not needed and the currency
        result = result[((result['Country'].isnull() == False) & (result['Asset_Class'] != 'Currency'))]
    
    
        data_group = ['Country', 'Region','Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Asset_CCY', 'Country_of_Risk',  'Total_CCY']
    
        ###### Calculate the exposures
        # Metric - net exposure 
        portfolio_net = result.groupby(data_group, as_index=False).sum()
        portfolio_net['ExposurePercentage_net'] = portfolio_net['Market_Value_in_Subfund_CCY']/portfolio_net['Total_CCY']*100
    
        # Metric - long exposure
        portfolio_long = result[result['Market_Value_in_Subfund_CCY']>0].groupby(data_group, as_index=False).sum()
        portfolio_long['ExposurePercentage_long'] = portfolio_long['Market_Value_in_Subfund_CCY']/portfolio_long['Total_CCY']*100
    
        # Metric - short exposure
        portfolio_short = result[result['Market_Value_in_Subfund_CCY']<0].groupby(data_group, as_index=False).sum()
        portfolio_short['ExposurePercentage_short'] = portfolio_short['Market_Value_in_Subfund_CCY']/portfolio_short['Total_CCY']*100
    
        # Metric - gross exposure
        portfolio_gross = result.copy()
        portfolio_gross['Market_Value_in_Subfund_CCY'] = result['Market_Value_in_Subfund_CCY'].abs()
        portfolio_gross = portfolio_gross.groupby(data_group, as_index=False).sum()
        portfolio_gross['ExposurePercentage_gross'] = portfolio_gross['Market_Value_in_Subfund_CCY']/portfolio_gross['Total_CCY']*100    
        
        # Merge the data frames
        data_group = ['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Asset_CCY', 'Country_of_Risk', 'Region']
        result1 = pd.merge(portfolio_short, portfolio_gross, on=data_group, how="outer")
        result2 = pd.merge(portfolio_net, portfolio_long, on=data_group, how="outer")
        result = pd.merge(result1, result2, on=data_group, how="outer").fillna(0)
        
        # Check wich exposure will be displayed
        columns_finalData = ['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Asset_CCY', 'Country_of_Risk', 'Region']
        if 'net' in exposure:
            columns_finalData.append('ExposurePercentage_net')
        if 'long' in exposure:
            columns_finalData.append('ExposurePercentage_long')
        if 'short' in exposure:
            columns_finalData.append('ExposurePercentage_short')
        if 'gross' in exposure:
            columns_finalData.append('ExposurePercentage_gross')
        result = result[columns_finalData]
    
    else:    
        

        
        # Convert all the CCY in EUR
        for i in range(portfolio.shape[0]):
            if portfolio['Asset_CCY'][i] == 'USD':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurUsd
            elif portfolio['Asset_CCY'][i] == 'CNY':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurCny
            elif portfolio['Asset_CCY'][i] == 'JPY':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurJpy
            elif portfolio['Asset_CCY'][i] == 'RUB':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]/EurRub
            elif portfolio['Asset_CCY'][i] == 'EUR':
                portfolio.loc[i,'EUR_CCY'] = portfolio['Market_Value_in_Subfund_CCY'][i]
                
        ###### group the total currency by subfund and Valuation.
        data_group_total = ['Subfund_Code', 'Valuation_Date']
        
        # Calculate the total value by CCY
        portfolio_totalCurrency = portfolio.copy()
        portfolio_totalCurrency['EUR_CCY'] = portfolio['EUR_CCY'].abs()
        portfolio_totalCurrency = portfolio_totalCurrency.groupby(data_group_total).sum()
        portfolio_totalCurrency = portfolio_totalCurrency.rename(columns = {'EUR_CCY':'Total_CCY'})

        
        # Merge the portfolio with the total currency information. This information is needed to calculate the percentage
        portfolio = pd.merge(portfolio, portfolio_totalCurrency, on="Subfund_Code")
        
        # Merge the data frame contry and region with portfolio
        result = pd.merge(country_region, portfolio, how='outer', left_on='Country', right_on='Country_of_Risk')
        
        ###### Check the assets
        # Check if there is some country that is in the portfolio and it will not be consider        
        print('Countries not included in the list:  ')
        print(result[((result['Country'].isnull() == True) & (result['Asset_Class'] != 'Currency'))]['Country_of_Risk'])
    
        # Cash in the portfolio
        cash = result[((result['Country'].isnull() == True) & (result['Asset_Class'] == 'Currency'))]
    
        # Exclude the Countries that are not needed and the currency
        result = result[((result['Country'].isnull() == False) & (result['Asset_Class'] != 'Currency'))]

        data_group = ['Country', 'Region','Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Country_of_Risk',  'Total_CCY']
        
        ###### Calculate the exposures
        # Metric - net exposure 
        portfolio_net = result.groupby(data_group, as_index=False).sum()
        portfolio_net['ExposurePercentage_net'] = portfolio_net['EUR_CCY']/portfolio_net['Total_CCY']*100
    
        # Metric - long exposure
        portfolio_long = result[result['EUR_CCY']>0].groupby(data_group, as_index=False).sum()
        portfolio_long['ExposurePercentage_long'] = portfolio_long['EUR_CCY']/portfolio_long['Total_CCY']*100
    
        # Metric - short exposure
        portfolio_short = result[result['EUR_CCY']<0].groupby(data_group, as_index=False).sum()
        portfolio_short['ExposurePercentage_short'] = portfolio_short['EUR_CCY']/portfolio_short['Total_CCY']*100
    
        # Metric - gross exposure
        portfolio_gross = result.copy()
        portfolio_gross['EUR_CCY'] = result['EUR_CCY'].abs()
        portfolio_gross = portfolio_gross.groupby(data_group, as_index=False).sum()
        portfolio_gross['ExposurePercentage_gross'] = portfolio_gross['EUR_CCY']/portfolio_gross['Total_CCY']*100    
        
        # Merge the data frames
        data_group = ['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Country_of_Risk', 'Region']
        result1 = pd.merge(portfolio_short, portfolio_gross, on=data_group, how="outer")
        result2 = pd.merge(portfolio_net, portfolio_long, on=data_group, how="outer")
        result = pd.merge(result1, result2, on=data_group, how="outer").fillna(0)
        
        # Check wich exposure will be displayed
        columns_finalData = ['Subfund_Code', 'Valuation_Date', 'Asset_Class', 'Country_of_Risk', 'Region']
        if 'net' in exposure:
            columns_finalData.append('ExposurePercentage_net')
        if 'long' in exposure:
            columns_finalData.append('ExposurePercentage_long')
        if 'short' in exposure:
            columns_finalData.append('ExposurePercentage_short')
        if 'gross' in exposure:
            columns_finalData.append('ExposurePercentage_gross')
        
        result = result[columns_finalData]
        
    return result[result['Asset_Class'].isin(Asset_Class)]

def calculate_volAnnualized(df, subfundo = 'subfund001', date_vol = pd.Timestamp("2021-07-01")):
    df_data = df[(df['Subfund_Code'] == subfundo) & (df['Valuation_Date'] < date_vol)].copy()
    df_data = df_data.reset_index(drop=True)

    # Check the period of the data collection
    df_data_date1 =df_data['Valuation_Date'][0:-1].reset_index(drop=True)
    df_data_date0 =df_data['Valuation_Date'][1:].reset_index(drop=True)
    data_collection = (df_data_date1-df_data_date0).mean()
    
    # Annualized the volatility
    if data_collection.days == 1:
        vol = df_data['NAV'].std()*(252**0.5)
    elif data_collection.days == 7:
        vol = df_data['NAV'].std()*(52**0.5)
    elif data_collection.days == 30:
        vol = df_data['NAV'].std()*(12**0.5)
    else:
        print("Check the data collection frequency!")
        
    return vol

if __name__ == "__main__":
    print(f"pandas version: {pd.__version__}\n" )
    
    portfolio = read_portfolio(file_name="example_portfolio.csv")
    subfund_names = list(portfolio["Subfund_Long_Name"].unique())
    print(f"Successfully loaded these sub-funds: {subfund_names} \n")

    
    print(f"Compute the exposures and save them in csv file \n")
    calculate_metrics(portfolio, exposureEUR = False).to_csv(f'Subfund_Metric_AssetCCY.csv')
    calculate_metrics(portfolio, exposureEUR = True).to_csv(f'Subfund_Metric_EurCCY.csv')
    
    country_region = read_country_region('country_region.csv')
    country_names = list(country_region["Country"].unique())
    print(f"Successfully loaded these countries: {country_names}")
    
    Asset_Class = ['Equity']
    Exposure = ['net']
    print(f"Calculate exposure {Exposure} for the asset class {Asset_Class}")
    
    print(f"Calculate exposure in Asset CCY \n" )
    calculate_metrics_CountryRegion(country_region, portfolio, Asset_Class, Exposure, exposureEUR = False).to_csv(f'CountryRegion_Metric_AssetCCY.csv')
    print(f"Calculate exposure in EUR CCY \n")
    calculate_metrics_CountryRegion(country_region, portfolio, Asset_Class, Exposure, exposureEUR = True).to_csv(f'CountryRegion_Metric_EurCCY.csv')
    
    
    
    histNAV = read_subfund_navs('subfunds_navs.xlsx')
    subfund_names = list(histNAV["Subfund_Code"].unique())
    print(f"Successfully loaded NAV for the following subfunds: {subfund_names} \n")
    
    subfundo = 'subfund001'
    date_vol = pd.Timestamp("2021-07-01")
    
    print(f"Annualized volatility of {subfundo} as of the {date_vol}:")
    print(f" {calculate_volAnnualized(histNAV, subfundo, date_vol)}")
    
