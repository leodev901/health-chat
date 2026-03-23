FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ /app
# EXPOSE 8080
# CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8080"]
# 파이썬(main.py) 안에서 settings.APP_HOST, APP_PORT를 실행 시킴으로써 Dockerfile을 유연하게 만듭니다.
CMD ["python", "main.py"] 
