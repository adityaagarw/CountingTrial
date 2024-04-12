FROM ankane/pgvector:latest

# Set environment variables for PostgreSQL
ENV POSTGRES_USER=avian-admin
ENV POSTGRES_PASSWORD=avian-password
ENV POSTGRES_DB=avian-db

# Expose PostgreSQL port
EXPOSE 5432

WORKDIR /app

CMD ["postgres"]