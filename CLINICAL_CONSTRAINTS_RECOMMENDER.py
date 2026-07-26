#Hard clinical constraints to introduce hybrid filtering 

#Vitamin D is not present in a lot of foods
#Recommended foods show up with near zero Vitamin D due to
#Vector Dot Product
#Before running the Cosine Similarity Calculation:
#Check for a patient's elevated need for Vitamin D
#If they do, the recommender should apply a filter to the food matrix
#To restrict the search space to find items that contain Vitamin D

def food_recommender_scaled_3(patient_vector, food_db, top_n=10):

    #Nutrient order
    target_fiber = patient_vector[0]
    target_pufa = patient_vector[1]
    target_magnesium = patient_vector[2]
    target_vit_d = patient_vector[3]
    target_zinc = patient_vector[4]

    #Creating copies of databases for filtering
    filtered_food_db = food_db.copy()

    #Elevated need for Magnesium
    if target_fiber > 25:
        #Filtering out the foods that don't contain a lot of Zinc
        fiber_mask = food_db['Fiber, total dietary'] > 0.5
        filtered_food_db = filtered_food_db[fiber_mask]

    #Elevated need for Magnesium
    if target_pufa > 12:
        #Filtering out the foods that don't contain a lot of Zinc
        pufa_mask = food_db['Fatty acids, total polyunsaturated'] > 0.5
        filtered_food_db = filtered_food_db[pufa_mask]

    #Elevated need for Magnesium
    if target_magnesium > 320:
        #Filtering out the foods that don't contain a lot of Zinc
        magnesium_mask = food_db['Magnesium, Mg'] > 0.5
        filtered_food_db = filtered_food_db[magnesium_mask]

    #Elevated need for vitamin D
    if target_vit_d > 10:
        #Filtering out the foods that don't contain a lot of Vitamin D
        vit_d_mask = food_db['Vitamin_D_Total_UG'] > 1.0
        filtered_food_db = filtered_food_db[vit_d_mask]

    #Elevated need for Zinc
    if target_zinc > 7:
        #Filtering out the foods that don't contain a lot of Zinc
        zinc_mask = food_db['Zinc, Zn'] > 0.5
        filtered_food_db = filtered_food_db[zinc_mask]

    #If the filtering is too restrictive and returns nothing, reset to the full database
    if filtered_food_db.empty:
        filtered_food_db = food_db.copy()
    
    #Isolating numeric columns from the filtered database
    nutrients_5d_order = [
        'Fiber, total dietary', 
        'Fatty acids, total polyunsaturated',
        'Magnesium, Mg',
        'Vitamin_D_Total_UG',
        'Zinc, Zn'
    ]
    
    #Filtering
    food_numeric_matrix = filtered_food_db[nutrients_5d_order].values

    #Converting the patient vector to 2D and scaling it normally
    scaler = MinMaxScaler()
    scaled_food_db = scaler.fit_transform(food_numeric_matrix)
    vector_2d = np.array(patient_vector).reshape(1, -1)
    scaled_patient_vector = scaler.transform(vector_2d)

    #Calculating the similarity strictly across the subspace
    score_similarity = cosine_similarity(scaled_patient_vector, scaled_food_db)[0]
    
    #Creating count for the top 10 recommended foods

    #Attaching the scores back and treturning the top results
    results_df = filtered_food_db.copy()
    results_df['Match_Score (%)'] = np.round(score_similarity * 100, 2)
    return results_df.sort_values(by='Match_Score (%)', ascending=False).head(top_n)

        