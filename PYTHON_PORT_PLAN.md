# Python Port Plan: LM Studio LAN Gateway

## Overview

This document provides a comprehensive plan for porting the LM Studio LAN Gateway from TypeScript/Node.js to Python, maintaining all features and architecture while leveraging Python's ecosystem.

**Source**: TypeScript/Node.js (this repository)
**Target**: Python 3.11+ with FastAPI
**Goal**: Complete feature parity with production-ready implementation

---

## Phase 1: Project Foundation & Structure

**Goal**: Set up Python project with proper structure and dependencies

### 1.1 Create Project Structure

```
lmstudio-lan-api-python/
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py             # Pydantic settings (replaces Zod + dotenv)
│   │   └── logger.py               # Python logging config
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── ip_allowlist.py         # IP/CIDR middleware
│   │   └── api_key.py              # API key auth
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic models (replaces Zod schemas)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py                # Admin endpoints
│   │   ├── debug.py                # Debug/monitoring
│   │   └── proxy.py                # /v1/* proxy
│   ├── services/
│   │   ├── __init__.py
│   │   └── lm_studio_client.py     # SDK client wrapper
│   └── utils/
│       ├── __init__.py
│       └── event_broadcaster.py    # SSE events
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_middleware.py
│   │   ├── test_schemas.py
│   │   └── test_utils.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_admin.py
│   │   ├── test_debug.py
│   │   └── test_proxy.py
│   └── fixtures/
│       ├── __init__.py
│       └── mock_data.py
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml                  # Poetry/setuptools config
├── pytest.ini                      # Pytest configuration
├── README.md
├── PYTHON_MIGRATION.md
└── Dockerfile
```

### 1.2 Define Dependencies

**requirements.txt** (Production):
```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0

# HTTP Client
httpx==0.26.0

# Validation & Settings
pydantic==2.5.3
pydantic-settings==2.1.0

# LM Studio SDK
# lmstudio-sdk==1.5.0  # Use if Python SDK exists
websockets==12.0       # For WebSocket communication

# Security & Utilities
python-multipart==0.0.6
python-dotenv==1.0.0
```

**requirements-dev.txt** (Development):
```txt
# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# Code Quality
black==23.12.1
ruff==0.1.11
mypy==1.8.0

# Type Stubs
types-aiofiles==23.2.0.0
```

### 1.3 Technology Mapping

| TypeScript/Node.js | Python | Purpose |
|-------------------|---------|---------|
| Express.js | **FastAPI** | Web framework (async, OpenAPI docs) |
| TypeScript | **Python 3.11+** | Language with type hints |
| Zod | **Pydantic** | Validation + serialization |
| Winston | **logging** module | Structured logging |
| axios | **httpx** | Async HTTP client |
| node-windows | **nssm/systemd** | Windows/Linux services |
| Jest | **pytest** | Testing framework |
| tsx | **uvicorn** | Development server |
| npm | **pip/poetry** | Package manager |

---

## Phase 2: Core Configuration & Settings

**Goal**: Environment configuration and logging setup

### 2.1 Create Pydantic Settings

**File**: `src/config/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import cached_property


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Equivalent to TypeScript settings.ts with Zod validation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # LM Studio Connection
    lmstudio_base_url: str = "http://127.0.0.1:1234"

    # Gateway Server
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8002

    # Security
    gateway_api_key: str = ""
    ip_allowlist: str = "*"
    require_auth_for_health: bool = False

    # Logging
    log_level: str = "INFO"

    # Environment
    node_env: str = "development"

    @cached_property
    def ip_allowlist_items(self) -> List[str]:
        """Parse IP allowlist into list of items."""
        return [
            ip.strip()
            for ip in self.ip_allowlist.split(",")
            if ip.strip()
        ]

    @cached_property
    def api_key_enabled(self) -> bool:
        """Check if API key authentication is enabled."""
        return len(self.gateway_api_key) > 0

    @cached_property
    def websocket_url(self) -> str:
        """Convert HTTP URL to WebSocket URL."""
        return (
            self.lmstudio_base_url
            .replace("http://", "ws://")
            .replace("https://", "wss://")
        )


# Global settings instance (singleton)
settings = Settings()
```

### 2.2 Configure Logging

**File**: `src/config/logger.py`

```python
import logging
import sys
from typing import Optional
from .settings import settings


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Configure and return logger instance.

    Equivalent to Winston logger in TypeScript version.
    """
    logger = logging.getLogger(name or "lmstudio_gateway")

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Console handler with colors
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logger()
```

---

## Phase 3: Pydantic Models & Schemas

**Goal**: Define all request/response models with validation

### 3.1 Create Schema Models

**File**: `src/models/schemas.py`

