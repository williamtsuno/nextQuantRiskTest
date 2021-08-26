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
    df["Valuation_Date"] = pd.to_datetime(df["Valuation_Date"], format="%m/%d/%Y").dt.date
    # Anonymize subfund name
    if anonymize:
        portfolio["Subfund_Long_Name"] = portfolio["Subfund_Long_Name"].replace({"简": "subfund001"})
    return df


if __name__ == "__main__":
    portfolio = read_portfolio(file_name="example_portfolio.csv")
    subfund_names = list(portfolio["Subfund_Long_Name"].unique())
    print(f"Successfully loaded these sub-funds: {subfund_names}")
