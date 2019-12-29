# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.7-slim

# Get source files & API key
COPY app.py \
     auth-key-file.json \
     CaptionedWord.py \
     requirements.txt \
     scrape_captions.py \
     ./

# Copy in utils and note where to find them when imported
COPY .not-shady-utils /usr/local/not-shady-utils
ENV PYTHONPATH=$PYTHONPATH:usr/local/not-shady-utils

# Note credential location for use of Google APIs
ENV GOOGLE_APPLICATION_CREDENTIALS=./auth-key-file.json

# Install Python dependencies
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

# Define the entrypoint (we only want this container for this program anyways)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
