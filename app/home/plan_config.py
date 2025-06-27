# Define the labels for all steps
all_steps = [
    "Information", 
    "Risk Assessment", 
    "Plan", 
    "Final Steps",
]

# Steps total for the questionnaire
TOTAL_PLAN_STEPS = len(all_steps)

form_data_lists = {
    1: ['health_conditions_list'],
    3: ['gokit_docs', 'gokit_supplies', 'gokit_comfort', 'gokit_medical', 'secure_home_items', 'staykit_items', 'power_comfort_items'],
}

risk_assessment_questions = {
    "must_evac_q1": {
        1: "Are you in a high-risk evacuation zone or an area with a history of flooding?",
        0: "Is the person in your care in a high-risk evacuation zone or an area with a history of flooding?"
    },
    "must_evac_q2": {
        1: "Is your home a mobile home, RV, or manufactured home?",
        0: "Is their home a mobile home, RV, or manufactured home?"
    },
    "must_evac_q3": {
        1: "Do you rely on electric medical devices (e.g., oxygen, CPAP, nebulizer, or feeding tubes) and do not have a reliable generator?",
        0: "Do they rely on electric medical devices (e.g., oxygen, CPAP, nebulizer, or feeding tubes) and do not have a reliable generator?"
    },
    "must_evac_q4": {
        1: "Are you at high risk for heat-related illness if the A/C fails?",
        0: "Are they at high risk for heat-related illness if the A/C fails?"
    },
    "must_evac_q5": {
        1: "Is your home a high-rise where a power outage where a power outage would leave you without access to an elevator or water?",
        0: "Is their home a high-rise where a power outage where a power outage would leave you without access to an elevator or water?"
    },
    "shelter_q1": {
        1: "Can your home withstand hurricane-force winds (considering the roof, windows, and whether garage doors can be secured from the inside)?",
        0: "Can their home withstand hurricane-force winds (considering the roof, windows, and whether garage doors can be secured from the inside)?"
    },
    "shelter_q2": {
        1: "Is there a reliable support person nearby who can provide physical assistance if needed?",
        0: "Is there a reliable support person nearby who can provide physical assistance to your care recipient if needed?"
    },
    "shelter_q3": {
        1: "Are there enough supplies (food, water, medications) to last at least 7 days without outside help?",
        0: "Are there enough supplies (food, water, medications) to last at least 7 days without outside help?"
    },
}