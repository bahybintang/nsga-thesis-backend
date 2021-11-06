FROM python:3.8-slim-buster
ENV FLASK_APP app
ENV FLASK_ENV production
ENV CLIENT_ORIGIN *
WORKDIR /app
COPY app .
RUN pip3 install -r requirements.txt
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
