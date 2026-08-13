#Evaluation metrics file

#Importing essential libraries

# Catalogue Coverage = (Counter of Unique Food Items Recommended / Total items in Catalogue) x 100

# Intra-List Diversity = Measuring the variety of items within a single user's list. 
# Calculates the average dissimilarity between pairs of recommended items in a list.

# User Coverage = The percentage of users for whom the system is able to generate a valid top-N
# recommendation list

# Inter-List Diversity = Measures how distinct recommendation lists are betweeen different users.
# High personalisation means that User A receives a different set of items than User B.

# Precision = The fraction of recommended items in the top-10 list that are relevant.


#--------------Catalog Coverage Quality Metric----------------
#Baseline Recommender Engine Catalog Coverage Function 
# (IF/ELIF based Nutrient Vector with 3 Nutrients: Fibre, Magnesium, PUFAs)

#Creating a function to loop through all 468 patient records
def food_catalog_coverage(patient_df, food_db, vector_function, recommender_function, food_scaled_db=None, scalerobj=None, top_n=10):
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
    print("Food Recommender Catalog Coverage")
    print(f"Total Unique Foods in Food Database: {total_foods}")
    print(f"Number of Unique Foods Recommended: {total_unique_foods_recommended}")
    print(f"Percentage of Unique Foods Recommended out of Total Foods: {percentage_covered:.2f}%")

    return percentage_covered

