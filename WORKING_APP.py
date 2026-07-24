#Flask test app

#Importing Libraries
from flask import Flask, render_template, request, redirect, url_for, flash, session, redirect
import logging, re, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash 

#Other python files
from DATABASE_CREATION import init_db
from RECOMMENDER_LOGIC import nutrient_vector_2
from RECOMMENDER_LOGIC import get_recommendations
import json

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

#Set Seed
SEED_VAL = 55
random.seed(SEED_VAL)
np.random.seed(SEED_VAL)

# ------------------------------------
#Initialising Flask Application
app = Flask(__name__)
# ------------------------------------

# ------------------------------------
# In production set SECRET_KEY via environment variable
app.secret_key = os.environ.get("SECRET_KEY", "ftgongvsbn7283")

# ------------------------------------

# ------------------------------------
# Database paths
DB_PATH = "patientdb.db"
# ------------------------------------

# ------------------------------------
#Creating patient table if they don't exist

# ------------------------------------
#Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)
# ------------------------------------

# ------------------------------------
# Validation patterns

##Ensure that first name is only letters and hyphens
FIRSTNAME_PATTERN = re.compile(r'^[A-Za-z-]{1,50}$')

##Ensure that last name is only letters and hyphens
LASTNAME_PATTERN = re.compile(r'[A-Za-z-]{1,50}$')

## Ensures the email has a basic valid structure of name@domain.tld
EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}$')

## Strong password pattern that requires lowercase, uppercase, digit, special character, and minimum 8 characters.
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$')
# ------------------------------------


# ------------------------------------
def generate_nutrition_message(patient_vector):
    #Analysing the patients target vector 
    #Generating a personalised explanation based on the results
    #And if nutrients needs are elevated above the baseline

    #Listing the order of the vector
    fiber, pufa, mag, vit_d, zinc = patient_vector

    #Initialising variable for the messages
    messages = []

    #Constraints for the messages if they are above the baseline level
    if fiber > 25.0: 
        messages.append("Increased fiber take: this can help manage blood glucose spikes and support insulin sensitivity.")
    if pufa > 12.0:
        messages.append("Extra omega-3 and polyunsaturated fats: this can help reduce inflammation and lower lipid levels.")
    if mag > 320.0: 
        messages.append("Higher magnesium intake: this can support insulin regulation and metabolic stability.")
    if vit_d > 10.0: 
        messages.append("Increased Vitamin D: this can support hormonal balance and menstrual regularity.")
    if zinc > 7.0:
        messages.append("Extra Zinc: this can help manage androgen related symptoms like acne or hair loss.")

    #If nutrient levels are perfectly at baseline level without elevated needs
    if not messages:
        return "Nutrifem suggests a balanced baseline diet to safely maintain your current metabolic and hormonal health."

    return messages

# ------------------------------------
# Routes for pages

# Route for the Home page
@app.route('/')
def home():
    return render_template('home.html')

# Route for the About page
@app.route('/about')
def about():
    return render_template('about.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    # ----- Post request handling -----
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not (email and password):
        flash("Please enter email and password.")
        return redirect(url_for("login"))

    # ----- Database connection and Query -----
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #Querying the user table to find a user matching the email
    cursor.execute("""
        SELECT first_name, last_name, email, hashed_password
        FROM patientdata
        WHERE lower(email) = lower(?)
    """, (email,))
    row = cursor.fetchone()
    conn.close() #Close connection immediately after fetching data

    # ----- Check if we found a user in the database
    if not row:
        flash("Invalid email or password.")
        return redirect(url_for("login"))
    
    #Extracting the user data from the database row
    db_first_name, db_last_name, db_email, password_hash = row

    # ----- Verify the submitted password against the stored hash -----
    if not check_password_hash(password_hash, password):
        flash("Invalid email or password.")
        return redirect(url_for("login"))

    #Saving user information in session upon successful login
    session["ID"] = db_email
    session["username"] = f"{db_first_name} {db_last_name}"
    return redirect(url_for("dashboard"))

# Route for the patient dashboard
@app.route("/dashboard")
def dashboard():
    if "ID" not in session:
        flash("Please log in to continue.")
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Route for the profile page
@app.route("/profile")
def profile():
    if "ID" not in session: 
        flash("Please log in to continue.")
        return redirect(url_for("login"))

    user_email = session["ID"]

    #Connecting to the database to retrieve user details
    conn= sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row #Accessing column names on rows
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patientdata WHERE lower(email) = lower(?)", (user_email,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        flash("User details could not be found.")
        return redirect(url_for("dashboard"))

    return render_template(
        'profile.html',
        user=user_row,
        user_name=session.get("username", "User")
    )

#Re routing user to login page when user logs out
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))

