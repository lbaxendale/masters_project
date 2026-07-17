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

import sqlite3
import ast
import json

#Libraries for machine learning
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


# -------------------------------------------------------------------
#Nutrient reccomender python logic
def nutrient_vector_2(patient_record):

    # Set a baseline daily reccomended intake of nutrients
    magnesium = 320.0 #milligrams
    fibre = 25.0 #grams
    PUFA = 12.0 #grams
    zinc = 7.0 #milligrams 25mg max
    vitamin_d = 10.0 #micrograms (1000 times smaller than a milligram) max 50ug

    #Fiber reccomendation logic
    #High HOMA IR or high Fasting Glucose level can indicate insulin resistance
    #Using a continuous proportional multiplier with 15g as a safety cap      
    if patient_record['HOMA_IR'] > 1.9 or patient_record['Fasting_Glucose_mg_dL'] > 99:
        fibre_addition = patient_record['HOMA_IR'] - 1.9
        fibre += min(15.0, fibre_addition * 1.5)

    #Omega 3 / Polyunsaturated fat reccommendation logic
    #High triglycerides and the presence of severe acne can indicate high lipids and inflammation
    #Omega 3 can lower lipid levels and combat skin inflammation
    #Using a continuous proportional multiplier with 10g as a safety cap
    if 150 <= patient_record['Triglycerides_mg_dL'] > 199 and patient_record['Acne_Severity'] == 3:
        PUFA_addition = patient_record['Triglycerides_mg_dL'] - 199
        PUFA += min(10.0, PUFA_addition * 1.8)

    if 150 <= patient_record['Triglycerides_mg_dL'] > 199 and patient_record['Acne_Severity'] == 2:
        PUFA_addition = patient_record['Triglycerides_mg_dL'] - 199
        PUFA += min(10.0, PUFA_addition * 1.5)

    if 150 <= patient_record['Triglycerides_mg_dL'] > 199 and patient_record['Acne_Severity'] == 1:
        PUFA_addition = patient_record['Triglycerides_mg_dL'] - 199
        PUFA += min(10.0, PUFA_addition * 1.3)

    #Magnesium reccomendation logic
    #Magnesium can support insulin resistance and hormonal imbalance
    #Using a continuous proportional multiplier with 80mg as a safety cap
    if patient_record['HOMA_IR'] > 1.9 and patient_record['PCOS_Diagnosis'] == 1:
        magnesium_addition = patient_record['HOMA_IR'] - 1.9
        magnesium += min(80, magnesium_addition * 10)

    if patient_record['HOMA_IR'] > 1.9 and patient_record['PCOS_Diagnosis'] == 1:
        magnesium_addition_2 = patient_record['HOMA_IR'] - 1.9
        magnesium += min(80, magnesium_addition_2 * 7.5)

    #Vitamin D recommendation logic
    #Vitamin D can support patients with hormonal imbalance, insulin resistance and hirsutism
    #Using a continuous proportional multiplier with 80mg as a safety cap
    if patient_record['BMI'] > 25:
        vitamin_d_addition = patient_record['BMI'] - 25
        vitamin_d += min(40, vitamin_d_addition * 2.5)

    #Zinc recommendation logic
    #Zinc can support PCOS patients with hirsutism, alopecia
    if patient_record['Total_Testosterone_ng_dL'] > 46:
        zinc_addition = patient_record['Total_Testosterone_ng_dL'] - 46
        zinc += min(18, zinc_addition * 1.5)

    #Round the nutrient figures
    return [round(fibre, 1), round(PUFA, 1), round(magnesium, 1), round(vitamin_d, 1), round(zinc, 1)]

# -------------------------------------------------------------------
#Defining a function that creates nutrition vectors for the patients in csv file
#This is for the existing patients in the csv file only, not new patients
def patient_data_with_vectors(csv_file, output_csv):

    #Reading the csv file without nutrition vector
    df = pd.read_csv(csv_file)

    #Running the nutrient vector logic across all rows in the PCOS dataset
    df['Target_Nutrient_Vector'] = df.apply(nutrient_vector_2, axis=1)

    #Save nutrient vector data to a new file
    df.to_csv(output_csv, index=False)

