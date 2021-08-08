# Voon: Video processing

## Getting Started with Video processing

1. Make sure [docker-compose](https://docs.docker.com/get-started/08_using_compose/) is installed.

2. Run `docker-compose up`

3. Server will be running on [http://localhost:5000](http://localhost:5000)

4. Send the following request to test that the OCR is working properly:
```test
GET http://localhost:5000/test
content-type: application/json
```