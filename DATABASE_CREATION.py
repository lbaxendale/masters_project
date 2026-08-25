# Database creation for application

#Importing Libraries
import random
import numpy as np

#Setting seed for reproducibility
np.random.seed(55)

from DATA_ENGINEERING import process_raw_file
from RECOMMENDER_LOGIC import populate_db, save_food_to_db

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
