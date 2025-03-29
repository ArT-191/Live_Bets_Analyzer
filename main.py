from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse
import asyncio
from processor import process, get_matches_state
from typing import Optional, Literal

app = FastAPI()


# Задача для поддержания соединения
async def keep_alive(websocket: WebSocket):
    while True:
        try:
            await asyncio.sleep(10)
            await websocket.send_text("pong")
            print("[PING] Отправлен ping/pong")
        except Exception as e:
            print(f"[PING] Соединение закрыто: {e}")
            break


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("INFO: connection open")
    asyncio.create_task(keep_alive(websocket))

    try:
        while True:
            print("[DEBUG] Жду сообщение...")
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                print("[INFO] Клиент отключился")
                break
            except Exception as e:
                print(f"[ERROR] receive_text: {e}")
                break

            print(f"[DEBUG] Получено сообщение длиной {len(raw)} символов")

            await process(raw)
            await asyncio.sleep(0.05)

    finally:
        print("[INFO] Соединение закрыто")


# REST API: Получение всех матчей
@app.get("/matches")
def get_matches(
    team: Optional[str] = Query(None, description="Фильтр по команде (home или away)"),
    sort_by: Optional[Literal["updated_at", "changed_at"]] = Query("updated_at", description="Поле для сортировки"),
    order: Optional[Literal["asc", "desc"]] = Query("desc", description="Порядок сортировки")
):
    matches = get_matches_state()
    filtered = []

    for match in matches.values():
        if team and team.lower() not in (match["home"].lower() + match["away"].lower()):
            continue

        latest_times = [
            odds.get("updated_at")
            for outcome in match.get("outcomes", {}).values()
            for bookmaker, odds in outcome.get("bookmakers", {}).items()
            if "updated_at" in odds
        ]
        latest_updated_at = max(latest_times) if latest_times else 0

        changed_times = [
            odds.get("changed_at")
            for outcome in match.get("outcomes", {}).values()
            for bookmaker, odds in outcome.get("bookmakers", {}).items()
            if "changed_at" in odds
        ]
        latest_changed_at = max(changed_times) if changed_times else 0

        match_summary = {
            "match_id": match["match_id"],
            "teams": f"{match['home']} vs {match['away']}",
            "score": match["score"],
            "outcomes_count": len(match.get("outcomes", {})),
            "updated_at": latest_updated_at,
            "changed_at": latest_changed_at,
        }
        filtered.append(match_summary)

    reverse = order == "desc"
    filtered.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

    return {"matches": filtered}


# REST API: Получение данных по конкретному матчу
@app.get("/matches/{match_id}")
def get_match(match_id: str):
    all_matches = get_matches_state()
    match = all_matches.get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Матч не найден")

    structured_outcomes = {}
    for outcome_type, outcome in match.get("outcomes", {}).items():
        structured_outcomes[outcome_type] = []
        for bookmaker, odds in outcome.get("bookmakers", {}).items():
            structured_outcomes[outcome_type].append({
                "bookmaker": bookmaker,
                "value": odds.get("value"),
                "roi": odds.get("roi"),
                "margin": odds.get("margin"),
                "updated_at": odds.get("updated_at"),
                "changed_at": odds.get("changed_at"),
            })

    response = {
        "match_id": match["match_id"],
        "teams": {
            "home": match["home"],
            "away": match["away"]
        },
        "score": match["score"],
        "updated_at": match.get("updated_at"),
        "changed_at": match.get("changed_at"),
        "outcomes": structured_outcomes
    }

    return response
