FROM cakecrusher/flask-ocr

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD [ "python", "server.py" ]