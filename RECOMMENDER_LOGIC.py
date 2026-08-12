#Nutrition Recommender Code Logic for Application

#Importing essential libraries
from openpyxl import load_workbook
from faker import Faker
import pandas as pd
import matplotlib.pyplot as plt
from werkzeug.security import generate_password_hash, check_password_hash 
import seaborn as sns
import numpy as np

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
df_category = pd.read_csv('food_category.csv')

#Seperating the target nutrients using the USDA nutrient ids
target_usda_ids = [291, 646, 304, 309, 325, 326]
df_selected_nutrients_2 = df_nutrient[df_nutrient['nutrient_nbr'].isin(target_usda_ids)]

##Fixing the filtering 
food_data = pd.read_csv('food.csv')

#Filtering for only master food records and filtering out lab tests and sub samples
valid_data_types=['foundation_food', 'sr_legacy_food']
food_data = food_data[food_data['data_type'].isin(valid_data_types)].copy()

#Grouping similar foods together
food_data['short_name'] = food_data['description'].apply(lambda x: ', '.join(str(x).split(',')[:2]))

#Relational Merge Pipeline
#Linking the filtered nutrients to the bridge table
merge_part_1 = pd.merge(df_food_nutrient, df_selected_nutrients_2, left_on='nutrient_id', right_on='id', how='inner')

#Linking the result to food name table
df_joined_3 = pd.merge(merge_part_1, food_data, on='fdc_id', how='inner')

#Using the short name to merge duplicate foods
food_matrix_2 = df_joined_3.pivot_table(
    index=['short_name', 'food_category_id'],
    columns='name',
    values='amount',
    aggfunc='mean'
).fillna(0).reset_index() #Bringing the grouped indices back as standard columns

#Calculating the total vitamin D
vit_d2 = food_matrix_2.get('Vitamin D2 (ergocalciferol)', 0)
vit_d3 = food_matrix_2.get('Vitamin D3 (cholecalciferol)', 0)
food_matrix_2['Vitamin_D_Total_UG'] = vit_d2 + vit_d3

#Vector for the target nutrients 
nutrients_5d_order = [
    'short_name',
    'food_category_id',
    'Fiber, total dietary', 
    'Fatty acids, total polyunsaturated',
    'Magnesium, Mg',
    'Vitamin_D_Total_UG',
    'Zinc, Zn'
]

#Cleaning up final column names before saving
food_matrix_5d = food_matrix_2[nutrients_5d_order].copy()
food_matrix_5d.rename(columns={'short_name': 'food_description'}, inplace=True)

#Merging with food_category.csv to get the text name of the categories
food_matrix_5d = pd.merge(
    food_matrix_5d,
    df_category[['id', 'description']],
    left_on='food_category_id',
    right_on='id',
    how='left'
)

#Saving the new matrix containing shortened names AND categories
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

#Nutrient reccomender python logic
def nutrient_vector_2(patient_record):

    # Set a baseline daily reccomended intake of nutrients
    magnesium = 320.0 #milligrams
    fibre = 25.0 #grams
    PUFA = 12.0 #grams
    zinc = 7.0 #milligrams 25mg max
    vitamin_d = 10.0 #micrograms (1000 times smaller than a milligram) max 50ug

    #Retrieving the patient data from user
    homa_ir = patient_record.get('HOMA_IR') or 0
    glucose = patient_record.get('Fasting_Glucose_mg_dL') or 0 
    triglycerides = patient_record.get('Triglycerides_mg_dL') or 0 
    acne = patient_record.get('Acne_Severity') or 0
    pcos = patient_record.get('PCOS_Diagnosis') or 0 
    bmi = patient_record.get('BMI') or 0
    testosterone = patient_record.get('Total_Testosterone_ng_dL') or 0
    vitamin_d_level = patient_record.get('Vitamin_D_ng_mL') or 0

    #Fiber recommendation logic
    #High HOMA IR or high Fasting Glucose level can indicate insulin resistance
    #Using a continuous proportional multiplier with 15g as a safety cap  
    if homa_ir > 1.9 or glucose > 99:
        fibre_addition = homa_ir - 1.9 if homa_ir > 1.9 else 0
        fibre += min(15.0, fibre_addition * 1.5)

    #Omega 3 / Polyunsaturated fat reccommendation logic
    #High triglycerides and the presence of severe acne can indicate high lipids and inflammation
    #Omega 3 can lower lipid levels and combat skin inflammation
    #Using a continuous proportional multiplier with 10g as a safety cap
    if 150 <= triglycerides > 199 and acne == 3: 
        PUFA_addition = triglycerides - 199
        PUFA += min(10.0, PUFA_addition * 1.8)
    elif 150 <= triglycerides > 199 and acne ==2:
        PUFA_addition = triglycerides - 199
        PUFA += min(10.0, PUFA_addition * 1.5)
    elif 150 <= triglycerides > 199 and acne == 1:
        PUFA_addition = triglycerides - 199
        PUFA += min(10.0, PUFA_addition * 1.3)

    #Magnesium reccomendation logic
    #Magnesium can support insulin resistance and hormonal imbalance
    #Using a continuous proportional multiplier with 80mg as a safety cap
    if homa_ir > 1.9 and pcos == 1:
        magnesium_addition = homa_ir - 1.9
        magnesium += min(80, magnesium_addition * 10)

    if homa_ir > 1.9 and pcos == 0:
        magnesium_addition = homa_ir - 1.9
        magnesium += min(80, magnesium_addition * 7.5)


    #Vitamin D recommendation logic
    #Vitamin D can support patients with hormonal imbalance, insulin resistance and hirsutism
    #Using a continuous proportional multiplier with 80mg as a safety cap
    if bmi > 25 and vitamin_d_level < 10:
        vitamin_d_addition = bmi - 25
        vitamin_d += min(40, vitamin_d_addition * 2.5)

    if bmi > 25 and 10 <= vitamin_d_level < 20:
        vitamin_d_addition = bmi - 25
        vitamin_d += min(40, vitamin_d_addition * 1.5)
    

    #Zinc recommendation logic
    #Zinc can support PCOS patients with hirsutism, alopecia
    if testosterone > 46:
        zinc_addition = testosterone - 46
        zinc += min(18, zinc_addition * 1.5)

    #Round the nutrient figures
    return [round(fibre, 1), round(PUFA, 1), round(magnesium, 1), round(vitamin_d, 1), round(zinc, 1)]

