import re
import httpx

DEFAULT_LOCATION = "Atlanta, GA"

WEATHER_KEYWORDS = [
    "weather", "temperature", "forecast", "degrees", "raining",
    "sunny", "cloudy", "humid", "how hot", "how cold", "wind",
]
SEARCH_KEYWORDS = [
    "search for", "look up", "find out", "who is", "who was",
    "when did", "when was", "how does", "latest", "news",
    "tell me about", "what happened", "current events",
    "what is", "give me", "recent",
]


def detect_and_fetch(message: str) -> str:
    lower = message.lower()

    if any(kw in lower for kw in WEATHER_KEYWORDS):
        location = _extract_location(message) or DEFAULT_LOCATION
        print(f"[tools] weather → {location}")
        return _get_weather(location)

    if any(kw in lower for kw in SEARCH_KEYWORDS):
        print(f"[tools] search → {message}")
        return _web_search(message)

    print("[tools] no tool triggered")
    return ""


def _extract_location(message: str) -> str | None:
    match = re.search(r'\bin\s+([A-Za-z][A-Za-z\s]+?)(?:\s*[\?\.,]|$)', message)
    if match:
        return match.group(1).strip()
    return None


def _get_weather(location: str) -> str:
    with httpx.Client(timeout=10) as client:
        geo = client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
        ).json()

        if not geo.get("results"):
            return f"Could not find location: {location}."

        r = geo["results"][0]
        lat, lon = r["latitude"], r["longitude"]
        name = f"{r.get('name', location)}, {r.get('country', '')}"

        weather = client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "forecast_days": 1,
                "timezone": "auto",
            },
        ).json()

        c = weather.get("current", {})
        d = weather.get("daily", {})
        condition = _weather_code(c.get("weather_code", 0))

        return (
            f"Current weather in {name}: {condition}, {c.get('temperature_2m')}°F. "
            f"Humidity {c.get('relative_humidity_2m')}%, wind {c.get('wind_speed_10m')} mph. "
            f"Today's high {d.get('temperature_2m_max', [None])[0]}°F, "
            f"low {d.get('temperature_2m_min', [None])[0]}°F."
        )


def _web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"- {r.get('title', '')}: {r.get('body', '')}")
        if results:
            print(f"[search] {len(results)} results for: {query}")
            return "\n".join(results)
        return "No results found."
    except Exception as e:
        print(f"[search] error: {e}")
        return ""


def _weather_code(code: int) -> str:
    if code == 0:
        return "Clear sky"
    if code in (1, 2, 3):
        return ["Mainly clear", "Partly cloudy", "Overcast"][code - 1]
    if code in (45, 48):
        return "Foggy"
    if code in (51, 53, 55):
        return "Drizzle"
    if code in (61, 63, 65):
        return "Rain"
    if code in (71, 73, 75):
        return "Snow"
    if code in (80, 81, 82):
        return "Rain showers"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return "Mixed conditions"
