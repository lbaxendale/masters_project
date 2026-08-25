# Unit testing for Flask application

import unittest
import sqlite3
import re
from RECOMMENDER_LOGIC import nutrient_vector_2
from WORKING_APP import app, generate_nutrition_message
from werkzeug.security import generate_password_hash, check_password_hash


#----------Testing Application Routes------------

# ----- 4 Unit Tests: Check That Home, About, Login & Registration Pages Load Successfully ----- #
#Test to check if the website is working
#Creating a test case class:
class TestNutritionSite(unittest.TestCase):
    #Creating a Flask test client 
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    # ----- Test 1: Testing the Home Page ----- #
    def test_homepage_loads(self):
        response = self.client.get('/')

        #First check to see if page loaded properly
        self.assertEqual(response.status_code, 200)

        #2nd check: see if page contains the word 'Hospital'
        page_content = response.data.decode('utf-8')
        self.assertIn("Home", page_content)

        print("Test passed: Home page loaded successfully.")

    # ----- Test 2: Testing the About Page ----- #
    def test_aboutpage(self):
        response = self.client.get('/about')

        #First check to see if page loaded properly
        self.assertEqual(response.status_code, 200)

        #2nd check: see if page contains the word 'About'
        page_content = response.data.decode('utf-8')
        self.assertIn("About", page_content)

        print("Test passed: About page loaded successfully.")

    # ----- Test 3: Testing the Login Page ----- #
    def test_loginpage(self):
        response = self.client.get('/login')

        #First check to see if page loaded properly
        self.assertEqual(response.status_code, 200)

        #2nd check: see if page contains the word 'Login'
        page_content = response.data.decode('utf-8')
        self.assertIn("Login", page_content)

        print("Test passed: Login page loaded successfully.")

        # ----- Test 4: Testing the Registration Page ----- #
    def test_registerpage(self):
        response = self.client.get('/register')

        #First check to see if page loaded properly
        self.assertEqual(response.status_code, 200)

        #2nd check: see if page contains the word 'Registration'
        page_content = response.data.decode('utf-8')
        self.assertIn("Register", page_content)

        print("Test passed: Registration page loaded successfully.")

# ----- SQL Database Unit Tests: Check that database logic works correctly ----- #

#Checking that patients exist in the SQL database
#Checking by email
def patient_exists(email):
    conn = sqlite3.connect("patientdb.db")
    cursor = conn.cursor()

    #Querying the 'patientdata' table 
    cursor.execute("SELECT 1 FROM patientdata WHERE email = ?", (email,))
    result = cursor.fetchone()

    conn.close()

    #Return True if found, False if not
    return result is not None

#Checking that foods exist in the SQL database
#Checking by food_description
def food_exists(food_description):
    conn = sqlite3.connect("patientdb.db")
    cursor = conn.cursor()

    #Querying the 'food_matrix_5d' table 
    cursor.execute("SELECT 1 FROM food_matrix_5d WHERE food_description = ?", (food_description,))
    result = cursor.fetchone()

    conn.close()

    #Return True if found, False if not
    return result is not None

#Defining the test class
class TestDatabase(unittest.TestCase):

    #Test 5: Testing an admin user exists
    def test_patient(self):
        #Username: 'admin1' (Charlie Alpha) inserted by init_db()
        exists = patient_exists('maureen.burgess2@example.com')

        #Should be True
        self.assertTrue(exists)
        print("Test Passed: 'maureen.burgess2@example.com' was found in the database.")

    #Test 6: Testing a food exists
    def test_food(self):
        #Username: 'frose' (Freya Rose) inserted by init_db()
        exists = food_exists('Alaska Pollock,  raw')

        #Should be True
        self.assertTrue(exists)
        print("Test Passed: 'Alaska Pollock,  raw' was found in the database.")
    
    #Test 7: Testing a fake user/patient does not exist
    def test_fakeuser_not_exist(self):
        #Username: 'fakeuser@example.com' was not inserted by init_db()
        exists = patient_exists('fakeuser@example.com')

        #Should be False
        self.assertFalse(exists)
        print("Test Passed: Non-existent user was correctly not found.")

# ----- Data Validation Logic Unit Tests ----- #
#Testing that patterns for inputs in registration form work correctly

## Ensures the email has a basic valid structure of name@domain.tld

#New email pattern: Forces the domain to start with a letter or number
EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[a-zA-Z0-9][\w\.-]+\.[A-Za-z]{2,}$')

## Strong password pattern that requires lowercase, uppercase, digit, special character, and minimum 8 characters.
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$')

