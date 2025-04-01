from langchain_community.utilities import SQLDatabase
import pandas as pd
from sqlalchemy import create_engine

# Reading and dropping null values in a single step
San_Francisco_df = pd.read_csv('San_Francisco_listings.csv')
New_jersey_df = pd.read_csv('New_Jersey_listings_csv.csv')
Settle_df = pd.read_csv('Seattle_listings.csv')
Oslo_df = pd.read_csv('Oslo_listings.csv')
Singapore_df = pd.read_csv('Singapore_listings.csv')
Taipei_df = pd.read_csv('Taipei_listings.csv')

San_Francisco_df = San_Francisco_df.dropna()
New_jersey_df = New_jersey_df.dropna()
Settle_df = Settle_df.dropna()
Oslo_df = Oslo_df.dropna()
Singapore_df = Singapore_df.dropna()
Taipei_df = Taipei_df.dropna()

# Concatenate the cleaned dataframes
merged_df = pd.concat([
    San_Francisco_df, 
    New_jersey_df, 
    Settle_df, 
    Oslo_df, 
    Singapore_df, 
    Taipei_df
], ignore_index=True)

# Reset the index
merged_df.reset_index(drop=True, inplace=True)

df = merged_df.copy()

engine = create_engine(f"sqlite:///{'properties.db'}")
df.to_sql("properties_df", engine, index=False, if_exists="replace")

db = SQLDatabase(engine)


schema_query = """

SELECT name, sql

FROM sqlite_master

WHERE type='table';

"""

def schema_builder(dict_path='Data_Dict.csv', sql_engine=None):
    
    schema_df = pd.read_sql(schema_query, sql_engine)

    schema_description = schema_df.to_string(index=False)

    data_dict = pd.read_csv(dict_path)

    data_dict_description = "\n".join(

    f"- {row['Column Name']} ({row['Data Type']}): {row['Data Description']}"

    for _, row in data_dict.iterrows())

    return schema_df, schema_description, data_dict, data_dict_description


schema_df, schema_description, data_dict, data_dict_description = schema_builder(
    dict_path="Data_Dict.csv", sql_engine=engine
)

location_values = ", ".join(df["location"].dropna().astype(str).unique())
property_type_values = ", ".join(df["property_type"].dropna().astype(str).unique())
unique_category_values = f"location: {location_values}, property_type: {property_type_values}"
