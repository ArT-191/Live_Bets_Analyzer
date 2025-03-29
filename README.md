# Live Bets Analyzer

Прототип системы для анализа live-коэффициентов ставок от разных букмекеров.

## 📦 Возможности

- Приём live-данных от нескольких парсеров (Sansabet, Betcenter, Pinnacle)
- Хранение данных in-memory
- Группировка исходов по тоталам
- Учёт маржи (8%) и расчёт «истинных» коэффициентов
- Расчёт медианы по рынку
- Расчёт ROI для каждого букмекера
- Учёт времени последнего получения и изменения коэффициентов
- Отслеживание порядка обновления данных
- REST API с фильтрацией и сортировкой
- WebSocket для приёма live-данных
- Docker / Docker Compose для быстрой сборки
- Pytest тесты

## 📥 Установка

Склонируйте репозиторий:

```bash
git clone git@github.com:ArT-191/Live_Bets_Analyzer.git
cd Live_Bets_Analyzer

## 🚀 Запуск

### Через Docker

```
docker-compose up --build
```

Приложение будет доступно на:
http://localhost:7100

### Без Docker (локально)

```
pip install -r requirements.txt
uvicorn main:app --reload --port 7100
```

## 📡 WebSocket

Адрес: `ws://localhost:7100/ws`

Пример сообщения от парсера:

```json
{
  "MatchId": "123",
  "Source": "Pinnacle",
  "homeName": "Team A",
  "awayName": "Team B",
  "HomeScore": 0,
  "AwayScore": 1,
  "Periods": [{
    "Totals": {
      "2.5": {
        "WinMore": 1.95,
        "WinLess": 1.85
      }
    }
  }]
}
```

## 🔗 REST API

- `GET /matches` — список всех матчей
- `GET /matches?team=arsenal` — фильтрация по названию команды
- `GET /matches?sort_by=changed_at&order=asc` — сортировка
- `GET /matches/{match_id}` — подробности матча

## 🧪 Тестирование

```
python3 -m pytest -v
```

## 📁 Структура

- `main.py` — WebSocket и REST API
- `processor.py` — логика обработки данных
- `test_processor.py`, `test_api.py` — тесты
- `Dockerfile`, `docker-compose.yml` — контейнеризация
- `requirements.txt` — зависимости
- `log_config.py` — конфигурация логов
- `logs/` — директория логов

---

## ✍️ Автор

[github.com/ArT-191](https://github.com/ArT-191)
