# Use an official Ubuntu 16.04 (Xenial Xerus) runtime as a parent image
FROM ubuntu:xenial

RUN apt-get update && apt-get upgrade -y
RUN apt-get -y install build-essential cmake \
                                       cppcheck \
                                       xsltproc \
                                       python \
                                       mercurial \
                                       git
RUN apt-get -y install python python-pip

# Set the working directory to /app
WORKDIR /revolve

# Copy the current directory contents into the container at /app
ADD . /revolve

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Define environment variable
ENV NAME Revolve

# Run app.py when the container launches
CMD ["python", "-m", "unittest", "discover"]
