#Data cleaning of the excel file for database setup

#Importing essential libraries
from openpyxl import load_workbook
from faker import Faker
import pandas as pd
import numpy as np
import string
import random
import csv

#Set Seed
SEED_VAL = 55
random.seed(SEED_VAL)
np.random.seed(SEED_VAL)

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

    #Saving the fake credentials to the file
    df2.to_csv('cleandata.csv', index=False)
