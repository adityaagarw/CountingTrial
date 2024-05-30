# Install Anaconda 
FROM continuumio/anaconda3 

# Create conda environment with python 3.11
RUN conda create --name ultralytics-env python=3.11 -y

# Activate environment
SHELL ["conda", "run", "-n", "ultralytics-env", "/bin/bash", "-c"]

# Install CUDA and cuDNN  
RUN conda install -c anaconda cudatoolkit cudnn

# Install Pytorch and torchvision with CUDA support  
RUN conda install -c pytorch -c nvidia -c conda-forge pytorch torchvision pytorch-cuda=11.8 ultralytics

# Install opencv and other packages
RUN pip install opencv-python

# Install dependencies
RUN apt-get update && apt-get install coreutils libgl1-mesa-glx ffmpeg libsm6 libxext6 libegl1 libopengl0 gcc -y


# Set the working directory to the mounted volume
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Run uvicorn command inside the conda environment
#CMD ["conda", "run", "-n", "ultralytics-env", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#CMD ["sh", "-c", "conda run -n ultralytics-env uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug > /app/uvicorn.log 2>&1"]
CMD ["sh", "-c", "conda init bash && . /opt/conda/etc/profile.d/conda.sh && conda activate ultralytics-env && uvicorn app.main:app --log-level debug --host 0.0.0.0 --port 8000 --reload > /app/uvicorn.log 2>&1"]
#CMD ["tail", "-f", "/dev/null"]