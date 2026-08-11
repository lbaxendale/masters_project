# Unit testing for Flask application

import unittest
import sqlite3
import re
from RECOMMENDER_LOGIC import nutrient_vector_2
from WORKING_APP import app


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

#Old email pattern that failed
#EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}$')

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
