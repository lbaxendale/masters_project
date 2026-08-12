#---------------Evaluation Metrics-----------------

#Importing essential libraries
import sqlite3 
import pandas as pd
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity
from RECOMMENDER_LOGIC import get_recommendations

def run_evaluation_metrics(db_path="patientdb.db"):
    conn = sqlite.connect()