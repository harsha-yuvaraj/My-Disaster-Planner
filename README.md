# TASH
This project is a disaster prepardenss app unders the supervision of School of Aging Studies at College of Behavioral and Community Sciences at USF . This app is designed to help caregivers and care recipients plan their next steps in the event of an emergency or natural disaster.

# Things to keep in mind while developing 

1. Use Virtual Environment (update requirements.txt after pip install). 
2. Running the Application in local: flask run
3. Database Migrations (important):
     - Generate a New Migration Script (after model changes): flask db migrate -m "Descriptive message about changes"
     - Apply Migrations to the Database: flask db upgrade





4- FetchAPI AI is in two files -> chatbot.py and llm.py -> not a RAG , just a generic llm called with an API




5- RAG model is in rag.py with its req in a txt file

