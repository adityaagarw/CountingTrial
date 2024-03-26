# Use the official Python image as the base image
# FROM python:3.11.8

# Install Conda
# RUN apt-get update && apt-get install -y wget
# RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda
# ENV PATH="/opt/conda/bin:$PATH"

FROM ankane/pgvector:latest

# Set environment variables for PostgreSQL
ENV POSTGRES_USER=avian-admin
ENV POSTGRES_PASSWORD=avian-password
ENV POSTGRES_DB=avian-db

# Install PostgreSQL
# RUN apt-get update && apt-get install -y postgresql

# Expose PostgreSQL port
EXPOSE 5432

# Install Python dependencies from requirements.txt
# COPY requirements.txt /app/requirements.txt
WORKDIR /app
# RUN pip install -r requirements.txt

# Start PostgreSQL container
# CMD ["docker", "run", "-d", "--name", "avian-pgsql", "-e", "POSTGRES_USER=avian-admin", "-e", "POSTGRES_PASSWORD=avian-password", "-e", "POSTGRES_DB=avian-db", "postgres"]
CMD ["postgres"]  