#Ubuntu bask image
FROM ubuntu:20.04

# Set the working directory as /app
WORKDIR /app

# Install all necessary packages and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv
# Copy the necessary files into the container from flaskr directory
COPY ./flaskr/static /app/flaskr/static
COPY ./flaskr/templates /app/flaskr/templates
COPY ./flaskr/__init__.py /app/flaskr/
COPY ./flaskr/auth.py /app/flaskr/
COPY ./flaskr/db.py /app/flaskr/
COPY ./flaskr/jokes.py /app/flaskr/
COPY ./flaskr/schema.sql /app/flaskr/

# Copy the pyproject.toml into container
COPY pyproject.toml /app/

# Create a virtual environment in the container
RUN python3 -m venv /app/.venv
RUN /app/.venv/bin/pip install .

# Set default path for the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Initialize the database
RUN flask --app flaskr init-db

# Run the app
CMD ["flask", "--app", "flaskr", "run", "--host=0.0.0.0", "--debug"]

# docker build -t flaskr .
# docker run -p 5001:5000 flaskr
# go to http://localhost:5001/ in your browser