FROM registry.fedoraproject.org/fedora:latest
COPY requirements.txt .
RUN dnf install -y graphviz pip && \
    pip install -r requirements.txt