#Defining the test class
class TestValidationPatterns(unittest.TestCase):

    #Test 8: Testing Email Regex Validation Pattern works correctly
    def test_email_valid(self):
        #Testing valid emails
        self.assertIsNotNone(EMAIL_PATTERN.fullmatch("patient@example.com")) 
        self.assertIsNotNone(EMAIL_PATTERN.fullmatch("patient.user@domain.co.uk"))

        #Testing Invalid emails
        self.assertIsNone(EMAIL_PATTERN.fullmatch("invalid_address"))
        self.assertIsNone(EMAIL_PATTERN.fullmatch("@no.username.com")) 
        self.assertIsNone(EMAIL_PATTERN.fullmatch("patient@.com.my")) #no email domain
        print("Test Passed: Email regex validation is working correctly.")

    #Test 9: Testing Password Validation Pattern works correctly 
    def test_password_strength(self):
        #Strong password example should pass
        self.assertIsNotNone(PASSWORD_PATTERN.fullmatch("ValidStrongPass123!"))

        #Weak passwords should fail
        self.assertIsNone(PASSWORD_PATTERN.fullmatch("abc")) #Too short, should be minimum 8 characters
        self.assertIsNone(PASSWORD_PATTERN.fullmatch("justletters")) #No numbers or special characters
        self.assertIsNone(PASSWORD_PATTERN.fullmatch("12345678")) #No letters or special characters
        print("Test Passed: Password validation is working correctly.")

#----------Testing Application Logic------------

# ---Personalised Nutrition Message Generator---
#Testing that raw mathematical input is translated into dietary advice

