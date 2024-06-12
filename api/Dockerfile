FROM python:3.9
WORKDIR /api
COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
COPY . .

CMD ["fastapi", "run", "main.py", "--port", "8000"]
