   # Use the official Python image from the Docker Hub
   FROM python:3.10-slim

   # Set the working directory in the container
   WORKDIR /app

   # Copy the requirements.txt file into the container
   COPY requirements.txt .

   # Install the dependencies
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy the rest of the application code into the container
   COPY . .

   # Expose the port that Streamlit will run on
   EXPOSE 8501

   # Set environment variables
   ENV PYTHONUNBUFFERED=1

   # Run the Streamlit application
   ENTRYPOINT ["streamlit", "run", "app/main.py"]