# Route for the register page
@app.route('/register', methods =['GET', 'POST'])
def register():
    if request.method == 'POST':
        First_name = (request.form.get("first-name") or "").strip()
        Last_name = (request.form.get("surname") or "").strip()
        email    = (request.form.get("email") or "").strip()
        password = (request.form.get("password") or "").strip()
        
        try:

            ## ---- SERVER-SIDE INPUT VALIDATION FOR REGISTRATION FORM ---- ##

            # ----- Checking empty fields -----
             if not First_name:
                 raise ValueError("First name is required")
             if not Last_name:
                 raise ValueError("Last name is required")
             if not email:
                 raise ValueError("Email is required.")
             if not password:
                 raise ValueError("Password is required.")
             
            # ----- Type / Format checks -----
             if not FIRSTNAME_PATTERN.fullmatch(First_name):
                  raise ValueError("First name must only contain letters and hyphens")

             if not LASTNAME_PATTERN.fullmatch(Last_name):
                  raise ValueError("Last name must only contain letters and hyphens")
             
             if not EMAIL_PATTERN.fullmatch(email):
                  raise ValueError("Email format is invalid.")
             
             if not PASSWORD_PATTERN.fullmatch(password):
                  raise ValueError("Password format is invalid.")
             
             if len(email) > 254:
                  raise ValueError("Email too long.")

            # ----- Hashing password ------
             hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

             conn= sqlite3.connect(DB_PATH)
             cursor = conn.cursor()

            # ----- Pre-check duplicate -----
             cursor.execute("SELECT 1 FROM patientdata WHERE lower(email) = lower(?)", (email,))
             if cursor.fetchone():
                 flash("This email is already registered. Please log in instead.")
                 conn.close()
                 return redirect(url_for("login"))
             
            # ----- Insert the user into the database ----- 
             try:
                 cursor.execute("""
                    INSERT INTO patientdata (first_name, last_name, email, hashed_password)
                    VALUES (?, ?, ?, ?)
                 """, (First_name, Last_name, email, hashed_password)) #doctor is set as default role for role based access 
                 conn.commit()
                 flash("Registration successful! Please log in.")
             except sqlite3.IntegrityError: 
                 flash("This email is already registered. Please log in.")
             finally:
                 conn.close()

             return redirect(url_for("success"))
        
        except ValueError as e:
            flash(str(e), 'error')
            log.warning("Validation failed: %s", e)
            return redirect(url_for("register"))
       
    return render_template("register.html")

# Route for Registration success page 
@app.route('/success')
def success():
    return render_template('register_success.html')

# Route for the view recommendations page
@app.route('/view_recs')
def view_recs():
    if "ID" not in session:
        flash("Please log in to view your recommendations.") 
        return redirect(url_for("login"))

    #Session is user's email
    user_email = session["ID"]

    #Retrieving the user's vector from the database first
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT Target_Nutrient_Vector FROM patientdata where lower(email) = lower(?)", (user_email,))
    user_row = cursor.fetchone()
    conn.close()

    #Printing error message if nutrient profile is not located
    if not user_row:
        flash("Could not locate nutrient profile.")
        return redirect(url_for("dashboard"))

    import json
    patient_vector = json.loads(user_row[0])

    #Generating personalised nutrition message
    personalised_messages = generate_nutrition_message(patient_vector)

    #Running the recommender engine
    top_10_foods = get_recommendations(user_email, DB_PATH, top_n=10)

    if top_10_foods is None:
        flash("Could not locate nutrient profile for your account.")
        return redirect(url_for("questionnaire"))
    
    #Passing the recommendations results into the HTML page for display
    return render_template(
        'view_recs.html', 
        recommendations=top_10_foods, 
        user_name=session.get("userFirstName", "User"),
        messages=personalised_messages
        )

