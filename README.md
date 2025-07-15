# My Disaster Planner

A web app to help caregivers create personalized disaster preparedness plans for older adults and other vulnerable individuals. Preparing for a disaster can be an overwhelming process, and our web app is designed to simplify it by providing a step-by-step, guided workflow. 

**Award winner at the 2025 Tech for Aging Hackathon.**

---

### Key Features

* **Guided Workflow**: A modular wizard that walks users through each stage of planning, saving their progress along the way.
* **Location-based Risk Analysis**: Integrates with external APIs to provide live, location-based data:
    * **FEMA Flood API**: Assesses the flood risk for a user's specific address.
    * **Google Geocoding & Routes API**: Converts addresses to coordinates and calculates travel time to evacuation destinations.
* **AI-Powered Chatbot**: A Retrieval-Augmented Generation (RAG) chatbot built with LlamaIndex provides instant answers to disaster preparedness questions.
* **Florida-Specific Tailoring**: Automatically provides users in Florida with a direct link to their local county's emergency management website for the most accurate local guidance.
* **Dynamic PDF Generation**: Creates a final, personalized PDF safety plan tailored to each user's specific needs.
* **Secure Storage & Delivery**: Stores generated plans securely in Amazon S3 and can deliver them directly to users via email.
* **Responsive Design**: A clean, modern, and fully responsive interface built to be accessible on desktop, tablet, and mobile devices.

---

## Tech Stack

* **Backend**: Python, Flask
* **Frontend**: HTML5, CSS, JavaScript, Bootstrap 5
* **Database & ORM**: PostgreSQL, SQLAlchemy
* **RAG Chatbot**: LlamaIndex, OpenAI API
* **Deployment**: AWS, Docker, Nginx
* **APIs & Services**:
    * Google APIs (Geocoding, Routes)
    * FEMA Flood Map API
    * Mailjet (for email delivery)
    * WeasyPrint (for PDF generation)
