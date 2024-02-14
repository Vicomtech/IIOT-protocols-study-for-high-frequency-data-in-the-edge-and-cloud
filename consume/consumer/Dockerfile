FROM continuumio/miniconda3

# para poder hacer ping y hacer que el contenedor tarde en lanzarse
RUN apt-get update && apt-get install -y iputils-ping

WORKDIR /app

# Copy the conda environment file
COPY environment.yml .
# Create the environment from file and clean the image
RUN conda env create -f environment.yml && conda clean -afy
COPY . .


# Make RUN commands use the new environment:
SHELL ["conda", "run", "-n", "ertzean", "/bin/bash", "-c"]

# The code to run when container is started:
WORKDIR /app/app
ENTRYPOINT ["/bin/sh", "-c" , "ping -c 10 127.0.0.1 > null && conda run --no-capture-output -n ertzean python run_consumer.py"]

#Dev Container
#ENTRYPOINT ["tail", "-f", "/dev/null"]



