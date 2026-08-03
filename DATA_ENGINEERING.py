#Data cleaning and engineering of the excel file for database setup

#Importing essential libraries
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import load_workbook
from faker import Faker
import pandas as pd
import numpy as np
import string
import random
import csv
import os

#Set Seed
SEED_VAL = 55
random.seed(SEED_VAL)
np.random.seed(SEED_VAL)
Faker.seed(SEED_VAL)

def process_raw_file():
    #Loading the excel file
    df1 = pd.read_excel("PCOS Dataset.xlsx")

    #Creating a Reduced Dataset
    essential = [
        'Age',
        'Height_cm',
        'Weight_kg',
        'BMI',
        'Menstrual_Cycle_Length_days',
        'Menstrual_Irregularity',
        'Fasting_Glucose_mg_dL',
        'Fasting_Insulin_uIU_mL',
        'HOMA_IR',
        'LH_mIU_mL',
        'FSH_mIU_mL',
        'LH_FSH_Ratio',
        'Total_Testosterone_ng_dL',
        'Free_Testosterone_pg_mL',
        'Total_Cholesterol_mg_dL',
        'Triglycerides_mg_dL',
        'Dietary_Sugar_Intake',
        'Physical_Activity_Level',
        'PCOS_Diagnosis', 
        'Hirsutism_Score_FG',
        'Acne_Severity',
        'Alopecia',
        'Skin_Darkening_Acanthosis',
    ]

    df2 = df1[essential].copy()

    #Median Imputation
    #First change negative values to NaN 
    cols = [
        'Fasting_Insulin_uIU_mL',
        'HOMA_IR',
        'LH_mIU_mL',
        'Free_Testosterone_pg_mL',
        'Triglycerides_mg_dL',
    ]

    #Converting negative values to nan
    df2[cols] = df2[cols].mask(df2[cols] < 0, np.nan)

    #Converting NaN values to median values
    for col in ['Fasting_Insulin_uIU_mL', 'HOMA_IR', 'LH_mIU_mL', 'Free_Testosterone_pg_mL', 'Triglycerides_mg_dL',]:
        col_median = df2[col].median()
        df2[col] = df2[col].fillna(col_median)

    #Recalculating LH to FSH Ratio column and HOMA IR column
    #For mathematical integrity

    #LH/FSH Ratio Formula
    df2['LH_FSH_Ratio'] = df2['LH_mIU_mL'] / df2['FSH_mIU_mL']

    #HOMA IR Formula
    df2['HOMA_IR'] = (df2['Fasting_Insulin_uIU_mL'] * df2['Fasting_Glucose_mg_dL']) / 405

    #Replacing zero values with NaN
    for col in ['Fasting_Insulin_uIU_mL', 'Triglycerides_mg_dL']:
        df2[col] = df2[col].replace(0.0, np.nan)
        col_median = df2[col].median()
        df2[col] = df2[col].fillna(col_median)
        
    #Recalculating HOMA IR again
    #HOMA IR Formula
    df2['HOMA_IR'] = (df2['Fasting_Insulin_uIU_mL'] * df2['Fasting_Glucose_mg_dL']) / 405

    ##Assigning Fake First Name, Surname, Emails, and Passwords to Excel file data for Testing
    fake = Faker()

    #Function to create the fake password
    def gen_password(length=12):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))

    first_names = []
    last_names = []
    emails = []
    passwords = []

    #Creating first names, last names and passwords to go with passwords
    for i in range (len(df2)):

        #Creating the first name, last name and emails
        firstname = fake.first_name()
        lastname = fake.last_name()

        first_names.append(firstname)
        last_names.append(lastname)
        emails.append(f"{firstname.lower()}.{lastname.lower()}{i}@example.com")
        passwords.append(gen_password())

    df2["first_name"] = first_names
    df2["last_name"] = last_names
    df2["email"] = emails
    df2["password"] = passwords

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

    #Apply the nutrient vector logic to each row
    df2['Target_Nutrient_Vector'] = df2.apply(nutrient_vector_2, axis=1)

    #Allergens and diet columns
    df2['Allergens'] = ""
    df2['Diet'] = "omnivore" #Defaulting to Omnivore

    #Saving the fake credentials, nutrient vectors and unhashed passwords to the file
    df2.to_csv('patientdata_nohash.csv', index=False)

    #Create copy of the dataframe
    df3 = df2.copy(deep=True)

    #Hashing the passwords
    df3['hashed_password'] = df3['password'].apply(
        lambda p: generate_password_hash(str(p), method="pbkdf2:sha256")
    )

    #Dropping the unhashed passwords and storing in a csv file
    df_secure = df3.drop(columns=['password'])
    df_secure.to_csv('patientdata.csv', index=False)