class TestApplicationLogic(unittest.TestCase):

    #Test 10: Testing the Baseline Nutrition Message
    def test_baseline_message(self):
        #Testing vector at baseline nutrient levels
        #Order: Fibre, PUFA, Magnesium, Vitamin D, Zinc
        baseline_vector = [25.0, 12.0, 320.0, 10.0, 7.0]

        #Expected message for baseline level users
        expected_message = "Nutrifem suggests a balanced baseline diet to safely maintain your current metabolic and hormonal health."

        #Running the function
        result = generate_nutrition_message(baseline_vector)

        #Print that the result matches the expected message
        self.assertEqual(result, expected_message)

    #Test 11: Testing Elevated Needs Nutrition Messages
    def test_elevated_messages(self):

        #Vector that exceeds all 5 nutrient baseline levels
        elevated_needs_vector = [30.0, 15.0, 400.0, 20.0, 10.0]

        #Running the function
        result = generate_nutrition_message(elevated_needs_vector)

        #Asserting that it returns a list instead of a single string
        self.assertIsInstance(result, list)

        #Asserting that exactly 5 messages are generated
        self.assertEqual(len(result), 5)

        #Assserting specific strings that were correctly appended to the list
        self.assertIn("Increased fibre take: this can help manage blood glucose spikes and support insulin sensitivity.")
        self.assertIn("Extra Zinc: this can help manage androgen related symptoms like acne or hair loss.")

        print("Test Passed: Elevated nutrition messages generated correctly.")

    # ---Clinical Mathematical Edge Cases---
    # For Markers such as BMI, HOMA-IR

    #Test 12: Testing BMI calculation accuracy
    def test_bmi(self):
        #Simulating inputs from questionnaire form
        height = "165.5" #cm
        weight = "69.5" #kg

        #BMI calculation logic
        try:
            height_m = float(height) / 100
            bmi = round(float(weight) / (height_m * height_m), 1)
        except ValueError: 
            bmi = None

        #Asserting that the it correctly calculates BMI = 25.4
        self.assertEqual(bmi, 25.4)
        print("Test Passed: The system calculated BMI accurately.")

    #Test 13: Testing HOMA-IR calculation - division by zero vulnerability
    def test_homa_ir_zero_division(self):
        #Simulating a user accidentally entering 0 for fasting glucose
        insulin_level = 15.0
        glucose_level = 0.0

        #Confirming that a ZeroDivisionError occurs using assertRaises
        #When it attempts to divide by 0.0
        with self.assertRaises(ZeroDivisionError):
            homa_ir = (insulin_level / glucose_level) / 405

        print("Test Passed: Successfully identified the ZeroDivisionError vulnerability in the HOMA-IR calculation.")
        
    #Test 14: Testing LH/FSH Ratio Accuracy
    def test_lh_fsh_ratio(self):
        lh_level = 12.0
        fsh_level = 4.0

        try:
            lh_fsh_ratio = lh_level / fsh_level
        except (ValueError, ZeroDivisionError):
            lh_fsh_ratio = None

        #Asserting that a LH level 12 and FSH level 4 yields ratio = 3
        self.assertEqual(lh_fsh_ratio, 3.0)
        print("Test Passed: LH/FSH Ratio calculates accurately.")


    # ---Test Nutrient Vector Function---
    #Testing that a specific patient profile generates the expected mathematical nutrient vector


    #Test 15: Testing patient with healthy levels
    #Their nutrient vector should be at baseline levels
    def test_nutrient_vector_baseline(self):

        #Setting healthy patient health data parameters
        healthy_patient = {
            'HOMA_IR': 1.5,
            'Fasting_Glucose_mg_dL': 85.0,
            'Triglycerides': 90,
            'Acne_Severity': 1,
            'PCOS_Diagnosis': 0,
            'BMI': 22.0,
            'Vitamin_D_ng_mL': 35.0,
            'Total_Testosterone_ng_dL': 30.0
        }

        #Expecting the minimum default baseline vector
        #Order= [Fibre, PUFA, Magnesium, Vitamin D, Zinc]
        expected_vector = [25.0, 12.0, 320.0, 10.0, 7.0]

        #Running the function
        result_vector = nutrient_vector_2(healthy_patient)

        #Asserting the match between the vectors
        self.assertEqual(result_vector, expected_vector)
        print("Test Passed: Nutrient vector outputs accurate baseline for healthy patients.")

    #Test 16: Testing the Nutrient Vector Proportional Multipliers
    def test_nutrient_vector_multipliers(self):

        #Creating patient profile with elevated markers to trigger the multipliers
        elevated_patient = {
            'HOMA_IR': 1.5,
            #HOMA IR Logic triggers these multipliers:
            #Fibre = (3.9 - 1.9 = 2) * 1.5 = +3.0g
            #Mag logic: (3.9 - 1.9 = 2) * 10 = +20.0mg (with PCOS Diagnosis = 1) 

            'Fasting_Glucose_mg_dL': 110.0, #Same mathematical multiplier trigger as HOMA IR

            'Triglycerides': 200.0,
            #Triglycerides triggers this
            #PUFA logic = (200 - 199 = 1) * 1.8 = + 1.8g with Acne = 3

            'Acne_Severity': 3,
            'PCOS_Diagnosis': 1,
            'BMI': 27.0,
            #BMI and low Vitamin D triggers this
            #Vitamin D logic = (27 - 25 = 2) * 2.5 = +5.0ug (with Vitamin D < 10)

            'Vitamin_D_ng_mL': 8.0,
            'Total_Testosterone_ng_dL': 50.0
            #Total testosterone triggers this
            #Zinc = (50 - 46 = 4) * 1.5 = +6.0mg
        }

        #Expected nutrient vector output
        #Order= [Fibre, PUFA, Magnesium, Vitamin D, Zinc]
        expected_vector = [28.0, 13.8, 340.0, 15.0, 13.0]

        #Running the function
        result_vector = nutrient_vector_2(elevated_patient)

        #Asserting the matching vectors
        self.assertEqual(result_vector, expected_vector)
        print("Test Passed: Nutrient vector calculates proportional multipliers accurately.")

    #----Test 17: Testing Patient profile with only Proxy data----
    def test_nutrient_vector_proxy_only(self):
        #Creating a patient profile missing all the optional clinical data, but severe symptoms
        proxy_patient = {
            'HOMA_IR': None,
            'Fasting_Glucose_mgl_dL': None,
            'Triglycerides_mgl_dL': None,
            'Vitamin_D_ng_mL': None,
            'Total_Testosterone_ng_dL': None,

            #Physical symptoms as Proxies
            'BMI': 33.0, #Proxy for fibre and vitamin D
            'Skin_Darkening_Acanthosis': 1, #Proxy for fibre and magnesium
            'Acne_Severity': 3, #Proxy for PUFA
            'PCOS_Diagnosis': 1, #Proxy for magnesium
            'Menstrual_Irregularity': 1, #Proxy for vitamin D
            'Alopecia': 1, #Proxy for zinc
            'Hirsutism_Score_FG': 12.0 #Proxy for zinc
        }

        #Expected vector calculations
        #Fibre= 25.0 + 5.0 (Acanthosis) + 3.0 (BMI) = 33.0
        #PUFA= 12.0 + 6.0 (Acne) = 18.0
        #Magnesium= 320.0 +40.0 (Acanthosis) + 40.0 (PCOS)= 400.0
        #Vitamin D= 10.0 + 10.0 (Irregular cycle) + 15.0 (BMI) = 35.0
        #Zinc: 7.0 = 5.0 (Alopecia) + 3.0p (FG Score) = 14.0
        expected_vector = [33.0, 18.0, 400.0, 35.0, 14.0]

        #Running vector logic
        result_vector = nutrient_vector_2(proxy_patient)

        #Asserting the match between the vectors
        self.assertEqual(result_vector, expected_vector)
        print("Test Passed: Nutrient vector calculated accurately with only proxy symptom data.")

    # ---Password Hashing Security---
    #Testing that passwords are encrypted and stored as hashed passwords instead of plain text

    #Test 18: Testing Password Hashing
    def test_password_hashing(self):

        #Create a mock password
        plain_password = "PlainPass345!"

        #Generating the hash
        hashed_password = generate_password_hash(plain_password, method="pbkdf2: sha256")

        #Asserting that the hash securely hides plain text 
        self.assertNotEqual(hashed_password, plain_password)

        #Verifying that the correct encryption standard is applied
        self.assertTrue(hashed_password.startswith("scrypt") or hashed_password.startswith("pbkdf2:sha256"))

        #Asserting that check_password_hash authenticates the correct password
        self.assertTrue(check_password_hash(hashed_password, plain_password))

        #Asserting that the wrong password is rejected
        self.assertFalse(check_password_hash(hashed_password, "WrongPass522?"))

        print("Test Passed: Password hashing and verification is secure.")