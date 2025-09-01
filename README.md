# My Disaster Planner

A web app to help caregivers create personalized disaster preparedness plans for older adults and other vulnerable individuals. Preparing for a disaster can be an overwhelming process, and our web app is designed to simplify it by providing a step-by-step, guided workflow. 

**Award winner at the 2025 Tech for Aging Hackathon** hosted by The Center for Innovation, Technology, and Aging at the University of South Florida.

---
![4_Main_Dashboard](https://github.com/user-attachments/assets/7aa27e14-547d-4883-b2c4-45bffa618cd9)

### Key Features

* **Guided Workflow**: A modular wizard that walks users through each stage of planning, saving their progress along the way.
* **Location-based Risk Analysis**: Integrates with external APIs to provide location-based data:
    * **Google Geocoding & FEMA Flood Map API**: Converts addresses to coordinates and assesses the flood risk for a user's specific address.
    * **Google Routes API**: Calculates travel time to evacuation destinations.
* **AI Chatbot**: A Retrieval-Augmented Generation (RAG) chatbot built with LlamaIndex provides instant, context-aware answers to disaster preparedness questions.
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
