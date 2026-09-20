# openrouter-proxy

Крошечный прокси для OpenRouter, чтобы обойти блокировку по IP (РФ-сервер -> Render US -> OpenRouter).

## Деплой на Render
1. Залей эти файлы в отдельный GitHub-репозиторий.
2. render.com -> New + -> Web Service -> подключи репозиторий.
3. Runtime: Python 3. Build: `pip install -r requirements.txt`.
   Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`. Instance: Free.
4. Create Web Service, дождись деплоя, скопируй URL вида https://xxx.onrender.com
5. Проверь: открой URL в браузере -> {"status":"ok",...}

## Подключение к ADS-ENGINE
В .env основного проекта добавь строку (с /v1 на конце!):
OPENROUTER_BASE=https://xxx.onrender.com/v1

Перезапусти ADS-ENGINE. Ключ OpenRouter остаётся в .env ADS-ENGINE — прокси его только пересылает.
