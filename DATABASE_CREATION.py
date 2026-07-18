# Database creation for application

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
from RECOMMENDER_LOGIC import populate_db, save_food_to_db

#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#CLEAN_DATA_PATH = os.path.join(BASE_DIR, 'cleandata.csv')
#PATIENT_DATA_PATH = os.path.join(BASE_DIR, 'patientdata.csv')

#Set Seed
SEED_VAL = 55
random.seed(SEED_VAL)
np.random.seed(SEED_VAL)

#Run code to process raw excel file data
#Patientdata.csv is patient data with nutrition vectors and hashed passwords
#Patientdata_nohash.csv is the patient data with nutrition vectors and unhashed passwords
process_raw_file() 

def init_db():

    #Populating the db with patient data that has encrypted passwords
    populate_db()

    #Saving the food matrix to the database
    save_food_to_db()

