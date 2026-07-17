#Nutrition Recommender Code Logic for Application

#Importing essential libraries
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

# -------------------------------------------------------------------
#Generating the nutrition vector for new users 
def new_user_nutrition_vector():
    

# -------------------------------------------------------------------
#Target nutrients matching to nutrients names in the USDA Nutrition/Food datasets

#Loading the nutrition datasets
df_food = pd.read_csv('food.csv')
df_food_nutrient = pd.read_csv('food_nutrient.csv')
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

