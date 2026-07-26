#Nutrition Recommender Code Logic for Application

#Importing essential libraries
from openpyxl import load_workbook
from faker import Faker
import pandas as pd
import matplotlib.pyplot as plt
from werkzeug.security import generate_password_hash, check_password_hash 
import seaborn as sns
import numpy as np
import string
import random
import csv
import bcrypt

import sqlite3
import ast
import json
import os

#Libraries for machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

# -------------------------------------------------------------------
#Hashing the passwords in the csv file and populating it 
def populate_db(db_path="patientdb.db"):

    #Patient data with hashed passwords
    patient_df = pd.read_csv("patientdata.csv")
    conn = sqlite3.connect(db_path)

    #Populating the database
    #Ensuring the table is created new each time
    patient_df.to_sql('patientdata', conn, if_exists='replace', index=False)
    conn.close()


# -------------------------------------------------------------------
#Creating the food database with the 5 target nutrients
#Target nutrients matching to nutrients names in the USDA Nutrition/Food datasets

#Loading the nutrition datasets
df_food = pd.read_csv('food.csv')
df_food_nutrient = pd.read_csv('food_nutrient.csv', low_memory=False)
df_nutrient = pd.read_csv('nutrient.csv')

#Seperating the target nutrients using the USDA nutrient ids
target_usda_ids = [291, 646, 304, 309, 325, 326]
df_selected_nutrients_2 = df_nutrient[df_nutrient['nutrient_nbr'].isin(target_usda_ids)]

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
food_matrix_2 = df_joined_3.pivot_table(
    index='short_name',
    columns='name',
    values='amount',
    aggfunc='mean'
).fillna(0)

food_matrix_2['Vitamin_D_Total_UG'] = food_matrix_2['Vitamin D2 (ergocalciferol)'] + food_matrix_2['Vitamin D3 (cholecalciferol)']

#Vector for the target nutrients 
nutrients_5d_order = [
    'Fiber, total dietary', 
    'Fatty acids, total polyunsaturated',
    'Magnesium, Mg',
    'Vitamin_D_Total_UG',
    'Zinc, Zn'
]

food_matrix_5d = food_matrix_2[nutrients_5d_order]

# New Cosine Similarity Food recommendation engine
# Names are trapped in the index so need to reset index
food_matrix_5d = food_matrix_5d.reset_index()
food_matrix_5d.rename(columns={'short_name': 'food_description'}, inplace=True)
food_matrix_5d.to_csv("food_matrix_5d.csv", index=False)


# -------------------------------------------------------------------
def save_food_to_db(db_path="patientdb.db"):

    #Food matrix created with 5 nutrient vectors
    food_df = pd.read_csv("food_matrix_5d.csv")

    #Food database containing names of foods
    food_names = pd.read_csv("food.csv")

    #Establish connection to db
    conn = sqlite3.connect(db_path)

    #Store the food csv files into the database
    food_df.to_sql("food_matrix_5d", conn, if_exists="replace", index=False)
    food_names.to_sql("food", conn, if_exists="replace", index=False)
    
    conn.close()

def get_recommendations(user_email, db_path="patientdb.db", top_n=10):
    conn = sqlite3.connect(db_path)

    #Retrieving user vector
    cursor = conn.cursor()
    cursor.execute("SELECT Target_Nutrient_Vector FROM patientdata WHERE lower(email) = lower(?)", (user_email,))
    row = cursor.fetchone()
    if not row or not row[0]:
        conn.close()
        return None
    
    patient_vector = json.loads(row[0])

    #Retrieving the names of foods to attach them to the matrix
    #Loading the saved food_matrix_5d table 
    food_df = pd.read_sql_query("SELECT * FROM food_matrix_5d", conn)
    conn.close()

    #Renaming the Raw DQL nutrient column names
    food_df = food_df.rename(columns={
        "Fiber, total dietary": 'fiber_g',
        "Fatty acids, total polyunsaturated": 'pufa_g',
        "Magnesium, Mg": 'magnesium_mg',
        "Vitamin_D_Total_UG": 'vitamin_d_mcg',
        "Zinc, Zn": 'zinc_mg'
    })

    #Creating copies of databases for filtering
    filtered_food_db = food_df.copy()

    #Nutrient order
    target_fiber = patient_vector[0]
    target_pufa = patient_vector[1]
    target_magnesium = patient_vector[2]
    target_vit_d = patient_vector[3]
    target_zinc = patient_vector[4]

    #Elevated need for Magnesium
    if target_fiber > 25:
        #Filtering out the foods that don't contain a lot of Zinc
        filtered_food_db = filtered_food_db[filtered_food_db['fiber_g'] > 0.5]

    #Elevated need for Magnesium
    if target_pufa > 12:
        #Filtering out the foods that don't contain a lot of Zinc
        filtered_food_db = filtered_food_db[filtered_food_db['pufa_g'] > 0.5]

    #Elevated need for Magnesium
    if target_magnesium > 320:
        #Filtering out the foods that don't contain a lot of Zinc
        filtered_food_db = filtered_food_db[filtered_food_db['magnesium_mg'] > 0.5]

    #Elevated need for vitamin D
    if target_vit_d > 10:
        #Filtering out the foods that don't contain a lot of Vitamin D
        filtered_food_db = filtered_food_db[filtered_food_db['vitamin_d_mcg'] > 0.5]

    #Elevated need for Zinc
    if target_zinc > 7:
        #Filtering out the foods that don't contain a lot of Zinc
        filtered_food_db = filtered_food_db[filtered_food_db['zinc_mg'] > 0.5]

    #If the filtering is too restrictive and returns nothing, reset to the full database
    if filtered_food_db.empty:
        filtered_food_db = food_df.copy()

    #Isolating the 5 nutrients in the vector
    #For scaling
    nutrient_cols = ['fiber_g', 'pufa_g', 'magnesium_mg', 'vitamin_d_mcg', 'zinc_mg']
    food_numeric_matrix = filtered_food_db[nutrient_cols].values
    
    #Mapping the nutrient values to the food matrix
    #Converting the patient vector to 2D and scaling it normally
    scaler = MinMaxScaler()
    scaled_food_db = scaler.fit_transform(food_numeric_matrix)
    patient_matrix = np.array(patient_vector).reshape(1, -1)

    #Scaling the nutrients
    scaler = MinMaxScaler()
    scaled_foods = scaler.fit_transform(food_numeric_matrix)
    scaled_patient = scaler.transform(patient_matrix)

    #Calculating the similarity strictly across the subspace
    score_similarity = cosine_similarity(scaled_patient, scaled_foods)[0]

    #Attaching the scores back and treturning the top results
    results_df = filtered_food_db.copy()
    results_df['Match_Score'] = np.round(score_similarity * 100, 2)

    #Returning the top N items as a list of dictionaries for Jinja2 HTML rendering
    top_foods = results_df.sort_values(by='Match_Score', ascending=False).head(top_n)
    return top_foods.to_dict(orient='records')

#df = pd.read_csv('patientdata.csv')

#def hash_password(password):
#    pwd_bytes = password.encode('utf-8')
#    salt = bcrypt.gensalt()
#    hashed = bcrypt.hashpw(pwd_bytes, salt)
#    return hashed.decode('utf-8')