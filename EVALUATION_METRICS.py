#Evaluation metrics file

#Importing essential libraries
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import itertools

#Setting seed for reproducibility
np.random.seed(55)

#--------------Catalogue Coverage Quality Metric----------------
# Catalogue Coverage = (Counter of Unique Food Items Recommended / Total items in Catalogue) x 100

#Creating a function to loop through all 468 patient records
def food_catalogue_coverage(patient_df, food_db, vector_function, recommender_function, food_scaled_db=None, scalerobj=None, top_n=10):
    #Calculating the percentage of unique foods used across the entire patient dataset

    #Parameters:
    #patient_df: Pandas dataframe of PCOS patients
    #food_db: Pandas dataframe of the food matrix
    #vector_function: The specific python function used to calculate the nutrient vector
    #recommender_function: The specific python function used to calculate cosine similarity
    #top_n: Number of recommendations per user

    #Initialising an empty set to collect only unique recommended food names and avoid duplicates
    unique_foods = set()

    #Looping through each patient record in the dataset
    for index, patient_record in patient_df.iterrows():

        #Applying the nutrient vector logic to each vector
        patient_vector = vector_function(patient_record)

        #Passing the nutrient vectors into the Cosine Similarity recommender logic
        #Returning the top 10 foods recommended to each patient
        if food_scaled_db is not None and scalerobj is not None:
            top_foods_df = recommender_function(patient_vector, food_db, food_scaled_db, scalerobj, top_n=top_n)
        else:
            top_foods_df = recommender_function(patient_vector, food_db, top_n=top_n)

        #Extracting the food names from the recommendations
        if top_foods_df is not None and not top_foods_df.empty:
            #Assuming the food name is either the index or a specific column named 'food_description'
            if 'food_description' in top_foods_df.columns:
                food_names = top_foods_df['food_description'].tolist()
            else:
                food_names = top_foods_df.index.tolist()

            #Adding these names to the unique foods set
            unique_foods.update(food_names)

    #Calculating the percentage of unique foods recommended out of total food database
    total_unique_foods_recommended = len(unique_foods)
    total_foods = len(food_db)

    percentage_covered = (total_unique_foods_recommended / total_foods) * 100

    #Printing the metrics 
    print("Food Recommender Catalogue Coverage")
    print(f"Total Unique Foods in Food Database: {total_foods}")
    print(f"Number of Unique Foods Recommended: {total_unique_foods_recommended}")
    print(f"Percentage of Unique Foods Recommended out of Total Foods: {percentage_covered:.2f}%")

    return percentage_covered


#--------------Intra-List Diversity Metric----------------
# Intra-List Diversity = Measuring the variety of items within a single user's list. 
# Calculates the average dissimilarity between pairs of recommended items in a list.
# Diversity = 1 - Average Cosine Similarity of pairs within a single recommendation

def intra_list_diversity(patient_df, food_db, vector_function, recommender_function, food_scaled_db=None, scalerobj=None, top_n=10):

    diversity_scores = []

    #Retrieve order of nutrients
    nutrients_5d_order = [
            'Fibre, total dietary', 
            'Fatty acids, total polyunsaturated',
            'Magnesium, Mg',
            'Vitamin_D_Total_UG',
            'Zinc, Zn'
        ]

    for index, patient_record in patient_df.iterrows():

        #Generating vector and recommendations
        patient_vector = vector_function(patient_record)

        #Passing the nutrient vectors into the Cosine Similarity recommender logic
        #Returning the top 10 foods recommended to each patient
        if food_scaled_db is not None and scalerobj is not None:
            top_foods_df = recommender_function(patient_vector, food_db, food_scaled_db, scalerobj, top_n=top_n)
        else:
            top_foods_df = recommender_function(patient_vector, food_db, top_n=top_n)

        #Skipping algorithm if not enough foods to compare
        if top_foods_df is None or len(top_foods_df) < 2:
            continue

        #Extracting raw nutrient values for top 10 foods
        food_vectors = top_foods_df[nutrients_5d_order].values

        #Calculating the similarity between recommended foods in the specific list
        similarity_matrix = cosine_similarity(food_vectors)

        #Extracting the upper triangle of the matrix
        #Excluding the diagonal
        #This is to prevent comparing an item to itself
        #Prevention of counting the same pair twice
        upper_tri_indices = np.triu_indices(n=len(food_vectors), k=1)
        pairwise_similarities = similarity_matrix[upper_tri_indices]

        #Averaging the similarity and subtracting 1 to get Diversity
        avg_list_similarity = np.mean(pairwise_similarities)
        list_diversity = 1.0 - avg_list_similarity

        #Appending the diversity scores
        diversity_scores.append(list_diversity)

    #Averaging diversity scores across all 468 patients
    system_diversity = np.mean(diversity_scores) * 100

    print("Recommender Intra-List Diversity")
    print(f"Average Diversity Score: {system_diversity: .2f}%")

    return system_diversity

