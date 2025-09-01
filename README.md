# My Disaster Planner

A web app to help caregivers create personalized disaster preparedness plans for older adults and other vulnerable individuals. Preparing for a disaster can be an overwhelming process, and our web app is designed to simplify it by providing a step-by-step, guided workflow. 

**Award winner at the 2025 Tech for Aging Hackathon** hosted by the Center for Innovation, Technology, and Aging at the University of South Florida.

---
### Dashboard
![7_quicklinks](https://github.com/user-attachments/assets/9b43a8df-51a7-474a-bf89-afc4853284aa)
### Guided Planning Process
![5_plan_process](https://github.com/user-attachments/assets/87532c98-1d9e-4366-9aea-36b6c28e1cf0)
### AI-Powered Planning Assistant
![6_Chatbot](https://github.com/user-attachments/assets/1499b578-c95e-49cf-a5e5-e32aee06ebd7)

### Key Features

* **Guided Workflow**: A modular wizard that walks users through each stage of planning, saving their progress along the way.
* **Location-based Risk Analysis**: Integrates with external APIs to provide location-based data:
    * **Google Geocoding & FEMA Flood Map API**: Converts addresses to coordinates and assesses the flood risk for a user's specific address.
    * **Google Routes API**: Calculates travel time to evacuation destinations.
* **AI-Powered Planning Assistant**: A Retrieval-Augmented Generation (RAG) chatbot built with LlamaIndex provides instant, context-aware answers to disaster preparedness questions.
* **Florida-Specific Tailoring**: Automatically provides users in Florida with a direct link to their local county's emergency management website for the most accurate local guidance.
* **Dynamic PDF Generation**: Creates a final, personalized PDF disaster plan tailored to each user's specific needs.
* **Secure Storage & Delivery**: Stores generated plans securely in Amazon S3 and can deliver them directly to users via email.
* **Responsive Design**: A clean, modern, and fully responsive interface built to be accessible on desktop, tablet, and mobile devices.

---

## Tech Stack

* **Backend**: Python, Flask
* **Frontend**: HTML5, CSS, JavaScript, Bootstrap 5
* **Database & ORM**: PostgreSQL, SQLAlchemy
* **AI Chatbot**: LlamaIndex, OpenAI API
* **Deployment**: AWS, Docker, Nginx
* **APIs & Services**:
    * Google APIs (Geocoding, Routes)
    * FEMA Flood Map API
    * Mailjet (for email delivery)
    * WeasyPrint (for PDF generation)

---
