FROM python:3.11

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
# Use -p python3 or -p python3.7 to select python version. Default is version 2.
RUN python3 -m venv /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

# Add the application source code.
ADD . /app
WORKDIR /app

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
# ADD requirements.txt /app/requirements.txt

RUN pip install pip --upgrade
RUN pip install -r /app/requirements.txt

# Run command
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