def get_recommendations(user_email, db_path="patientdb.db", top_n=10):
    conn = sqlite3.connect(db_path)

    #Retrieving user vector
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Target_Nutrient_Vector, Allergens, Diet 
        FROM patientdata 
        WHERE lower(email) = lower(?) 
    """, (user_email,))
    row = cursor.fetchone()

    if not row or not row[0]:
        conn.close()
        return None
    
    patient_vector = json.loads(row[0])

    #Allergens list
    #Parsing the comma-seperated string back into a Python list
    patient_allergens = row[1].split(',') if row[1] else []

    #User diet
    user_diet = (row[2] or "omnivore").lower().strip()

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

    #------------------------------------------------
    #Dietary restriction filtering logic
    #Mapping diets to the USDA category IDs to exclude
    diet_exclusions = {
        'vegetarian': [5, 7, 10, 13, 15, 17], #Excluding Pork, Beef, Fish/Shellfish, Lamb/Veal/Game, Sausages/Luncheon
        'vegan': [1, 5, 7, 10, 13, 15, 17], #Excluding Dairy/Egg, Poultry, + all meat and seafood
        'pesketarian': [5, 7, 10, 13, 17], #Excluding Sausages/Luncheon, Pork, Beef, Lamb/Veal/Game (Keeps Fish 1500 & Poultry 500)
        'halal_diet': [7, 10] #Excluding Pork Products, Sausages/Luncheon Meats (contains non-halal gelatin/pork)
    }

    #If a user follows a specific restricted diet, filter out those category IDs
    if user_diet in diet_exclusions:
        excluded_category_ids = diet_exclusions[user_diet]
        filtered_food_db = filtered_food_db[~filtered_food_db['food_category_id'].isin(excluded_category_ids)]

    #Filtering logic for allergens
    #All keywords to filter out allergens out of the  
    allergen_keywords = {
        'milk': 'milk|cheese|yogurt|butter|cream|whey|dairy|ghee|paneer',
        'egg': 'egg|mayonnaise',
        'peanut':'peanut',
        'soy':'soy|tofu|edamame|miso',
        'wheat': 'wheat|flour|bread|pasta|cereal|bran|gluten|noodle',
        'tree_nut': 'almond|walnut|pecan|cashew|pistachio|macadamia|hazelnut|pine nut',
        'shellfish': 'shrimp|crab|lobster|prawn|crayfish|scallop|mussel|oyster|clam',
        'fish': 'salmon|tuna|cod|trout|halibut|sardine|mackerel|anchovy|pollock|fish',
        'sesame':'sesame|tahini'
    }

    #Iterating through the user's saved allergens and droping matching foods
    for allergen in patient_allergens:
        if allergen in allergen_keywords:
            pattern = allergen_keywords[allergen]
            #Keeping the rows where the food description does not contain the allergen words
            mask = ~filtered_food_db['food_description'].str.contains(pattern, case=False, na=False)
            filtered_food_db = filtered_food_db[mask]

    #Nutrient order
    target_fiber = patient_vector[0]
    target_pufa = patient_vector[1]
    target_magnesium = patient_vector[2]
    target_vit_d = patient_vector[3]
    target_zinc = patient_vector[4]

    #Elevated need for Fibre
    if target_fiber > 25:
        #Filtering out the foods that don't contain a lot of Fibre
        filtered_food_db = filtered_food_db[filtered_food_db['fiber_g'] > 0.5]

    #Elevated need for PUFA
    if target_pufa > 12:
        #Filtering out the foods that don't contain a lot of PUFA
        filtered_food_db = filtered_food_db[filtered_food_db['pufa_g'] > 0.5]

    #Elevated need for Magnesium
    if target_magnesium > 320:
        #Filtering out the foods that don't contain a lot of Magnesium
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

