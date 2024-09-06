# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libsqlite3-dev

# Install the required version of SQLite
RUN wget https://www.sqlite.org/2023/sqlite-autoconf-3410000.tar.gz && \
    tar xvfz sqlite-autoconf-3410000.tar.gz && \
    cd sqlite-autoconf-3410000 && \
    ./configure && \
    make && \
    make install && \
    cd .. && \
    rm -rf sqlite-autoconf-3410000*

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app/main.py"]