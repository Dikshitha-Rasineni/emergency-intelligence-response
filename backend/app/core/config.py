from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "RESQ.AI Emergency Intelligence & Response"
    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/resq_ai"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ---- Authentication -------------------------------------------------
    JWT_SECRET: str = "change-me-in-production-this-is-a-dev-only-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    # Shared secret ESP32 devices send as "Authorization: Bearer <token>".
    # Empty = device auth disabled (development only; logged as a warning).
    IOT_DEVICE_TOKEN: str = ""

    # ---- Text LLM -------------------------------------------------------
    # LLM_PROVIDER: ollama | gemini | openai | none
    LLM_PROVIDER: str = "ollama"
    LLM_TIMEOUT_SECONDS: float = 20.0
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_KEEP_ALIVE: str = "30m"
    OLLAMA_NUM_CTX: int = 4096           # Ollama's default can be 2048, which silently cuts long prompts
    GENAI_FAST_MODEL: str = ""          # optional smaller model for briefs/Ask RESQ, e.g. "qwen3:1.7b"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    # Any OpenAI-compatible server: Groq, OpenRouter, llama.cpp server, vLLM, LM Studio
    OPENAI_BASE_URL: str = "https://api.groq.com/openai/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "llama-3.1-8b-instant"

    # ---- Vision ---------------------------------------------------------
    # VISION_PROVIDER: ollama | gemini | openai | none
    VISION_PROVIDER: str = "ollama"
    OLLAMA_VISION_MODEL: str = "qwen2.5vl:3b"
    GEMINI_VISION_MODEL: str = "gemini-2.5-flash"
    OPENAI_VISION_MODEL: str = ""
    VISION_TIMEOUT_SECONDS: float = 60.0

    # ---- Speech-to-text (server side; browser speech is the first option) -
    # STT_PROVIDER: gemini | openai | none   (openai = Whisper-compatible /audio/transcriptions)
    STT_PROVIDER: str = "none"
    OPENAI_STT_MODEL: str = "whisper-large-v3"

    # ---- Uploads --------------------------------------------------------
    UPLOAD_DIR: str = os.path.join(BACKEND_DIR, "uploads")
    MAX_IMAGE_MB: float = 8.0
    MAX_IMAGES_PER_INCIDENT: int = 6
    MAX_AUDIO_MB: float = 10.0
    IMAGE_MAX_DIMENSION: int = 1600
    MEDIA_RETENTION_DAYS: int = 30

    # ---- Routing / geo --------------------------------------------------
    DEFAULT_ROUTING_SPEED_KMH: float = 40.0  # used only for clearly-labelled approximations
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    ENABLE_OSM_LIVE_LOOKUP: bool = True
    IOT_MERGE_RADIUS_M: float = 300.0
    IOT_MERGE_WINDOW_MIN: int = 20

    # ---- Translation (citizen language <-> English) ----------------------
    # auto = MyMemory (free, no key) first, then the configured LLM; mymemory | llm | none
    TRANSLATION_PROVIDER: str = "auto"
    MYMEMORY_URL: str = "https://api.mymemory.translated.net/get"
    TRANSLATION_TIMEOUT_SECONDS: float = 8.0

    # ---- Unit dispatch ---------------------------------------------------
    AUTO_DISPATCH: bool = True            # sensor alerts / HIGH+CRITICAL incidents get the nearest unit automatically
    AUTO_DISPATCH_MAX_KM: float = 30.0
    DEMO_SIMULATE_UNITS: bool = True      # move demo units along their route when no crew GPS is shared
    DEMO_SIM_SPEED: float = 6.0           # simulated movement runs this many times faster (clearly labelled)

    # ---- Severity thresholds -------------------------------------------
    PRIORITY_CRITICAL_THRESHOLD: int = 75
    PRIORITY_HIGH_THRESHOLD: int = 50
    PRIORITY_MODERATE_THRESHOLD: int = 25

    # ---- Notifications --------------------------------------------------
    ACK_DEADLINE_CRITICAL_MIN: int = 2
    ACK_DEADLINE_DEFAULT_MIN: int = 5

    # ---- Rate limiting (per client IP, per minute) ----------------------
    RATE_LIMIT_REPORTS_PER_MIN: int = 10
    RATE_LIMIT_UPLOADS_PER_MIN: int = 30

    # ---- Amazon Location Service (optional) -----------------------------
    AWS_REGION: str = "us-east-1"
    AWS_LOCATION_MAP_NAME: str = ""
    AWS_LOCATION_ROUTE_CALCULATOR: str = ""

    # ---- Frontend -------------------------------------------------------
    FRONTEND_DIST: str = os.path.join(os.path.dirname(BACKEND_DIR), "frontend", "dist")


settings = Settings()
