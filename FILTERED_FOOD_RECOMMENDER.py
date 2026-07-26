def get_recommendations(user_email, db_path="patientdb.db", top_n=10):
    conn = sqlite3.connect(db_path)

    #Retrieving user vector
    cursor = conn.cursor()
    cursor.execute("SELECT Target_Nutrient_Vector FROM patientdata WHERE lower(email) = lower(?)", (user_email,))
    row = cursor.fetchone()
    if not row or not row[0]:
        conn.close()
        return None
    
    patient_vector = json.loads(row[0])

    #Retrieving the names of foods to attach them to the matrix
    #Loading the saved food_matrix_5d table 
    food_df = pd.read_sql_query("SELECT * FROM food_matrix_5d", conn)

    #Renaming the Raw DQL nutrient column names
    food_df = food_df.rename(columns={
        "Fiber, total dietary": 'fiber_g',
        "Fatty acids, total polyunsaturated": 'pufa_g',
        "Magnesium, Mg": 'magnesium_mg',
        "Vitamin_D_Total_UG": 'vitamin_d_mcg',
        "Zinc, Zn": 'zinc_mg'
    })

    conn.close()

    #Isolating the 5 nutrients in the vector
    #For scaling
    nutrient_cols = ['fiber_g', 'pufa_g', 'magnesium_mg', 'vitamin_d_mcg', 'zinc_mg']
    
    #Mapping the nutrient values to the food matrix
    food_matrix = food_df[nutrient_cols].values
    patient_matrix = np.array(patient_vector).reshape(1, -1)

    #Scaling the nutrients
    scaler = MinMaxScaler()
    scaled_foods = scaler.fit_transform(food_matrix)
    scaled_patient = scaler.transform(patient_matrix)

    #Running the cosine similarity engine 
    similarity_scores = cosine_similarity(scaled_patient, scaled_foods)[0]
    food_results_df = food_df.copy()
    food_results_df['Match_Score'] = np.round(similarity_scores * 100, 1)

    #Returning the top N items as a list of dictionaries for Jinja2 HTML rendering
    top_foods = food_results_df.sort_values(by='Match_Score', ascending=False).head(top_n)
    return top_foods.to_dict(orient='records')