# src/lmstudio_gateway/admin_models.py
"""
Admin API router for model management.
Provides endpoints to load, unload, activate, and list models.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from .dependencies import get_active_model, get_debug_state, get_http_client
from .lm_studio_client import get_lm_studio_client
from .debug import broadcast_debug_event

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
async def list_models() -> Dict[str, Any]:
    """
    List available models from LM Studio via SDK.

    Returns:
        Dictionary containing loaded and downloaded models

    Raises:
        HTTPException: If LM Studio is unreachable or returns an error
    """
    try:
        logger.info("Fetching model list from LM Studio SDK")

        client_service = get_lm_studio_client()
        client = await client_service.get_client()

        # Get both loaded and downloaded models using SDK
        loaded_models = await asyncio.to_thread(client.llm.list_loaded)
        downloaded_models = await asyncio.to_thread(client.system.list_downloaded_models)

        return {
            "loaded": [
                {
                    "path": model.path,
                    "identifier": getattr(model, "identifier", None)
                }
                for model in loaded_models
            ],
            "downloaded": [
                {
                    "path": model.path,
                    "size": getattr(model, "size_bytes", 0),
                    "type": getattr(model, "type", "unknown")
                }
                for model in downloaded_models
            ]
        }

    except Exception as error:
        logger.exception("Error fetching models via SDK: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LM Studio SDK error: {str(error)}",
        ) from error


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
    start_time = time.time()
    debug_state = get_debug_state(request)

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

    # Update debug state
    debug_state["status"] = "loading_model"
    debug_state["current_operation"] = {
        "type": "model_load",
        "model_key": payload.model_key,
        "progress": 0,
        "started_at": datetime.utcnow().isoformat() + "Z"
    }

    # Broadcast load start event
    await broadcast_debug_event("model_load_start", {
        "model_key": payload.model_key,
        "instance_id": payload.instance_id,
        "load_config": config_dict
    })

    # Load model via LM Studio SDK
    try:
        client_service = get_lm_studio_client()
        client = await client_service.get_client()

        # Load model using SDK
        if payload.instance_id:
            # Load with specific instance ID
            model = await asyncio.to_thread(
                client.llm.load,
                payload.model_key,
                identifier=payload.instance_id,
                config=config_dict if config_dict else None
            )
        else:
            # Load default instance
            model = await asyncio.to_thread(
                client.llm.load,
                payload.model_key,
                config=config_dict if config_dict else None
            )

        logger.info("Model loaded successfully via SDK: %s", payload.model_key)

        # Update debug state
        debug_state["status"] = "idle"
        debug_state["current_operation"] = None

        total_time_ms = int((time.time() - start_time) * 1000)

        # Broadcast completion event
        await broadcast_debug_event("model_load_complete", {
            "model_key": payload.model_key,
            "instance_id": payload.instance_id,
            "activated": payload.activate,
            "total_time_ms": total_time_ms,
            "load_config": config_dict
        })

    except Exception as e:
        debug_state["status"] = "error"
        debug_state["total_errors"] = debug_state.get("total_errors", 0) + 1

        total_time_ms = int((time.time() - start_time) * 1000)

        logger.exception("Failed to load model via SDK: %s", e)

        await broadcast_debug_event("error", {
            "operation": "model_load",
            "model_key": payload.model_key,
            "error": str(e),
            "total_time_ms": total_time_ms
        })

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
    start_time = time.time()
    debug_state = get_debug_state(request)

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

    # Update debug state
    debug_state["status"] = "loading_model"  # Using loading_model for any model operation
    debug_state["current_operation"] = {
        "type": "model_unload",
        "model_key": model_key,
        "progress": 0,
        "started_at": datetime.utcnow().isoformat() + "Z"
    }

    # Broadcast unload start event
    await broadcast_debug_event("model_unload_start", {
        "model_key": model_key,
        "instance_id": instance_id
    })

    try:
        client_service = get_lm_studio_client()
        client = await client_service.get_client()

        # Find and unload the model
        loaded_models = await asyncio.to_thread(client.llm.list_loaded)

        model_to_unload = None
        for model in loaded_models:
            if instance_id:
                # Match by instance ID
                if getattr(model, "identifier", None) == instance_id:
                    model_to_unload = model
                    break
            else:
                # Match by path
                if model.path == model_key:
                    model_to_unload = model
                    break

        if not model_to_unload:
            not_found_msg = f"Model not found: {model_key}"
            if instance_id:
                not_found_msg += f" (instance: {instance_id})"

            logger.warning(not_found_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=not_found_msg
            )

        # Unload the model
        await asyncio.to_thread(model_to_unload.unload)
        logger.info("Model unloaded successfully via SDK: %s", model_key)

        # Update debug state
        debug_state["status"] = "idle"
        debug_state["current_operation"] = None

        total_time_ms = int((time.time() - start_time) * 1000)

        # Broadcast completion event
        await broadcast_debug_event("model_unload_complete", {
            "model_key": model_key,
            "instance_id": instance_id,
            "total_time_ms": total_time_ms
        })

    except HTTPException:
        raise
    except Exception as e:
        debug_state["status"] = "error"
        debug_state["total_errors"] = debug_state.get("total_errors", 0) + 1

        total_time_ms = int((time.time() - start_time) * 1000)

        logger.exception("Failed to unload model via SDK: %s", e)

        await broadcast_debug_event("error", {
            "operation": "model_unload",
            "model_key": model_key,
            "error": str(e),
            "total_time_ms": total_time_ms
        })

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}",
        ) from e

    # Clear active model if it was the unloaded one
    if app_active_model.get("model_key") == model_key:
        if not instance_id or app_active_model.get("instance_id") == instance_id:
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

    default_inference = (
        payload.default_inference.model_dump(exclude_unset=True)
        if payload.default_inference
        else {}
    )

    # Broadcast activation event
    await broadcast_debug_event("model_activate", {
        "model_key": payload.model_key,
        "instance_id": payload.instance_id,
        "default_inference": default_inference
    })

    # Update active model state
    active_model["model_key"] = payload.model_key
    active_model["instance_id"] = payload.instance_id
    active_model["default_inference"] = default_inference

    logger.info("Model activated: %s", payload.model_key)

    return ActivateModelResponse(
        status="activated",
        model_key=payload.model_key,
        instance_id=payload.instance_id,
        default_inference=default_inference,
    )
