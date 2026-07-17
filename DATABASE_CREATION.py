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
from RECOMMENDER_LOGIC import hash_and_populate, save_food_to_db

#Set Seed
SEED_VAL = 55
random.seed(SEED_VAL)
np.random.seed(SEED_VAL)

DB_PATH = "patientdb.db"
CSV_PATH = "cleandata.csv"

#Run code to process raw excel file data
process_raw_file() #Creates the cleandata.csv file

#Populating the db with patient data that has encrypted passwords
hash_and_populate("patientdata.csv")

save_food_to_db()


