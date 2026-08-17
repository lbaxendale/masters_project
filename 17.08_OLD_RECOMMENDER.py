#Nutrient reccomender python logic
def nutrient_vector_2(patient_record):

    # Set a baseline daily reccomended intake of nutrients
    magnesium = 320.0 #milligrams
    fibre = 25.0 #grams
    PUFA = 12.0 #grams
    zinc = 7.0 #milligrams 25mg max
    vitamin_d = 10.0 #micrograms (1000 times smaller than a milligram) max 50ug

    #Retrieving the patient data from user
    homa_ir = patient_record.get('HOMA_IR') or 0
    glucose = patient_record.get('Fasting_Glucose_mg_dL') or 0 
    triglycerides = patient_record.get('Triglycerides_mg_dL') or 0 
    acne = patient_record.get('Acne_Severity') or 0
    pcos = patient_record.get('PCOS_Diagnosis') or 0 
    bmi = patient_record.get('BMI') or 0
    testosterone = patient_record.get('Total_Testosterone_ng_dL') or 0
    vitamin_d_level = patient_record.get('Vitamin_D_ng_mL') or 0

    #Fiber recommendation logic
    #High HOMA IR or high Fasting Glucose level can indicate insulin resistance
    #Using a continuous proportional multiplier with 15g as a safety cap  
    if homa_ir > 1.9 or glucose > 99:
        fibre_addition = homa_ir - 1.9 if homa_ir > 1.9 else 0
        fibre += min(15.0, fibre_addition * 1.5)

    #Omega 3 / Polyunsaturated fat reccommendation logic
    #High triglycerides and the presence of severe acne can indicate high lipids and inflammation
    #Omega 3 can lower lipid levels and combat skin inflammation
    #Using a continuous proportional multiplier with 10g as a safety cap
    if 150 <= triglycerides > 199 and acne == 3: 
        PUFA_addition = triglycerides - 199
        PUFA += min(10.0, PUFA_addition * 1.8)
    elif 150 <= triglycerides > 199 and acne ==2:
        PUFA_addition = triglycerides - 199
        PUFA += min(10.0, PUFA_addition * 1.5)
    elif 150 <= triglycerides > 199 and acne == 1:
        PUFA_addition = triglycerides - 199
        PUFA += min(10.0, PUFA_addition * 1.3)

    #Magnesium reccomendation logic
    #Magnesium can support insulin resistance and hormonal imbalance
    #Using a continuous proportional multiplier with 80mg as a safety cap
    if homa_ir > 1.9 and pcos == 1:
        magnesium_addition = homa_ir - 1.9
        magnesium += min(80, magnesium_addition * 10)

    if homa_ir > 1.9 and pcos == 0:
        magnesium_addition = homa_ir - 1.9
        magnesium += min(80, magnesium_addition * 7.5)


    #Vitamin D recommendation logic
    #Vitamin D can support patients with hormonal imbalance, insulin resistance and hirsutism
    #Using a continuous proportional multiplier with 80mg as a safety cap
    if bmi > 25 and vitamin_d_level < 10:
        vitamin_d_addition = bmi - 25
        vitamin_d += min(40, vitamin_d_addition * 2.5)

    if bmi > 25 and 10 <= vitamin_d_level < 20:
        vitamin_d_addition = bmi - 25
        vitamin_d += min(40, vitamin_d_addition * 1.5)
    

    #Zinc recommendation logic
    #Zinc can support PCOS patients with hirsutism, alopecia
    if testosterone > 46:
        zinc_addition = testosterone - 46
        zinc += min(18, zinc_addition * 1.5)

    #Round the nutrient figures
    return [round(fibre, 1), round(PUFA, 1), round(magnesium, 1), round(vitamin_d, 1), round(zinc, 1)]