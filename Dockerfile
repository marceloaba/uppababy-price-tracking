FROM python:3.10.0rc2-slim

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt /app/
RUN pip3 install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY app/main.py /app/

# Run the application
CMD ["python", "main.py"]