FROM python:3.11-slim-bullseye
LABEL authors="fabcassano"

# Set environment variables
ENV DAGSTER_HOME /opt/dagster
ENV PYTHONPATH /opt/dagster

WORKDIR /home

COPY . .
RUN pip3 install --upgrade pip
RUN pip3 install -r ./requirements.txt
# RUN python3 subscription.py

# FastAPI port
EXPOSE 8000

CMD ["uvicorn", "main:pharma", "--host", "0.0.0.0", "--port", "8000"]