# Route for the update password page
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if "ID" not in session:
        flash("Please log in to continue.")
        return redirect(url_for("login"))

    user_email = session["ID"]

    if request.method == "GET":
        return render_template('update_password.html')

    #Retrieving fields from the update password form
    if request.method == 'POST':
        current_password = (request.form.get("current_password") or "").strip()
        new_password = (request.form.get("new_password") or "").strip()
        confirm_password = (request.form.get("confirm_password") or "").strip()

        #Checking for empty fields
        if not (current_password and new_password and confirm_password):
            flash("All fields are required.", "error")
            return redirect(url_for("update_password"))

        #Checking if the new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match. Please try again.", "error")
            return redirect(url_for("update_password"))

        #Validate the new password complexity using the regex pattern
        if not PASSWORD_PATTERN.fullmatch(new_password):
            flash("Password must be at least 8 characters long and include an uppercase letter, lowercase letter, number, and special character.")
            return redirect(url_for("update_password"))

        #Connecting to database to verify the current password
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT hashed_password FROM patientdata WHERE lower(email) = lower(?)", (user_email,))
        row = cursor.fetchone()

        if not row or not row[0]:
            conn.close()
            flash("User record not found.", "error")
            return redirect(url_for("login"))
        stored_hash = row[0]

        #Checking if the current password matches the stored hash
        if not check_password_hash(stored_hash, current_password):
            conn.close()
            flash("Incorrect current password. Please try again.", "error")
            return redirect(url_for("update_password"))

        #Hashing the new password and updating it in the database
        new_hashed_password = generate_password_hash(new_password, method="pbkdf2:sha256")

        cursor.execute("""
            UPDATE patientdata
            SET hashed_password = ?
            WHERE lower(email) = lower(?)
        """,  (new_hashed_password, user_email))

        conn.commit()
        conn.close()

        flash("Password updated successfully!", "success")
        return redirect(url_for("profile"))

