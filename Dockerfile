FROM python:3.7-alpine

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY awair_exporter.py .

EXPOSE 8000

CMD [ "python", "./awair_exporter.py" ]