#--------------Personalisation: Inter-List Diversity----------------
#Measures the average uniqueness of recommendation lists between all pairs of users
def inter_list_diversity(patient_df, food_db, vector_function, recommender_function, food_scaled_db=None, scalerobj=None, top_n=10):

    all_user_lists = []

    #Collecting recommendation lists from all patients
    for index, patient_record in patient_df.iterrows():
    
        #Generating vector and recommendations
        patient_vector = vector_function(patient_record)

        #Passing the nutrient vectors into the Cosine Similarity recommender logic
        #Returning the top 10 foods recommended to each patient
        if food_scaled_db is not None and scalerobj is not None:
            top_foods_df = recommender_function(patient_vector, food_db, food_scaled_db, scalerobj, top_n=top_n)
        else:
            top_foods_df = recommender_function(patient_vector, food_db, top_n=top_n)

        #Skipping algorithm if not enough foods to compare
        if top_foods_df is None or len(top_foods_df) < 1:
            continue

        #Extracting food names as a Python 'set' to easily calculate overlaps
        if 'food_description' in top_foods_df.columns:
            food_set = set(top_foods_df['food_description'].tolist())
        else:
            food_set = set(top_foods_df.index.tolist())

        all_user_lists.append(food_set)

    #Calculating the overlap for every possible pair of users
    overlaps = []

    #Utilising itertools.combinations 
    #This automatically pairs all usrs without duplicating pairs
    for list_a, list_b in itertools.combinations(all_user_lists, 2):
        #Counting identical foods between two lists
        shared_items = len(list_a.intersection(list_b))

        #Calculating the overlap ratio
        #For example: 4 shared items / 10 = 0.4
        overlap_ratio = shared_items / top_n
        overlaps.append(overlap_ratio)

    #Calculating the final personalisation score
    if not overlaps:
        return 0.0
    
    #Taking the average of the overlaps
    average_overlap = np.mean(overlaps)

    #Personalisation is the opposite percentage of overlap
    #Personalisation = (1 - overlap) x 100
    personalisation_score = (1.0 - average_overlap) * 100

    print("System Personalisation Inter-List Diversity")
    print(f"Total Patient Pairs Compared: {len(overlaps)}")
    print(f"Average Personalisation Score: {personalisation_score:.2f}%")

    return personalisation_score

#--------------Nutrient Contribution Metric----------------
#Calculates the percentage of a patient's target nutrients needs are met by the top N foods.

def nutrient_contribution_test(patient_df, food_db, vector_function, recommender_function, food_scaled_db=None, scalerobj=None, top_n=10):
    #Retrieve order of nutrients
    nutrients_5d_order = [
            'Fibre, total dietary', 
            'Fatty acids, total polyunsaturated',
            'Magnesium, Mg',
            'Vitamin_D_Total_UG',
            'Zinc, Zn'
    ]

    #Dictionaries to track the percentages across all patients
    nutrient_fulfillment = {
        'Fibre': [],
        'PUFAs': [],
        'Magnesium':[],
        'Vitamin D': [],
        'Zinc': []
    }

    for index, patient_record in patient_df.iterrows():
        #Generating vector and recommendations
        patient_vector = vector_function(patient_record)

        #Passing the nutrient vectors into the Cosine Similarity recommender logic
        #Returning the top 10 foods recommended to each patient
        if food_scaled_db is not None and scalerobj is not None:
            top_foods_df = recommender_function(patient_vector, food_db, food_scaled_db, scalerobj, top_n=top_n)
        else:
            top_foods_df = recommender_function(patient_vector, food_db, top_n=top_n)

        #Skipping algorithm if not enough foods to compare
        if top_foods_df is None or top_foods_df.empty:
            continue

        #Add all the actual nutrients provided by the top N recommended foods
        provided_nutrients = top_foods_df[nutrients_5d_order].sum().values

        #Calculating the percentage of the target that was met for each nutrient
        for i, key in enumerate(nutrient_fulfillment.keys()):
            target = patient_vector[i]
            provided = provided_nutrients[i]

            if target > 0:
                fulfillment = ( provided / target) * 100
            else: 
                fulfillment = 100.0 #To prevent division by zero
                #There is baseline of nutrients incase

            nutrient_fulfillment[key].append(fulfillment)

    #Calculating the system averages across all 468 patients
    print("Nutrient Contribution Test (Relevance)")
    print(f"Average fulfillment of daily targets by the Top-{top_n} recommendations:") 

    final_scores = {}
    for key, values in nutrient_fulfillment.items():
        avg_score = np.mean(values)
        final_scores[key] = avg_score
        print(f"- {key}: {avg_score:.2f}%")

    return final_scores

            
        






