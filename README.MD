1. Запускаем локально Ollama с предзагруженной моделью gpt-oss:20b (модель задается переменной model
   в [llm.py](app/services/llm.py)).
2. Запускаем MongoDb в контейнере при помощи прилагаемого [docker-compose.yml](docker-compose.yml)
3. Запускаем само приложение, используя [main.py](app/main.py) (например через uvicorn app.main:app --reload)
4. Проверка работы:

```
curl -X POST http://127.0.0.1:8000/api/v1/check \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "task_001",
    "reference_answer_id": "reference_answer_001",
    "prompt_id": "default_v1",
    "candidate_answer": "Карандаш лежит у стены, что делает прыжок через него невозможным без столкновения с препятствием"
}'
  ```