```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


# ===== Load Configuration Schemas =====

class GPUConfig(BaseModel):
    """GPU offload configuration."""
    ratio: Optional[float] = Field(None, ge=0, le=1, description="GPU offload ratio (0-1)")
    layers: Optional[int] = Field(None, ge=0, description="Number of layers to offload")


class LoadConfig(BaseModel):
    """Model loading configuration."""

    model_config = ConfigDict(populate_by_name=True)

    context_length: Optional[int] = Field(
        None,
        gt=0,
        alias="contextLength",
        description="Context window size"
    )
    gpu: Optional[GPUConfig] = None
    cpu_threads: Optional[int] = Field(
        None,
        gt=0,
        alias="cpuThreads",
        description="Number of CPU threads"
    )
    rope_frequency_base: Optional[float] = Field(
        None,
        gt=0,
        alias="ropeFrequencyBase"
    )
    rope_frequency_scale: Optional[float] = Field(
        None,
        gt=0,
        alias="ropeFrequencyScale"
    )


# ===== Inference Parameter Schemas =====

class DefaultInference(BaseModel):
    """Default inference parameters."""

    model_config = ConfigDict(populate_by_name=True)

    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0, alias="maxTokens")
    top_p: Optional[float] = Field(None, ge=0, le=1, alias="topP")
    top_k: Optional[int] = Field(None, ge=0, alias="topK")
    repeat_penalty: Optional[float] = Field(None, ge=0, alias="repeatPenalty")
    stop_strings: Optional[List[str]] = Field(None, alias="stopStrings")
    stream: Optional[bool] = None


# ===== Admin API Request/Response Schemas =====

class LoadModelRequest(BaseModel):
    """Request to load a model."""

    model_config = ConfigDict(populate_by_name=True)

    model_key: str = Field(..., min_length=1, alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")
    load_config: Optional[LoadConfig] = Field(None, alias="loadConfig")
    ttl_seconds: Optional[int] = Field(None, ge=0, alias="ttlSeconds")
    default_inference: Optional[DefaultInference] = Field(None, alias="defaultInference")
    activate: bool = True


class LoadModelResponse(BaseModel):
    """Response from model load."""
    status: Literal["loaded"]
    model_key: str = Field(..., alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")
    activated: bool
    total_time_ms: int = Field(..., alias="totalTimeMs")
    message: str


class UnloadModelRequest(BaseModel):
    """Request to unload a model."""

    model_config = ConfigDict(populate_by_name=True)

    model_key: str = Field(..., min_length=1, alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")


class UnloadModelResponse(BaseModel):
    """Response from model unload."""
    status: Literal["unloaded"]
    model_key: str = Field(..., alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")
    total_time_ms: int = Field(..., alias="totalTimeMs")
    message: str


class ActivateModelRequest(BaseModel):
    """Request to activate a model."""

    model_config = ConfigDict(populate_by_name=True)

    model_key: str = Field(..., min_length=1, alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")
    default_inference: Optional[DefaultInference] = Field(None, alias="defaultInference")


class ActivateModelResponse(BaseModel):
    """Response from model activation."""
    status: Literal["activated"]
    model_key: str = Field(..., alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")
    default_inference: Dict[str, Any] = Field(..., alias="defaultInference")
    message: str


# ===== Application State Models =====

class ActiveModel(BaseModel):
    """Currently active model state."""

    model_config = ConfigDict(populate_by_name=True)

    model_key: Optional[str] = Field(None, alias="modelKey")
    instance_id: Optional[str] = Field(None, alias="instanceId")
    default_inference: Dict[str, Any] = Field(default_factory=dict, alias="defaultInference")


class OperationInfo(BaseModel):
    """Information about current operation."""
    type: Optional[Literal["model_load", "model_unload", "inference"]] = None
    model_key: Optional[str] = Field(None, alias="modelKey")
    progress: Optional[float] = None
    started_at: Optional[str] = Field(None, alias="startedAt")
    elapsed_ms: Optional[int] = Field(None, alias="elapsedMs")


class RequestInfo(BaseModel):
    """Information about a request."""

    model_config = ConfigDict(populate_by_name=True)

    request_id: str = Field(..., alias="requestId")
    status: Literal["pending", "completed", "failed"]
    tokens_generated: Optional[int] = Field(None, alias="tokensGenerated")
    time_ms: Optional[int] = Field(None, alias="timeMs")
    timestamp: str


class DebugState(BaseModel):
    """Debug state tracking."""
    status: Literal["idle", "loading_model", "processing_inference", "error"]
    current_operation: Optional[OperationInfo] = Field(None, alias="currentOperation")
    recent_requests: List[RequestInfo] = Field(default_factory=list, alias="recentRequests")
    total_requests: int = Field(0, alias="totalRequests")
    total_errors: int = Field(0, alias="totalErrors")


class AppState(BaseModel):
    """Complete application state."""

    model_config = ConfigDict(populate_by_name=True)

    active_model: ActiveModel = Field(default_factory=ActiveModel, alias="activeModel")
    debug_state: DebugState = Field(default_factory=lambda: DebugState(status="idle"), alias="debugState")


# ===== Debug Event Types =====

class DebugEvent(BaseModel):
    """Debug event structure."""
    type: str
    data: Dict[str, Any]
```

---

## Phase 4: Middleware Implementation

**Goal**: Security and request filtering

### 4.1 API Key Middleware

