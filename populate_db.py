#Importing Libraries
from flask import Flask, render_template, request, redirect, url_for, flash, session, redirect
import logging, re, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash 
import sqlite3
import csv
import math
import ast
import random
import os

from openpyxl import load_workbook
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import string
import random
import csv

from DATA_ENGINEERING import process_raw_file
from RECOMMENDER_LOGIC import patient_data_with_vectors
from RECOMMENDER_LOGIC import save_food_to_db

# Database paths
DB_PATH = "users.db"
CSV_PATH = "patientdata.csv"

#Creating patient table if they don't exist
def init_db(CSV_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #Drop table at start
    cursor.execute("DROP TABLE IF EXISTS patientdata")

    #Creating the table structure
    #Email needs to be unique so it is a primary key
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patientdata (
    "Age"	INTEGER,
	"Height_cm"	REAL,
	"Weight_kg"	REAL,
	"BMI"	REAL,
	"Menstrual_Cycle_Length_days"	INTEGER,
	"Menstrual_Irregularity"	INTEGER,
	"Fasting_Glucose_mg_dL"	REAL,
	"Fasting_Insulin_uIU_mL"	REAL,
	"HOMA_IR"	REAL,
	"LH_mIU_mL"	REAL,
	"FSH_mIU_mL"	REAL,
	"LH_FSH_Ratio"	REAL,
	"Total_Testosterone_ng_dL"	REAL,
	"Free_Testosterone_pg_mL"	REAL,
	"Total_Cholesterol_mg_dL"	INTEGER,
	"Triglycerides_mg_dL"	REAL,
	"Dietary_Sugar_Intake"	INTEGER,
	"Physical_Activity_Level"	INTEGER,
	"PCOS_Diagnosis"	INTEGER,
	"Hirsutism_Score_FG"	INTEGER,
	"Acne_Severity"	INTEGER,
	"Alopecia"	INTEGER,
	"Skin_Darkening_Acanthosis"	INTEGER,
	"first_name"	TEXT,
	"last_name"	TEXT,
	"email"	TEXT PRIMARY KEY,
	"password"	TEXT,
	"Target_Nutrient_Vector"	TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

    #Checking if the CSV file path exists before reading
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return
    
    #Checking if table is empty before populating to avoid duplication
    cursor.execute("SELECT COUNT(*) FROM patientdata")
    if cursor.fetchone()[0] == 0:

        with open(CSV_PATH, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                #Applying hashing encryption to passwords
                hashed_pw = generate_password_hash(row['password'], method="pbkdf2:sha256")

                #Inserting the rows from the CSV file
                cursor.execute("""
                    INSERT OR REPLACE INTO patientdata (
                        Age, Height_cm, Weight_kg, BMI, 
                        Menstrual_Cycle_Length_days, Menstrual_Irregularity,
                        Fasting_Glucose_mg_dL, Fasting_Insulin_uIU_mL,
                        HOMA_IR, LH_mIU_mL, FSH_mIU_mL, LH_FSH_Ratio,
                        Total_Testosterone_ng_dL, Free_Testosterone_pg_mL,
                        Total_Cholesterol_mg_dL, Triglycerides_mg_dL,
                        Dietary_Sugar_Intake, Physical_Activity_Level,
                        PCOS_Diagnosis, Hirsutism_Score_FG, Acne_Severity,
                        Alopecia, Skin_Darkening_Acanthosis, first_name, 
                        last_name, email, password, Target_Nutrient_Vector
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (

                        row['Age'], row['Height_cm'], row['Weight_kg'], row['BMI'],
                        row['Menstrual_Cycle_Length_days'], row['Menstrual_Irregularity'],
                        row['Fasting_Glucose_mg_dL'], row['Fasting_Insulin_uIU_mL'],
                        row['HOMA_IR'], row['LH_mIU_mL'], row['FSH_mIU_mL'], row['LH_FSH_Ratio'],
                        row['Total_Testosterone_ng_dL'], row['Free_Testosterone_pg_mL'],
                        row['Total_Cholesterol_mg_dL'], row['Triglycerides_mg_dL'],
                        row['Dietary_Sugar_Intake'], row['Physical_Activity_Level'],
                        row['PCOS_Diagnosis'], row['Hirsutism_Score_FG'], row['Acne_Severity'],
                        row['Alopecia'], row['Skin_Darkening_Acanthosis'], row['first_name'],
                        row['last_name'], row['email'], hashed_pw, row['Target_Nutrient_Vector']
                    ))
        conn.commit()
        conn.close()

