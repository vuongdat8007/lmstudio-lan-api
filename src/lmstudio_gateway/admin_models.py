# src/lmstudio_gateway/admin_models.py
"""
Admin API router for model management.
Provides endpoints to load, unload, activate, and list models.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from .dependencies import get_active_model, get_http_client, lm_client

logger = logging.getLogger("lmstudio_gateway.admin")

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Pydantic Models
# ============================================================================


class LoadConfig(BaseModel):
    """Configuration for loading a model."""

    contextLength: Optional[int] = Field(
        default=None,
        description="Requested context length in tokens",
        ge=1,
    )
    gpu: Optional[Dict[str, Any]] = Field(
        default=None,
        description="GPU configuration (e.g., {'ratio': 1.0})",
    )

    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class DefaultInference(BaseModel):
    """Default inference parameters to inject into requests."""

    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)

    class Config:
        extra = "allow"  # Allow additional inference parameters


class LoadModelRequest(BaseModel):
    """Request to load a model."""

    model_key: str = Field(..., description="LM Studio model identifier")
    instance_id: Optional[str] = Field(
        default=None,
        description="Optional instance ID for multiple model instances",
    )
    load_config: Optional[LoadConfig] = Field(
        default=None,
        description="Model loading configuration",
    )
    ttl_seconds: Optional[int] = Field(
        default=None,
        description="Time-to-live for automatic unloading (seconds)",
        ge=0,
    )
    default_inference: Optional[DefaultInference] = Field(
        default=None,
        description="Default inference parameters for this model",
    )
    activate: bool = Field(
        default=True,
        description="Set this model as the active default",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_key": "qwen2.5-7b-instruct",
                "instance_id": "primary-qwen",
                "load_config": {"contextLength": 8192, "gpu": {"ratio": 1.0}},
                "ttl_seconds": 3600,
                "default_inference": {"temperature": 0.4, "max_tokens": 2048},
                "activate": True,
            }
        }


class LoadModelResponse(BaseModel):
    """Response from loading a model."""

    status: str = Field(..., description="Status of the operation")
    model_key: str
    instance_id: Optional[str] = None
    ttl_seconds: Optional[int] = None
    load_config: Dict[str, Any] = Field(default_factory=dict)
    default_inference: Dict[str, Any] = Field(default_factory=dict)
    activated: bool = Field(..., description="Whether model was set as active")


class UnloadModelRequest(BaseModel):
    """Request to unload a model."""

    model_key: Optional[str] = Field(
        default=None,
        description="Model key to unload (uses active model if not specified)",
    )
    instance_id: Optional[str] = Field(
        default=None,
        description="Instance ID to unload",
    )


class UnloadModelResponse(BaseModel):
    """Response from unloading a model."""

    status: str = Field(..., description="Status of the operation")
    model_key: Optional[str] = None
    instance_id: Optional[str] = None


class ActivateModelRequest(BaseModel):
    """Request to activate a model as default."""

    model_key: str = Field(..., description="Model key to activate")
    instance_id: Optional[str] = Field(
        default=None,
        description="Instance ID to activate",
    )
    default_inference: Optional[DefaultInference] = Field(
        default=None,
        description="Default inference parameters",
    )


class ActivateModelResponse(BaseModel):
    """Response from activating a model."""

    status: str = Field(..., description="Status of the operation")
    model_key: str
    instance_id: Optional[str] = None
    default_inference: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/models")
async def list_models(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> Dict[str, Any]:
    """
    List available models from LM Studio.

    Returns:
        Dictionary containing available models

    Raises:
        HTTPException: If LM Studio is unreachable or returns an error
    """
    try:
        resp = await http_client.get("/api/v0/models")
        resp.raise_for_status()
    except httpx.RequestError as e:
        logger.exception("Error connecting to LM Studio: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LM Studio API unreachable",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.exception("LM Studio returned error: %s", e)
        raise HTTPException(
            status_code=e.response.status_code,
            detail="LM Studio returned error",
        ) from e

    return resp.json()


@router.post("/models/load", response_model=LoadModelResponse)
async def load_model(
    payload: LoadModelRequest,
    request: Request,
) -> LoadModelResponse:
    """
    Load a model via LM Studio Python SDK.

    Args:
        payload: Model loading request
        request: FastAPI request object

    Returns:
        Load model response with status

    Raises:
        HTTPException: If model loading fails
    """
    logger.info(
        "Loading model_key=%s instance_id=%s ttl=%s",
        payload.model_key,
        payload.instance_id,
        payload.ttl_seconds,
    )

    # Prepare load config
    config_dict = (
        payload.load_config.model_dump(exclude_unset=True)
        if payload.load_config
        else {}
    )
    ttl = payload.ttl_seconds

    # Load model via LM Studio SDK
    try:
        if payload.instance_id:
            # Load specific instance
            model = lm_client.llm.load_new_instance(
                payload.model_key,
                payload.instance_id,
                config=config_dict if config_dict else None,
                ttl=ttl,
            )
        else:
            # Load or reuse default instance
            model = lm_client.llm(
                payload.model_key,
                config=config_dict if config_dict else None,
                ttl=ttl,
            )

        logger.info("Model loaded successfully: %s", payload.model_key)
    except Exception as e:
        logger.exception("Failed to load model: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}",
        ) from e

    # Get active model state
    app_active_model = get_active_model(request)
    default_inference = (
        payload.default_inference.model_dump(exclude_unset=True)
        if payload.default_inference
        else {}
    )

    # Activate if requested
    if payload.activate:
        app_active_model["model_key"] = payload.model_key
        app_active_model["instance_id"] = payload.instance_id
        app_active_model["default_inference"] = default_inference
        logger.info("Model activated as default: %s", payload.model_key)

    return LoadModelResponse(
        status="loaded",
        model_key=payload.model_key,
        instance_id=payload.instance_id,
        ttl_seconds=ttl,
        load_config=config_dict,
        default_inference=default_inference,
        activated=payload.activate,
    )


@router.post("/models/unload", response_model=UnloadModelResponse)
async def unload_model(
    payload: UnloadModelRequest,
    request: Request,
) -> UnloadModelResponse:
    """
    Unload a model instance via LM Studio SDK.

    Args:
        payload: Model unload request
        request: FastAPI request object

    Returns:
        Unload model response

    Raises:
        HTTPException: If unload fails or no model specified
    """
    model_key = payload.model_key
    instance_id = payload.instance_id

    # Get active model if not specified
    app_active_model = get_active_model(request)
    if not model_key:
        model_key = app_active_model.get("model_key")

    if not model_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="model_key is required if no active model is set",
        )

    logger.info(
        "Unloading model_key=%s instance_id=%s",
        model_key,
        instance_id,
    )

    try:
        # Get model reference and unload
        model = lm_client.llm(model_key)
        model.unload()
        logger.info("Model unloaded successfully: %s", model_key)
    except Exception as e:
        logger.exception("Failed to unload model: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}",
        ) from e

    # Clear active model if it was the unloaded one
    if app_active_model.get("model_key") == model_key:
        app_active_model["model_key"] = None
        app_active_model["instance_id"] = None
        app_active_model["default_inference"] = {}
        logger.info("Cleared active model state")

    return UnloadModelResponse(
        status="unloaded",
        model_key=model_key,
        instance_id=instance_id,
    )


@router.post("/models/activate", response_model=ActivateModelResponse)
async def activate_model(
    payload: ActivateModelRequest,
    request: Request,
) -> ActivateModelResponse:
    """
    Activate an already-loaded model as the default.

    This does NOT load or unload anything, just updates the gateway's
    active model state.

    Args:
        payload: Model activation request
        request: FastAPI request object

    Returns:
        Activation response
    """
    logger.info(
        "Activating model_key=%s instance_id=%s",
        payload.model_key,
        payload.instance_id,
    )

    active_model = get_active_model(request)
    active_model["model_key"] = payload.model_key
    active_model["instance_id"] = payload.instance_id

    if payload.default_inference:
        active_model["default_inference"] = payload.default_inference.model_dump(
            exclude_unset=True
        )
    else:
        active_model["default_inference"] = {}

    logger.info("Model activated: %s", payload.model_key)

    return ActivateModelResponse(
        status="activated",
        model_key=payload.model_key,
        instance_id=payload.instance_id,
        default_inference=active_model.get("default_inference", {}),
    )