**File**: `src/middleware/api_key.py`

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..config.settings import settings
from ..config.logger import logger


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API key authentication middleware.

    Equivalent to TypeScript apiKey.ts middleware.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip if API key not enabled
        if not settings.api_key_enabled:
            return await call_next(request)

        # Skip /health if configured
        if request.url.path == "/health" and not settings.require_auth_for_health:
            return await call_next(request)

        # Validate API key
        api_key = request.headers.get("X-API-Key")

        if not api_key or api_key != settings.gateway_api_key:
            client_host = request.client.host if request.client else "unknown"
            logger.warning(
                f"Unauthorized request from {client_host}",
                extra={
                    "ip": client_host,
                    "path": request.url.path,
                    "has_key": bool(api_key)
                }
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Unauthorized"}
            )

        return await call_next(request)
```

### 4.2 IP Allowlist Middleware

**File**: `src/middleware/ip_allowlist.py`

```python
from ipaddress import ip_address, ip_network, AddressValueError
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..config.settings import settings
from ..config.logger import logger


class IPAllowlistMiddleware(BaseHTTPMiddleware):
    """
    IP allowlist middleware with CIDR support.

    Equivalent to TypeScript ipAllowlist.ts middleware.
    """

    async def dispatch(self, request: Request, call_next):
        # Allow all if wildcard
        if "*" in settings.ip_allowlist_items:
            return await call_next(request)

        if not request.client:
            return await call_next(request)

        try:
            client_ip = ip_address(request.client.host)
        except (ValueError, AddressValueError):
            logger.warning(f"Invalid client IP: {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Forbidden"}
            )

        # Check if IP in allowlist
        allowed = False
        for allowed_item in settings.ip_allowlist_items:
            try:
                # Try as network (CIDR)
                if client_ip in ip_network(allowed_item, strict=False):
                    allowed = True
                    break
            except (ValueError, AddressValueError):
                # Try as single IP
                try:
                    if client_ip == ip_address(allowed_item):
                        allowed = True
                        break
                except (ValueError, AddressValueError):
                    logger.warning(f"Invalid allowlist entry: {allowed_item}")

        if not allowed:
            logger.warning(
                f"Forbidden IP: {client_ip}",
                extra={"ip": str(client_ip), "path": request.url.path}
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Forbidden"}
            )

        return await call_next(request)
```

---

## Phase 5: LM Studio SDK Client Service

**Goal**: WebSocket-based SDK integration with singleton pattern

### 5.1 Create Client Service

**File**: `src/services/lm_studio_client.py`

```python
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..config.settings import settings
from ..config.logger import logger

# Import LM Studio SDK when available
try:
    from lmstudio import LMStudioClient as SDKClient
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    # Fallback: use websockets directly
    import websockets
    import json