# Route for the Questionnaire page
@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    if "ID" not in session:
        flash("Please log in to continue.")
        return redirect(url_for("login"))
    
    if request.method == 'POST':
        age = (request.form.get("age") or "").strip()
        height = (request.form.get("height") or "").strip()
        weight = (request.form.get("weight") or "").strip()
        cycle_length = (request.form.get("cycle_length") or "").strip()
        sugar_intake = (request.form.get("sugar_intake") or "").strip()
        physical_activity = (request.form.get("physical_activity") or "").strip()
        acne_severity = (request.form.get("acne_severity") or "").strip()
        fg_score = (request.form.get("fg_score") or "").strip()

        #Function to convert blank string to None (NULL) for optional fields
        def parse_optional(val):
            return float(val) if val.strip() else None

        #Extracting values from optional fields using the parse_optional function
        lh_level = parse_optional(request.form.get("lh_level" or ""))
        fsh_level = parse_optional(request.form.get("fsh_level" or ""))
        glucose_level = parse_optional(request.form.get("glucose_level" or ""))
        insulin_level = parse_optional(request.form.get("insulin_level" or ""))
        total_tes = parse_optional(request.form.get("total_tes" or ""))
        free_tes = parse_optional(request.form.get("free_tes" or ""))
        cholesterol = parse_optional(request.form.get("cholesterol" or ""))
        triglycerides = parse_optional(request.form.get("triglycerides" or ""))

        #Mapping yes/no radio button answers to 1/0 for the database
        menstrual_irregularity = 1 if request.form.get("menstrual_irregularity") == "Yes" else 0
        pcos_diagnosis = 1 if request.form.get("pcos_diagnosis") == "Yes" else 0
        alopecia = 1 if request.form.get("alopecia") == "Yes" else 0
        acanthosis = 1 if request.form.get("acanthosis") == "Yes" else 0
        hirsutism = 1 if request.form.get("hirsutism") == "Yes" else 0

        #Calculation for the BMI
        try:
            height_m = float(height) / 100
            bmi = round(float(weight) / (height_m * height_m), 1)
        except ValueError:
            bmi = None

        #Calculation for the HOMA IR level
        try:
            homa_ir = (insulin_level / glucose_level) / 405
        except ValueError:
            homa_ir = None

        #Calculation for LH/FSH Ratio
        try: 
            lh_fsh_ratio = lh_level / fsh_level
        except ValueError: 
            lh_fsh_ratio = None

        #Using the session ID (user email) to make sure the data is inserted to the record of the logged in user
        user_email = session["ID"]

        try:

            ## ---- SERVER-SIDE INPUT VALIDATION FOR REGISTRATION FORM ---- ##

            # ----- Checking empty fields -----
             if not age:
                 raise ValueError("Age is required")
             if not height:
                 raise ValueError("Height is required")
             if not weight:
                 raise ValueError("Weight is required.")
             if not cycle_length:
                 raise ValueError("Cycle length is required.")
             if not sugar_intake:
                 raise ValueError("Sugar intake is required.")
             if not physical_activity:
                 raise ValueError("Physical activity level is required.")
             if not physical_activity:
                 raise ValueError("Physical activity level is required.")
             if not acne_severity:
                 raise ValueError("Acne severity is required.")
             if not fg_score:
                 raise ValueError("Ferriman-Gallwey Hirsutism is required.")
            
             patient_data_for_vector = {
                 'HOMA_IR': homa_ir,
                 'Fasting_Glucose_mg_dL': glucose_level,
                 'Triglycerides_mg_dL': triglycerides,
                 'Acne_Severity': int(acne_severity),
                 'PCOS_Diagnosis': int(pcos_diagnosis),
                 'BMI': bmi,
                 'Total_Testosterone_ng_dL': total_tes
             }
            # ----- Generating and inserting the nutrition vector -----
             try:
                vector = nutrient_vector_2(patient_data_for_vector)
                vector_json = json.dumps(vector)
             except Exception:
                 vector_json = json.dumps([0, 0, 0, 0, 0])
             

            # ----- Inserting the data into the database -----
             try:
                 conn = sqlite3.connect(DB_PATH)
                 cursor = conn.cursor()

                 #SQL query to UPDATE the existing user's row with the new data
                 cursor.execute("""
                    UPDATE patientdata
                    SET Age = ?, Height_cm = ?, Weight_kg = ?, BMI = ?, Menstrual_Cycle_Length_days = ?,
                                Menstrual_Irregularity = ?, PCOS_Diagnosis = ?, Dietary_Sugar_Intake = ?, Physical_Activity_Level = ?,
                                Acne_Severity = ?, Alopecia = ?, Skin_Darkening_Acanthosis = ?, Hirsutism_Score_FG = ?,
                                LH_mIU_mL = ?, FSH_mIU_mL = ?, LH_FSH_Ratio = ?, Fasting_Glucose_mg_dL = ?, Fasting_Insulin_uIU_mL = ?,
                                HOMA_IR = ?, Total_Testosterone_ng_dL = ?, Free_Testosterone_pg_mL = ? , Total_Cholesterol_mg_dL = ?, Triglycerides_mg_dL = ?, Target_Nutrient_Vector = ?
                    WHERE email = ?
                 """, (
                    age, height, weight, bmi, cycle_length, 
                    menstrual_irregularity, pcos_diagnosis, sugar_intake, physical_activity,
                    acne_severity, alopecia, acanthosis, fg_score, 
                    lh_level, fsh_level, lh_fsh_ratio, glucose_level, 
                    insulin_level, homa_ir, total_tes, free_tes, 
                    cholesterol, triglycerides, vector_json, user_email
                 ))  
             
                 conn.commit()
                 flash("Your health profile was updated successfully.")
                 return redirect(url_for("dashboard"))
        
             except Exception as e:
                flash(f"An error occured while saving: {str(e)}", "error")
                log.warning("Database error during questionnaire update: %s", e)
             finally:
                conn.close()

        except ValueError as e:
            flash(str(e), 'error')
            log.warning("Validation failed: %s", e)
            return redirect(url_for("questionnaire"))

    return render_template('questionnaire.html')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)  