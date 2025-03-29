import json
from fastapi.testclient import TestClient
from main import app
from processor import process

# Пример тестового сообщения
sample_message = json.dumps({
    "MatchId": "555",
    "Source": "Betcenter",
    "homeName": "Team A",
    "awayName": "Team B",
    "HomeScore": 1,
    "AwayScore": 0,
    "Periods": [{
        "Totals": {
            "1.5": {"WinMore": 1.5, "WinLess": 2.5},
            "2.5": {"WinMore": 2.1, "WinLess": 1.6}
        }
    }]
})

def test_matches_endpoint():
    import asyncio
    asyncio.run(process(sample_message))

    client = TestClient(app)
    response = client.get("/matches")
    assert response.status_code == 200

    data = response.json()
    assert "555" in data
    assert data["555"]["home"] == "Team A"
    assert data["555"]["score"] == "1:0"
    assert "1.5" in data["555"]["totals"]

    print("✅ REST API тест пройден успешно")

if __name__ == "__main__":
    test_matches_endpoint()
