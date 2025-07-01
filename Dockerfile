FROM python:3.13-slim-bullseye

ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file and install them
COPY requirements.txt .

# Install system-level dependencies required by Python packages (like WeasyPrint for PDF generation)
# This must be done BEFORE installing the Python packages with pip.
RUN apt-get update && apt-get install -y && apt install -y weasyprint 

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port Gunicorn will run on
EXPOSE 5000

# Command to run the application using Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "180", "run:app"]

# For t2.micro on AWS
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "180", "run:app"]
