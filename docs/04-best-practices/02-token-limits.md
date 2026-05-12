# Token-Limits & Rate-Limiting — Best Practices

## Warum Token-Limits unverzichtbar sind

```
OHNE TOKEN-LIMITS:
  Angreifer Input: 200.000 Zeichen  →  ~50.000 Token
  Kosten pro Request: $0.25
  Bei 1.000 Anfragen/h: $250/h = $6.000/Tag

  Außerdem:
  → API-Rate-Limit erschöpft → echte Nutzer ausgesperrt
  → Response-Zeit: 30+ Sekunden → praktisch offline
  → Context Poisoning möglich (System-Prompt verdrängt)

MIT TOKEN-LIMITS (max. 4.096 Token):
  Angreifer Input geblockt, normale Nutzung ungestört
  Max. Kosten: ~$0.02 pro Anfrage
```

## Empfohlene Limits nach Use-Case

```
┌──────────────────────┬─────────────┬────────────┬───────────┬──────────────┐
│ Use-Case             │ Input-Token │ Output-T.  │ Req/Min   │ Budget/Tag   │
├──────────────────────┼─────────────┼────────────┼───────────┼──────────────┤
│ Externer Chatbot     │    2.048    │   1.024    │    20     │    $50       │
│ Interner Chatbot     │    8.192    │   2.048    │    60     │   $200       │
│ E-Mail-Agent         │    4.096    │   1.024    │    100/h  │    $20       │
│ Dokument-Analyse     │   32.768    │   4.096    │    10     │   $100       │
│ Code-Assistent       │   16.384    │   8.192    │    30     │   $150       │
│ Batch-Verarbeitung   │   16.384    │   2.048    │    N/A    │   $500       │
└──────────────────────┴─────────────┴────────────┴───────────┴──────────────┘
```

## Implementierung

### FastAPI mit Token-Limit Middleware

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import tiktoken
import time
from collections import defaultdict

app = FastAPI()
encoder = tiktoken.encoding_for_model("gpt-4o")

# Konfiguration
MAX_INPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 1024
RATE_LIMIT_PER_MINUTE = 20

# In-Memory Rate-Limiter (Redis für Produktion!)
request_log: dict[str, list[float]] = defaultdict(list)

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Rate-Limiting per IP
    client_ip = request.client.host
    now = time.time()
    request_log[client_ip] = [t for t in request_log[client_ip] if now - t < 60]

    if len(request_log[client_ip]) >= RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"error": "Zu viele Anfragen. Bitte warte einen Moment."},
            headers={"Retry-After": "60"}
        )

    request_log[client_ip].append(now)
    return await call_next(request)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")

    # Token-Limit prüfen
    token_count = len(encoder.encode(message))
    if token_count > MAX_INPUT_TOKENS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Nachricht zu lang",
                "token_count": token_count,
                "max_tokens": MAX_INPUT_TOKENS,
            }
        )

    # LLM-Call mit Output-Limit
    # response = client.chat.completions.create(
    #     max_tokens=MAX_OUTPUT_TOKENS,
    #     ...
    # )
```

### Budget-Monitoring mit OpenAI

```python
import openai

class BudgetAwareClient:
    """OpenAI-Client mit eingebautem Budget-Tracking."""

    PRICE_PER_1K_TOKENS = {
        "gpt-4o":         {"input": 0.0025, "output": 0.010},
        "gpt-4o-mini":    {"input": 0.00015, "output": 0.0006},
        "claude-sonnet":  {"input": 0.003, "output": 0.015},
    }

    def __init__(self, api_key: str, daily_budget_usd: float = 50.0):
        self.client = openai.OpenAI(api_key=api_key)
        self.daily_budget = daily_budget_usd
        self.spent = 0.0

    def chat(self, messages: list, model: str = "gpt-4o-mini",
             max_tokens: int = 1024) -> str:
        # Pre-flight: Budget-Check
        if self.spent >= self.daily_budget:
            raise RuntimeError(f"Tages-Budget erschöpft: ${self.spent:.2f}")

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )

        # Kosten verbuchen
        usage = response.usage
        prices = self.PRICE_PER_1K_TOKENS.get(model, self.PRICE_PER_1K_TOKENS["gpt-4o"])
        cost = (usage.prompt_tokens / 1000 * prices["input"] +
                usage.completion_tokens / 1000 * prices["output"])
        self.spent += cost

        # Budget-Warnung
        if self.spent > self.daily_budget * 0.8:
            print(f"⚠️  Budget-Warnung: {self.spent/self.daily_budget:.0%} verbraucht")

        return response.choices[0].message.content
```

## Redis-basierter Rate-Limiter (Produktion)

```python
import redis
import time

class RedisRateLimiter:
    """
    Produktionsreifer Rate-Limiter mit Redis.
    Funktioniert auch bei mehreren Server-Instanzen (horizontal scaling).
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)

    def check(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        key = f"rate_limit:{identifier}:{int(time.time() // window_seconds)}"
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds * 2)
        count, _ = pipe.execute()
        return count <= max_requests
```

---

Zurück: [Best Practices](README.md) | Weiter: [Sichere System-Prompts →](03-sichere-system-prompts.md)