patient_data_with_vectors('cleandata.csv', 'patientdata.csv')

def hash_and_populate(csv_path, db_path="patientdb.db"):
    #reading the csv
    df = pd.read_csv(csv_path)

    #Hashing the passwords
    if 'password' in df.columns:
        df['password'] = df['password'].apply(
            lambda x: generate_password_hash(str(x), method="pbkdf2:sha256")
        )
    else:
        print("Error: 'password' column not found in CSV.")
        return
    
    #Populating the database
    conn = sqlite3.connect(db_path)
    #Ensuring the table is created new each time
    df.to_sql('patientdata', conn, if_exists='replace', index=False)
    conn.commit()
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

#Relational Merge Pipeline
#Linking the filtered nutrients to the bridge table
merge_part_1 = pd.merge(df_food_nutrient, df_selected_nutrients_2, left_on='nutrient_id', right_on='id', how='inner')

#Linking the result to food name table
df_joined_2 = pd.merge(merge_part_1, df_food, on='fdc_id', how='inner')

#Converting the table from a vertical format to horizontal format
#Each row represents one unique food
food_matrix_2 = df_joined_2.pivot_table(
    index='description',
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
scaler_2 = MinMaxScaler()
food_matrix_scaled_2 = scaler_2.fit_transform(food_matrix_5d)
food_scaled_2 = pd.DataFrame(food_matrix_scaled_2, columns=food_matrix_5d.columns, index=food_matrix_5d.index)

food_matrix_5d.to_csv("food_matrix_5d.csv", index=False)


# -------------------------------------------------------------------
def save_food_to_db(db_path="patientdb.db"):

    #Food matrix created with 5 nutrient vectors
    food_df = pd.read_csv("food_matrix_5d.csv")
    conn = sqlite3.connect(db_path)

    #Store the food data into the database
    food_df.to_sql("food_matrix_5d", conn, if_exists="replace", index=False)
    conn.close()

def get_recommendations(user_email, db_path="patientdb.db", top_n=10):
    conn = sqlite3.connect(db_path)

    #Retrieving user vector
    cursor = conn.cursor()
    cursor.execute("SELECT Target_Nutrition_Vector FROM patientdata WHERE lower(email) = lower(?)", (user_email,))
    row = cursor.fetchone()
    if not row or not row[0]:
        conn.close()
        return None
    
    patient_vector = json.loads(row[0])

    #Retrieving the names of foods to attach them to the matrix
    #Loading the saved food_matrix_5d table 
    food_df = pd.read_sql_query("SELECT * FROM food_matrix_5d", conn)

    #Renaming the Raw DQL nutrient column names
    food_df = food_df.rename(columns={
        "Fiber, total dietary": 'fiber_g',
        "Fatty acids, total polyunsaturated": 'pufa_g',
        "Magnesium, Mg": 'magnesium_mg',
        "Vitamin_D_Total_UG": 'vitamin_d_mcg',
        "Zinc, Zn": 'zinc_mg'
    })

    #Retrieving the names of foods to attach them to the matrix
    names_df = pd.read_sql_query("SELECT description AS food_description FROM food", conn)
    food_df['food_description'] = names_df['food_description']

    conn.close()

    #Isolating the 5 nutrients in the vector
    #For scaling
    nutrient_cols = ['fiber_g', 'pufa_g', 'magnesium_mg', 'vitamin_d_mcg', 'zinc_mg']
    
    #Mapping the nutrient values to the food matrix
    food_matrix = food_df[nutrient_cols].values
    patient_matrix = np.array(patient_vector).reshape(1, -1)

    #Scaling the nutrients
    scaler = MinMaxScaler()
    scaled_foods = scaler.fit_transform(food_matrix)
    scaled_patient = scaler.transform(patient_matrix)

    #Running the cosine similarity engine 
    similarity_scores = cosine_similarity(scaled_patient, scaled_foods)[0]
    food_results_df = food_df.copy()
    food_results_df['Match_Score'] = np.round(similarity_scores * 100, 1)

    #Returning the top N items as a list of dictionaries for Jinja2 HTML rendering
    top_foods = food_results_df.sort_values(by='Match_Score', ascending=False).head(top_n)
    return top_foods.to_dict(orient='records')

