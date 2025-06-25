# Define the labels for all steps
all_steps = [
    "Information", 
    "Risk Assessment", 
    "Plan", 
    "Evacuation", 
    "Communicate", 
    "Review"
]

# Steps total for the questionnaire
TOTAL_PLAN_STEPS = len(all_steps)

form_data_lists = {
    1: ['health_conditions_list'],
    3: ['gokit_docs', 'gokit_supplies', 'gokit_comfort', 'gokit_medical', 'secure_home_items', 'staykit_items', 'power_comfort_items'],
}