class LMStudioClientService:
    """
    Singleton service for LM Studio SDK client.

    Equivalent to TypeScript lmStudioClient.ts service.
    Provides connection management, retry logic, and model operations.
    """

    _instance: Optional['LMStudioClientService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.client: Optional[Any] = None
        self._connecting: Optional[asyncio.Task] = None
        self.max_retries = 3
        self.retry_delay_ms = 2000
        self._initialized = True

    async def get_client(self) -> Any:
        """
        Get or create LMStudioClient connection.

        Returns:
            Connected LMStudioClient instance

        Raises:
            ConnectionError: If connection fails after retries
        """
        # Return existing client if connected
        if self.client is not None:
            return self.client

        # Wait for existing connection attempt
        if self._connecting is not None:
            await self._connecting
            return self.client

        # Start new connection
        self._connecting = asyncio.create_task(self._connect())
        await self._connecting
        self._connecting = None

        return self.client

    async def _connect(self) -> Any:
        """Connect to LM Studio with retry logic."""
        ws_url = settings.websocket_url

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Connecting to LM Studio SDK",
                    extra={
                        "url": ws_url,
                        "attempt": attempt,
                        "max_retries": self.max_retries
                    }
                )

                if HAS_SDK:
                    # Use official SDK
                    client = SDKClient(base_url=ws_url)
                    # Test connection
                    await client.system.list_downloaded_models()
                else:
                    # Fallback: create custom WebSocket client
                    client = await self._create_websocket_client(ws_url)

                logger.info(
                    "Successfully connected to LM Studio SDK",
                    extra={"url": ws_url, "attempt": attempt}
                )

                self.client = client
                return client

            except Exception as error:
                logger.warning(
                    f"Failed to connect to LM Studio SDK",
                    extra={
                        "url": ws_url,
                        "attempt": attempt,
                        "max_retries": self.max_retries,
                        "error": str(error)
                    }
                )

                if attempt < self.max_retries:
                    delay_sec = self.retry_delay_ms / 1000
                    logger.info(f"Retrying in {delay_sec}s...")
                    await asyncio.sleep(delay_sec)
                else:
                    error_msg = (
                        f"Failed to connect to LM Studio SDK after {self.max_retries} attempts. "
                        "Ensure LM Studio is running and the API server is enabled."
                    )
                    logger.error(error_msg, extra={"url": ws_url})
                    raise ConnectionError(error_msg) from error

        raise ConnectionError("Connection failed")

    async def _create_websocket_client(self, ws_url: str):
        """Create custom WebSocket client if SDK not available."""
        # Placeholder for custom WebSocket implementation
        # This would implement the LM Studio protocol manually
        raise NotImplementedError(
            "LM Studio Python SDK not found. "
            "Install with: pip install lmstudio-sdk"
        )

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.client is not None

    async def health_check(self) -> bool:
        """
        Verify connection is alive.

        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            if self.client is None:
                return False

            # Test connection
            if HAS_SDK:
                await self.client.system.list_downloaded_models()
            else:
                # Custom health check
                pass

            return True

        except Exception as error:
            logger.warning(
                "LM Studio SDK health check failed",
                extra={"error": str(error)}
            )

            # Invalidate client on failure
            self.client = None
            self._connecting = None

            return False

    async def disconnect(self):
        """Disconnect from LM Studio."""
        if self.client is not None:
            logger.info("Disconnecting from LM Studio SDK")
            # SDK cleanup if needed
            self.client = None
            self._connecting = None


# Singleton instance getter
def get_lm_studio_client() -> LMStudioClientService:
    """Get singleton LMStudioClientService instance."""
    return LMStudioClientService()
```

---

## Phase 6: Route Handlers

**Goal**: Implement all API endpoints

### 6.1 Admin Routes

**File**: `src/routes/admin.py`

```python
from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any
import time
from ..models.schemas import (
    LoadModelRequest, LoadModelResponse,
    UnloadModelRequest, UnloadModelResponse,
    ActivateModelRequest, ActivateModelResponse
)
from ..services.lm_studio_client import get_lm_studio_client
from ..utils.event_broadcaster import broadcast_debug_event
from ..config.logger import logger


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/models")
async def list_models(request: Request) -> Dict[str, Any]:
    """
    List available models (loaded and downloaded).

    Equivalent to TypeScript GET /admin/models endpoint.
    """
    try:
        logger.info("Fetching model list from LM Studio SDK")

        client_service = get_lm_studio_client()
        client = await client_service.get_client()

        # Get both loaded and downloaded models
        loaded_models = await client.llm.list_loaded()
        downloaded_models = await client.system.list_downloaded_models()

        return {
            "loaded": [
                {"path": model.path, "identifier": model.identifier}
                for model in loaded_models
            ],
            "downloaded": [
                {
                    "path": model.path,
                    "size": model.size_bytes,
                    "type": model.type
                }
                for model in downloaded_models
            ]
        }

    except Exception as error:
        logger.error(f"Error fetching models via SDK: {error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )


@router.post("/models/load", response_model=LoadModelResponse)
async def load_model(
    payload: LoadModelRequest,
    request: Request
) -> LoadModelResponse:
    """
    Load a model with configuration.

    Equivalent to TypeScript POST /admin/models/load endpoint.
    """
    app_state = request.app.state.app_state
    start_time = time.time()

    try:
        logger.info(
            f"Loading model",
            extra={
                "model_key": payload.model_key,
                "instance_id": payload.instance_id
            }
        )

        # Update debug state
        app_state.debug_state.status = "loading_model"
        app_state.debug_state.current_operation = {
            "type": "model_load",
            "modelKey": payload.model_key,
            "progress": 0,
            "startedAt": datetime.utcnow().isoformat() + "Z"
        }

        # Broadcast event
        await broadcast_debug_event("model_load_start", {
            "modelKey": payload.model_key,
            "instanceId": payload.instance_id,
            "loadConfig": payload.load_config.model_dump(by_alias=True) if payload.load_config else {}
        })

        # Load model via SDK
        client_service = get_lm_studio_client()
        client = await client_service.get_client()

        # Build load config
        load_config = {}
        if payload.load_config:
            config_dict = payload.load_config.model_dump(exclude_none=True, by_alias=True)
            load_config = config_dict

        # Load the model
        await client.llm.load(
            payload.model_key,
            identifier=payload.instance_id,
            config=load_config
        )

        logger.info(
            f"Model loaded successfully via SDK",
            extra={
                "model_key": payload.model_key,
                "instance_id": payload.instance_id
            }
        )

        # Activate if requested
        if payload.activate:
            app_state.active_model.model_key = payload.model_key
            app_state.active_model.instance_id = payload.instance_id
            app_state.active_model.default_inference = (
                payload.default_inference.model_dump(exclude_none=True, by_alias=True)
                if payload.default_inference else {}
            )
            logger.info(f"Model activated as default: {payload.model_key}")

        # Update debug state
        app_state.debug_state.status = "idle"
        app_state.debug_state.current_operation = None

        total_time_ms = int((time.time() - start_time) * 1000)

        # Broadcast completion
        await broadcast_debug_event("model_load_complete", {
            "modelKey": payload.model_key,
            "instanceId": payload.instance_id,
            "activated": payload.activate,
            "totalTimeMs": total_time_ms,
            "loadConfig": load_config
        })

        return LoadModelResponse(
            status="loaded",
            modelKey=payload.model_key,
            instanceId=payload.instance_id,
            activated=payload.activate,
            totalTimeMs=total_time_ms,
            message="Model loaded successfully via LM Studio SDK"
        )

    except Exception as error:
        app_state.debug_state.status = "error"
        app_state.debug_state.total_errors += 1

        total_time_ms = int((time.time() - start_time) * 1000)

        logger.error(
            f"Failed to load model via SDK",
            extra={"model_key": payload.model_key, "error": str(error)}
        )

        await broadcast_debug_event("error", {
            "operation": "model_load",
            "modelKey": payload.model_key,
            "error": str(error),
            "totalTimeMs": total_time_ms
        })

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


@router.post("/models/unload", response_model=UnloadModelResponse)
async def unload_model(
    payload: UnloadModelRequest,
    request: Request
) -> UnloadModelResponse:
    """
    Unload a model from memory.

    Equivalent to TypeScript POST /admin/models/unload endpoint.
    """
    app_state = request.app.state.app_state
    start_time = time.time()

    try:
        logger.info(
            f"Unloading model",
            extra={
                "model_key": payload.model_key,
                "instance_id": payload.instance_id
            }
        )

        # Update debug state
        app_state.debug_state.status = "loading_model"
        app_state.debug_state.current_operation = {
            "type": "model_unload",
            "modelKey": payload.model_key,
            "progress": 0,
            "startedAt": datetime.utcnow().isoformat() + "Z"
        }

        # Broadcast event
        await broadcast_debug_event("model_unload_start", {
            "modelKey": payload.model_key,
            "instanceId": payload.instance_id
        })

        # Unload via SDK
        client_service = get_lm_studio_client()
        client = await client_service.get_client()

        # Find model to unload
        loaded_models = await client.llm.list_loaded()

        model_to_unload = None
        for model in loaded_models:
            if payload.instance_id:
                if model.identifier == payload.instance_id:
                    model_to_unload = model
                    break
            else:
                if model.path == payload.model_key:
                    model_to_unload = model
                    break

        if not model_to_unload:
            not_found_msg = f"Model not found: {payload.model_key}"
            if payload.instance_id:
                not_found_msg += f" (instance: {payload.instance_id})"

            logger.warning(not_found_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=not_found_msg
            )

        # Unload the model
        await model_to_unload.unload()

        logger.info(
            f"Model unloaded successfully via SDK",
            extra={
                "model_key": payload.model_key,
                "instance_id": payload.instance_id
            }
        )

        # Clear active model if it's the one being unloaded
        if (app_state.active_model.model_key == payload.model_key and
            (not payload.instance_id or
             app_state.active_model.instance_id == payload.instance_id)):
            app_state.active_model.model_key = None
            app_state.active_model.instance_id = None
            app_state.active_model.default_inference = {}
            logger.info("Active model cleared")

        # Update debug state
        app_state.debug_state.status = "idle"
        app_state.debug_state.current_operation = None

        total_time_ms = int((time.time() - start_time) * 1000)

        # Broadcast completion
        await broadcast_debug_event("model_unload_complete", {
            "modelKey": payload.model_key,
            "instanceId": payload.instance_id,
            "totalTimeMs": total_time_ms
        })

        return UnloadModelResponse(
            status="unloaded",
            modelKey=payload.model_key,
            instanceId=payload.instance_id,
            totalTimeMs=total_time_ms,
            message="Model unloaded successfully via LM Studio SDK"
        )

    except HTTPException:
        raise
    except Exception as error:
        app_state.debug_state.status = "error"
        app_state.debug_state.total_errors += 1

        total_time_ms = int((time.time() - start_time) * 1000)

        logger.error(
            f"Failed to unload model via SDK",
            extra={"model_key": payload.model_key, "error": str(error)}
        )

        await broadcast_debug_event("error", {
            "operation": "model_unload",
            "modelKey": payload.model_key,
            "error": str(error),
            "totalTimeMs": total_time_ms
        })

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


@router.post("/models/activate", response_model=ActivateModelResponse)
async def activate_model(
    payload: ActivateModelRequest,
    request: Request
) -> ActivateModelResponse:
    """
    Activate a model as default (without loading).

    Equivalent to TypeScript POST /admin/models/activate endpoint.
    """
    app_state = request.app.state.app_state

    try:
        logger.info(
            f"Activating model",
            extra={
                "model_key": payload.model_key,
                "instance_id": payload.instance_id
            }
        )

        # Broadcast event
        await broadcast_debug_event("model_activate", {
            "modelKey": payload.model_key,
            "instanceId": payload.instance_id,
            "defaultInference": (
                payload.default_inference.model_dump(exclude_none=True, by_alias=True)
                if payload.default_inference else {}
            )
        })

        # Update active model
        app_state.active_model.model_key = payload.model_key
        app_state.active_model.instance_id = payload.instance_id
        app_state.active_model.default_inference = (
            payload.default_inference.model_dump(exclude_none=True, by_alias=True)
            if payload.default_inference else {}
        )

        return ActivateModelResponse(
            status="activated",
            modelKey=payload.model_key,
            instanceId=payload.instance_id,
            defaultInference=app_state.active_model.default_inference,
            message="Model activated successfully"
        )

    except Exception as error:
        app_state.debug_state.total_errors += 1

        await broadcast_debug_event("error", {
            "operation": "model_activate",
            "error": str(error)
        })

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )
```

### 6.2 Proxy Routes

**File**: `src/routes/proxy.py`

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
from typing import Any
from ..config.settings import settings
from ..config.logger import logger


router = APIRouter()


@router.api_route(
    "/v1/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_v1(path: str, request: Request):
    """
    Proxy all /v1/* requests to LM Studio HTTP API.

    Equivalent to TypeScript proxy.ts route handler.
    Auto-injects model and inference parameters.
    """
    app_state = request.app.state.app_state

    try:
        # Get request body
        request_body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None

        # Auto-inject model if missing
        if request_body and "model" not in request_body:
            if app_state.active_model.model_key:
                request_body["model"] = app_state.active_model.model_key
                logger.info(f"Auto-injected model: {app_state.active_model.model_key}")

        # Auto-inject default inference params
        if request_body and app_state.active_model.default_inference:
            for key, value in app_state.active_model.default_inference.items():
                if key not in request_body:
                    request_body[key] = value

        # Build target URL
        target_url = f"{settings.lmstudio_base_url}/v1/{path}"

        # Prepare headers
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("x-api-key", None)  # Don't forward our API key

        # Make request
        async with httpx.AsyncClient() as client:
            # Check if streaming
            is_streaming = request_body.get("stream", False) if request_body else False

            if is_streaming:
                # Stream response
                async def stream_generator():
                    async with client.stream(
                        request.method,
                        target_url,
                        json=request_body,
                        headers=headers,
                        timeout=60.0
                    ) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk

                return StreamingResponse(
                    stream_generator(),
                    media_type="text/event-stream"
                )
            else:
                # Regular request
                response = await client.request(
                    request.method,
                    target_url,
                    json=request_body,
                    headers=headers,
                    timeout=60.0
                )

                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )

    except Exception as error:
        logger.error(f"Proxy error: {error}")
        return JSONResponse(
            content={"error": str(error)},
            status_code=500
        )
```

### 6.3 Debug Routes

**File**: `src/routes/debug.py`

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import asyncio
import json
import time
from ..config.logger import logger
from ..utils.event_broadcaster import subscribe_to_events


router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/stream")
async def debug_stream(request: Request):
    """
    Server-Sent Events stream for real-time debugging.

    Equivalent to TypeScript GET /debug/stream endpoint.
    """
    logger.info(f"Client connected to debug stream: {request.client.host}")

    async def event_generator():
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'timestamp': time.time(), 'message': 'Debug stream connected'})}\n\n"

        # Subscribe to events
        async for event in subscribe_to_events():
            yield event

            # Keep-alive ping every 30 seconds
            await asyncio.sleep(30)
            yield ": keep-alive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/status")
async def debug_status(request: Request) -> Dict[str, Any]:
    """
    Get current debug status snapshot.

    Equivalent to TypeScript GET /debug/status endpoint.
    """
    app_state = request.app.state.app_state

    return {
        "status": app_state.debug_state.status,
        "currentOperation": app_state.debug_state.current_operation,
        "activeModel": {
            "modelKey": app_state.active_model.model_key,
            "instanceId": app_state.active_model.instance_id,
            "defaultInference": app_state.active_model.default_inference
        },
        "recentRequests": app_state.debug_state.recent_requests[-10:],
        "totalRequests": app_state.debug_state.total_requests,
        "totalErrors": app_state.debug_state.total_errors
    }


@router.get("/metrics")
async def debug_metrics(request: Request) -> Dict[str, Any]:
    """
    Get performance metrics.

    Equivalent to TypeScript GET /debug/metrics endpoint.
    """
    app_state = request.app.state.app_state

    # Calculate metrics
    completed_requests = [
        req for req in app_state.debug_state.recent_requests
        if req.status == "completed" and req.time_ms is not None
    ]

    avg_response_time = (
        sum(req.time_ms for req in completed_requests) / len(completed_requests)
        if completed_requests else 0
    )

    error_rate = (
        (app_state.debug_state.total_errors / app_state.debug_state.total_requests * 100)
        if app_state.debug_state.total_requests > 0 else 0
    )

    response_times = sorted([req.time_ms for req in completed_requests])
    min_response_time = response_times[0] if response_times else 0
    max_response_time = response_times[-1] if response_times else 0
    median_response_time = (
        response_times[len(response_times) // 2]
        if response_times else 0
    )

    return {
        "modelInfo": {
            "modelKey": app_state.active_model.model_key,
            "instanceId": app_state.active_model.instance_id,
            "defaultInference": app_state.active_model.default_inference
        },
        "performance": {
            "totalRequests": app_state.debug_state.total_requests,
            "totalErrors": app_state.debug_state.total_errors,
            "errorRate": round(error_rate, 2),
            "recentRequestCount": len(app_state.debug_state.recent_requests),
            "completedRequestCount": len(completed_requests),
            "avgResponseTimeMs": round(avg_response_time, 2),
            "minResponseTimeMs": min_response_time,
            "maxResponseTimeMs": max_response_time,
            "medianResponseTimeMs": median_response_time
        },
        "recentActivity": {
            "last10Requests": [
                {
                    "requestId": req.request_id,
                    "status": req.status,
                    "timeMs": req.time_ms,
                    "timestamp": req.timestamp
                }
                for req in app_state.debug_state.recent_requests[-10:]
            ]
        },
        "system": {
            "uptime": time.time() - request.app.state.start_time,
            "uptimeFormatted": format_uptime(time.time() - request.app.state.start_time),
            "platform": "python"
        },
        "currentOperation": app_state.debug_state.current_operation
    }


def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
```

---

## Phase 7: Event Broadcasting (SSE)

**Goal**: Real-time debug event streaming

**File**: `src/utils/event_broadcaster.py`

```python
import asyncio
import json
from typing import Dict, Any, Set
from datetime import datetime


class DebugEventBroadcaster:
    """
    Debug event broadcaster for SSE.

    Equivalent to TypeScript eventBroadcaster.ts utility.
    """

    def __init__(self):
        self.clients: Set[asyncio.Queue] = set()

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        event_data = {
            **data,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        event_str = f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

        # Send to all clients
        for client_queue in self.clients.copy():
            try:
                await client_queue.put(event_str)
            except Exception:
                # Remove disconnected clients
                self.clients.discard(client_queue)

    async def subscribe(self):
        """Subscribe to event stream."""
        queue = asyncio.Queue()
        self.clients.add(queue)

        try:
            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            self.clients.discard(queue)


# Global event broadcaster instance
_event_broadcaster = DebugEventBroadcaster()


async def broadcast_debug_event(event_type: str, data: Dict[str, Any]):
    """Broadcast debug event."""
    await _event_broadcaster.broadcast(event_type, data)


async def subscribe_to_events():
    """Subscribe to debug events."""
    async for event in _event_broadcaster.subscribe():
        yield event
```

---

## Phase 8: Main Application Setup

**Goal**: FastAPI app assembly with middleware

**File**: `src/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from .config.settings import settings
from .config.logger import logger
from .middleware.ip_allowlist import IPAllowlistMiddleware
from .middleware.api_key import APIKeyMiddleware
from .routes import admin, debug, proxy
from .models.schemas import AppState


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    app.state.start_time = time.time()
    app.state.app_state = AppState()

    logger.info(
        f"Server starting on {settings.gateway_host}:{settings.gateway_port}",
        extra={
            "host": settings.gateway_host,
            "port": settings.gateway_port,
            "environment": settings.node_env
        }
    )

    yield

    # Shutdown
    logger.info("Server shutting down")


app = FastAPI(
    title="LM Studio LAN Gateway (Python)",
    version="1.0.0",
    description="Python port of LM Studio LAN Gateway with SDK integration",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Custom middleware (order matters!)
app.add_middleware(IPAllowlistMiddleware)
app.add_middleware(APIKeyMiddleware)

# Include routers
app.include_router(admin.router)
app.include_router(debug.router)
app.include_router(proxy.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "uptime": time.time() - app.state.start_time
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=settings.node_env == "development",
        log_level=settings.log_level.lower()
    )
```

---

## Phase 9: Testing

**Goal**: Port Jest tests to pytest

### 9.1 Pytest Configuration

**File**: `pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

### 9.2 Example Test

**File**: `tests/integration/test_admin.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.mark.asyncio
async def test_load_model():
    """Test model loading endpoint."""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/admin/models/load",
            json={
                "modelKey": "test-model",
                "activate": True
            },
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "loaded"
        assert data["modelKey"] == "test-model"


@pytest.mark.asyncio
async def test_list_models():
    """Test model listing endpoint."""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/admin/models",
            headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "loaded" in data
        assert "downloaded" in data
```

---

## Phase 10: Documentation

**Goal**: Create Python-specific documentation

### 10.1 Files to Create/Update

1. **README.md** - Update with Python setup
2. **PYTHON_MIGRATION.md** - Document TypeScript → Python mapping
3. **API_GUIDE_PYTHON.md** - Python client examples
4. **requirements.txt** - Production dependencies
5. **requirements-dev.txt** - Development dependencies
6. **.env.example** - Same as TypeScript version
7. **.gitignore** - Python-specific ignores

---

## Phase 11: Deployment

### 11.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 11.2 docker-compose.yml

```yaml
version: '3.9'

services:
  lmstudio-gateway:
    build: .
    container_name: lmstudio-lan-gateway-python
    ports:
      - "${GATEWAY_PORT:-8002}:8002"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8002/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

### 11.3 Windows Service (NSSM)

**File**: `scripts/install-service.bat`

```batch
@echo off
nssm install LMStudioLANGatewayPython "C:\Python311\python.exe" "-m" "uvicorn" "src.main:app" "--host" "0.0.0.0" "--port" "8002"
nssm set LMStudioLANGatewayPython AppDirectory "C:\path\to\lmstudio-lan-api-python"
nssm set LMStudioLANGatewayPython DisplayName "LM Studio LAN Gateway (Python)"
nssm set LMStudioLANGatewayPython Description "LM Studio LAN API Gateway - Python Edition"
nssm set LMStudioLANGatewayPython Start SERVICE_AUTO_START
nssm start LMStudioLANGatewayPython
```

### 11.4 Linux Systemd

**File**: `scripts/lmstudio-gateway.service`

```ini
[Unit]
Description=LM Studio LAN Gateway (Python)
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/lmstudio-lan-api-python
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8002
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Key Differences: TypeScript vs Python

| Aspect | TypeScript/Node.js | Python |
|--------|-------------------|--------|
| **Web Framework** | Express.js | FastAPI |
| **Validation** | Zod | Pydantic |
| **Async** | Promises/async-await | asyncio/async-await |
| **HTTP Client** | axios | httpx |
| **Type System** | TypeScript compiler | Type hints + mypy |
| **Package Manager** | npm | pip/poetry |
| **Testing** | Jest + Supertest | pytest + httpx |
| **Logging** | Winston | logging module |
| **SSE** | Express Response | StreamingResponse |
| **Service (Windows)** | node-windows | NSSM |
| **Service (Linux)** | systemd | systemd |
| **Singleton Pattern** | Static private instance | `__new__` override |
| **Environment** | dotenv | pydantic-settings |

---

## Expected Challenges & Solutions

### 1. LM Studio Python SDK Availability

**Challenge**: Python SDK may not exist or differ from TypeScript SDK

**Solutions**:
- Check PyPI for official `lmstudio-sdk` package
- If unavailable, use `websockets` library to implement WebSocket protocol manually
- Create wrapper that mimics TypeScript SDK API for compatibility

### 2. Streaming Proxy Differences

**Challenge**: httpx streaming works differently than axios

**Solution**:
```python
# Use httpx.stream() context manager
async with client.stream("POST", url, json=data) as response:
    async for chunk in response.aiter_bytes():
        yield chunk
```

### 3. SSE Implementation

**Challenge**: FastAPI SSE requires async generators

**Solution**:
```python
async def event_generator():
    async for event in subscribe_to_events():
        yield event

return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 4. Type Safety

**Challenge**: Python less strict than TypeScript

**Solutions**:
- Use mypy with `--strict` mode
- Pydantic for runtime validation
- Type hints everywhere
- ConfigDict for Pydantic models

### 5. Middleware Order

**Challenge**: FastAPI middleware executes in reverse order of registration

**Solution**: Register in reverse order compared to Express.js

---

## Success Criteria

✅ All endpoints functional (admin, proxy, debug)
✅ Real model loading via SDK (or fallback)
✅ Auto-injection working (model + inference params)
✅ SSE debug stream operational
✅ All tests passing (80%+ coverage)
✅ Docker deployment working
✅ Windows/Linux service installation
✅ Documentation complete
✅ Performance comparable to TS version

---

## Estimated Timeline

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| **Phase 1-2** | Project setup, config | 2-3 hours |
| **Phase 3-4** | Models, middleware | 2 hours |
| **Phase 5** | SDK client (most complex) | 3-4 hours |
| **Phase 6-7** | Routes, SSE | 4-5 hours |
| **Phase 8** | Main app assembly | 1 hour |
| **Phase 9** | Testing | 3-4 hours |
| **Phase 10-11** | Docs, deployment | 2 hours |

**Total**: ~20-25 hours for complete port

---

## Recommendations

### 1. Start with Foundation (Phases 1-4)
Get basic structure running first:
- Project setup
- Configuration
- Pydantic models
- Middleware

### 2. Mock SDK Initially
Use dummy responses to test routes before SDK integration:
```python
class MockLMStudioClient:
    async def list_loaded(self):
        return []

    async def list_downloaded_models(self):
        return []
```

### 3. Copy-Paste Documentation
Most .md files can be adapted with find-replace:
- TypeScript → Python
- npm → pip
- Express → FastAPI
- Zod → Pydantic

### 4. Test Incrementally
Don't wait until end:
- Write tests alongside implementation
- Use pytest-watch for TDD workflow
- Test each endpoint as you build it

### 5. Use FastAPI Auto-Docs
Access `/docs` endpoint for interactive API testing during development

---

## Quick Start Commands

```bash
# Clone and setup
git clone <repo-url>
cd lmstudio-lan-api-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8002

# Run tests
pytest

# Build Docker image
docker build -t lmstudio-gateway-python .

# Run with Docker
docker-compose up -d
```

---

## Final Notes

This plan provides a complete roadmap for porting the LM Studio LAN Gateway to Python while maintaining 100% feature parity with the TypeScript version.

**Key Advantages of Python Port**:
- FastAPI provides automatic OpenAPI documentation
- Pydantic offers superior data validation
- Python's async/await is mature and well-supported
- Easier deployment with Docker/systemd
- Better scientific computing ecosystem (if needed later)

**Next Steps**:
1. Create repository structure
2. Set up virtual environment
3. Install dependencies
4. Start with Phase 1 (foundation)
5. Build incrementally, test frequently
6. Deploy and validate

Good luck with the implementation! 🚀
