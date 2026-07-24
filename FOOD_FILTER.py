#Importing essential libraries
from openpyxl import load_workbook
from faker import Faker
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import string
import random
import csv

#Libraries for machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

##Fixing the filtering 
food_data = pd.read_csv('food.csv')

#Filtering for only master food records and filtering out lab tests and sub samples
valid_data_types=['foundation_food', 'sr_legacy_food']
food_data = food_data[food_data['data_type'].isin(valid_data_types)]

#Grouping similar foods together
food_data['short_name'] = food_data['description'].apply(lambda x: ', '.join(str(x).split(',')[:2]))

#Relational Merge Pipeline
#Linking the filtered nutrients to the bridge table
merge_part_1 = pd.merge(df_food_nutrient, df_selected_nutrients_2, left_on='nutrient_id', right_on='id', how='inner')

#Linking the result to food name table
df_joined_3 = pd.merge(merge_part_1, food_data, on='fdc_id', how='inner')

#Using the short name to merge duplicate foods
food_matrix_3 = df_joined_3.pivot_table(
    index='short_name',
    columns='name',
    values='amount',
    aggfunc='mean'
).fillna(0)

food_matrix_3['Vitamin_D_Total_UG'] = food_matrix_3['Vitamin D2 (ergocalciferol)'] + food_matrix_3['Vitamin D3 (cholecalciferol)']

food_matrix_5d_3 = food_matrix_3[nutrients_5d_order]

# New Cosine Similarity Food recommendation engine
scaler_2 = MinMaxScaler()
food_matrix_scaled_3 = scaler_2.fit_transform(food_matrix_5d_3)
food_scaled_3 = pd.DataFrame(food_matrix_scaled_3, columns=food_matrix_5d_3.columns, index=food_matrix_5d_3.index)
