FROM python:3.13-slim-bullseye

ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file and install them
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Pre-build the AI index during the image build process
# This RUN command will execute our app factory, which in turn calls
# the initialize_ai_services() function to build the index.
# This makes our container start little faster in production.
RUN python -c "from app import create_app; create_app()"

# Expose the port Gunicorn will run on
EXPOSE 5000

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "5", "--timeout", "120", "run:app"]

