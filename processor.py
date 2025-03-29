import json
import logging
import time
from typing import Dict, Any

# Настройка логирования
logger = logging.getLogger("processor")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/processor.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

live_data: Dict[str, dict] = {}

def extract_odds(odds_data: Any) -> float | None:
    """Извлекает числовое значение коэффициента (поддержка старого и нового формата)"""
    if isinstance(odds_data, dict):
        return odds_data.get("value")
    return odds_data

def calculate_true_odds(odds: float, margin: float = 0.08) -> float:
    """Возвращает истинный коэффициент"""
    return round(odds / (1 - margin), 4)

def calculate_median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return round((sorted_vals[mid - 1] + sorted_vals[mid]) / 2, 4)
    else:
        return round(sorted_vals[mid], 4)

def calculate_roi(raw_odds: float, median_true_odds: float) -> float:
    try:
        return round((raw_odds - median_true_odds) / median_true_odds * 100, 2)
    except ZeroDivisionError:
        return 0.0

async def process(raw: str):
    try:
        data = json.loads(raw)
        match_id = data.get("MatchId")
        source = data.get("Source")
        if not match_id or not source:
            logger.warning("Нет MatchId или Source в данных")
            return

        home = data.get("homeName", "")
        away = data.get("awayName", "")
        score = f"{data.get('HomeScore', 0)}:{data.get('AwayScore', 0)}"

        periods = data.get("Periods", [])
        if not periods or not periods[0].get("Totals"):
            logger.warning(f"[{match_id}] Нет данных по тоталам")
            return

        totals_raw = periods[0]["Totals"]
        timestamp = time.time()

        # Получаем или создаём данные по матчу
        match = live_data.setdefault(match_id, {
            "match_id": match_id,
            "home": home,
            "away": away,
            "score": score,
            "outcomes": {}
        })

        for total, values in totals_raw.items():
            win_more = extract_odds(values.get("WinMore"))
            win_less = extract_odds(values.get("WinLess"))
            if not win_more or not win_less:
                continue

            # Вычисление маржи
            try:
                margin = round((1 / win_more + 1 / win_less - 1) * 100, 2)
            except ZeroDivisionError:
                margin = None

            outcome = match["outcomes"].setdefault(total, {
                "bookmakers": {},
                "median_true_more": None,
                "median_true_less": None,
            })

            book_data = outcome["bookmakers"].get(source, {})
            changed_at = book_data.get("changed_at", timestamp)
            if (
                book_data.get("WinMore") != win_more
                or book_data.get("WinLess") != win_less
            ):
                changed_at = timestamp

            # Обновляем данные букмекера
            outcome["bookmakers"][source] = {
                "WinMore": win_more,
                "WinLess": win_less,
                "value": (win_more + win_less) / 2 if win_more and win_less else None,
                "margin": margin,
                "roi": None,
                "updated_at": timestamp,
                "changed_at": changed_at,
            }

        # Пересчёт медиан и ROI
        for total, outcome in match["outcomes"].items():
            true_more_list = [
                calculate_true_odds(bm["WinMore"])
                for bm in outcome["bookmakers"].values()
            ]
            true_less_list = [
                calculate_true_odds(bm["WinLess"])
                for bm in outcome["bookmakers"].values()
            ]
            median_more = calculate_median(true_more_list)
            median_less = calculate_median(true_less_list)

            outcome["median_true_more"] = median_more
            outcome["median_true_less"] = median_less

            for source, bm in outcome["bookmakers"].items():
                bm["ROI_More"] = calculate_roi(bm["WinMore"], median_more) if median_more else None
                bm["ROI_Less"] = calculate_roi(bm["WinLess"], median_less) if median_less else None
                bm["roi"] = round((bm["ROI_More"] + bm["ROI_Less"]) / 2, 2) if bm["ROI_More"] and bm["ROI_Less"] else None

        logger.info(f"[{match_id}] Обновлены данные по исходам ({source})")

    except Exception as e:
        logger.exception(f"Ошибка обработки сообщения: {e}")

def get_matches_state():
    return live_data
