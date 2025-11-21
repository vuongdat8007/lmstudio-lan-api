"""Admin API endpoints for model management with Ollama."""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from .logging_config import get_logger
from .model_adapter import ModelMetadata, InferenceDefaults
from .ollama_client import OllamaClient

logger = get_logger("admin")

router = APIRouter(prefix="/admin", tags=["admin"])


# Request/Response models
class LoadModelRequest(BaseModel):
    """Request to load a model."""

    model_id: str = Field(..., description="Model ID (custom or Ollama name)")
    pull_if_missing: bool = Field(default=True, description="Pull model if not found locally")
    warm_up: bool = Field(default=True, description="Warm up model after loading")


class LoadModelResponse(BaseModel):
    """Response after loading a model."""

    status: str
    model_id: str
    ollama_name: str
    message: str
    details: Optional[Dict[str, Any]] = None


class UnloadModelResponse(BaseModel):
    """Response after unloading a model."""

    status: str
    message: str


class ModelListResponse(BaseModel):
    """Response containing list of models."""

    models: List[Dict[str, Any]]
    count: int


class ActiveModelResponse(BaseModel):
    """Response containing active model information."""

    active: bool
    model: Optional[Dict[str, Any]] = None
    running_models: List[Dict[str, Any]] = Field(default_factory=list)


@router.get("/models")
async def list_models(request: Request) -> dict:
    """
    List all models from Ollama, merged with registry metadata.

    Returns:
        Combined list of Ollama models with custom metadata from registry
    """
    logger.info("Listing models from Ollama")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client

        # Get models from Ollama
        ollama_models = await ollama_client.list_models()

        # If registry is enabled, merge with metadata
        if hasattr(request.app.state, 'model_adapter') and request.app.state.model_adapter:
            from .model_adapter import ModelAdapter
            adapter: ModelAdapter = request.app.state.model_adapter
            enhanced_models = adapter.merge_with_ollama_models(ollama_models)
        else:
            # No registry, use Ollama models as-is
            enhanced_models = ollama_models

        # Get running models
        running_models = await ollama_client.list_running_models()
        running_names = {m.get("name") for m in running_models}

        # Add running status to each model
        for model in enhanced_models:
            model_name = model.get("name")
            model["running"] = model_name in running_names

        return {
            "models": enhanced_models,
            "count": len(enhanced_models),
            "running_count": len(running_names),
            "success": True,
            "error": None
        }

    except Exception as e:
        logger.exception(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/models/active", response_model=ActiveModelResponse)
async def get_active_model(request: Request) -> ActiveModelResponse:
    """
    Get information about currently running models.

    Note: Ollama can run multiple models concurrently.

    Returns:
        List of running models
    """
    logger.info("Getting running models")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client
        running_models = await ollama_client.list_running_models()

        # Get default/active model from app state if set
        active_model_id = getattr(request.app.state, 'active_model_id', None)
        active_model = None

        if active_model_id and running_models:
            # Try to find active model in running list
            for model in running_models:
                model_name = model.get("name")
                # Check if this matches active_model_id (could be custom ID or Ollama name)
                if hasattr(request.app.state, 'model_adapter') and request.app.state.model_adapter:
                    from .model_adapter import ModelAdapter
                    adapter: ModelAdapter = request.app.state.model_adapter
                    ollama_name = adapter.get_ollama_name(active_model_id)
                    if ollama_name and model_name == ollama_name:
                        active_model = model
                        break
                elif model_name == active_model_id:
                    active_model = model
                    break

        return ActiveModelResponse(
            active=len(running_models) > 0,
            model=active_model,
            running_models=running_models
        )

    except Exception as e:
        logger.exception(f"Error getting active models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active models: {str(e)}"
        )


@router.post("/models/load", response_model=LoadModelResponse)
async def load_model(
    payload: LoadModelRequest,
    request: Request
) -> LoadModelResponse:
    """
    Load a model in Ollama.

    This ensures the model exists (pulling if needed) and optionally warms it up.
    With Ollama, models load automatically on first inference request.

    Args:
        payload: Model load request with model_id

    Returns:
        Load status and model information
    """
    logger.info(f"Loading model: {payload.model_id}")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client

        # Resolve model name (custom ID → Ollama name)
        ollama_name = payload.model_id
        if hasattr(request.app.state, 'model_adapter') and request.app.state.model_adapter:
            from .model_adapter import ModelAdapter
            adapter: ModelAdapter = request.app.state.model_adapter
            ollama_name = adapter.resolve_model_name(payload.model_id)
            logger.info(f"Resolved {payload.model_id} → {ollama_name}")

        # Check if model exists
        model_exists = await ollama_client.check_model_exists(ollama_name)

        if not model_exists:
            if payload.pull_if_missing:
                logger.info(f"Model not found, pulling: {ollama_name}")
                # Pull model (streaming operation)
                async for progress in ollama_client.pull_model(ollama_name):
                    status_msg = progress.get("status")
                    if status_msg:
                        logger.debug(f"Pull progress: {status_msg}")
                logger.info(f"Model pulled successfully: {ollama_name}")
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model not found in Ollama: {ollama_name}. Set pull_if_missing=true to download."
                )

        # Warm up model if requested
        if payload.warm_up:
            logger.info(f"Warming up model: {ollama_name}")
            await ollama_client.ensure_model_loaded(ollama_name)

        # Set as active model
        request.app.state.active_model_id = payload.model_id

        # Get model info
        model_info = await ollama_client.get_model_info(ollama_name)

        return LoadModelResponse(
            status="success",
            model_id=payload.model_id,
            ollama_name=ollama_name,
            message=f"Model {payload.model_id} loaded successfully",
            details=model_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error loading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}"
        )


@router.post("/models/unload", response_model=UnloadModelResponse)
async def unload_model(request: Request, model_id: Optional[str] = None) -> UnloadModelResponse:
    """
    Unload a model (optional with Ollama).

    Ollama manages model lifecycle automatically. This endpoint is mainly for
    clearing the "active model" state in the gateway.

    Args:
        model_id: Optional specific model to unload

    Returns:
        Unload status
    """
    logger.info(f"Unload requested for: {model_id or 'active model'}")

    try:
        # Clear active model state
        if hasattr(request.app.state, 'active_model_id'):
            if model_id is None or request.app.state.active_model_id == model_id:
                request.app.state.active_model_id = None

        return UnloadModelResponse(
            status="success",
            message="Model unload requested. Ollama will manage memory automatically."
        )

    except Exception as e:
        logger.exception(f"Error unloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}"
        )


@router.post("/models/reload", response_model=LoadModelResponse)
async def reload_model(request: Request) -> LoadModelResponse:
    """
    Reload the currently active model.

    With Ollama, this mainly re-warms the model.

    Returns:
        Reload status
    """
    logger.info("Reloading active model")

    try:
        active_model_id = getattr(request.app.state, 'active_model_id', None)

        if active_model_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active model set"
            )

        # Reload by calling load again
        load_request = LoadModelRequest(
            model_id=active_model_id,
            pull_if_missing=False,
            warm_up=True
        )

        return await load_model(load_request, request)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error reloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload model: {str(e)}"
        )


# Registry Management Endpoints

@router.post("/models/register", response_model=Dict[str, Any])
async def register_model(
    model: ModelMetadata,
    request: Request
) -> Dict[str, Any]:
    """
    Register a new model in the registry.

    This adds custom metadata for an Ollama model.

    Args:
        model: Model metadata

    Returns:
        Registration status
    """
    logger.info(f"Registering model: {model.model_id} → {model.ollama_name}")

    try:
        if not hasattr(request.app.state, 'model_adapter') or not request.app.state.model_adapter:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Model registry is not enabled. Set MODEL_REGISTRY_PATH in configuration."
            )

        from .model_adapter import ModelAdapter
        adapter: ModelAdapter = request.app.state.model_adapter

        # Check if model already exists
        if adapter.get_model(model.model_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model with ID '{model.model_id}' already exists"
            )

        # Verify model exists in Ollama
        ollama_client: OllamaClient = request.app.state.ollama_client
        if not await ollama_client.check_model_exists(model.ollama_name):
            logger.warning(f"Registering model that doesn't exist in Ollama: {model.ollama_name}")

        adapter.add_model(model)
        adapter.save_registry()

        return {
            "status": "success",
            "model_id": model.model_id,
            "ollama_name": model.ollama_name,
            "message": f"Model {model.model_id} registered successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error registering model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register model: {str(e)}"
        )


@router.put("/models/{model_id}", response_model=Dict[str, Any])
async def update_model(
    model_id: str,
    updates: Dict[str, Any],
    request: Request
) -> Dict[str, Any]:
    """
    Update model metadata in the registry.

    Args:
        model_id: Model ID to update
        updates: Fields to update

    Returns:
        Update status
    """
    logger.info(f"Updating model: {model_id}")

    try:
        if not hasattr(request.app.state, 'model_adapter') or not request.app.state.model_adapter:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Model registry is not enabled"
            )

        from .model_adapter import ModelAdapter
        adapter: ModelAdapter = request.app.state.model_adapter

        if not adapter.update_model(model_id, updates):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_id}"
            )

        adapter.save_registry()

        return {
            "status": "success",
            "model_id": model_id,
            "message": f"Model {model_id} updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update model: {str(e)}"
        )


@router.delete("/models/{model_id}", response_model=Dict[str, Any])
async def delete_model(
    model_id: str,
    request: Request,
    delete_from_ollama: bool = False
) -> Dict[str, Any]:
    """
    Delete a model from the registry.

    Args:
        model_id: Model ID to delete
        delete_from_ollama: Also delete from Ollama (default: False)

    Returns:
        Deletion status
    """
    logger.info(f"Deleting model from registry: {model_id}")

    try:
        if not hasattr(request.app.state, 'model_adapter') or not request.app.state.model_adapter:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Model registry is not enabled"
            )

        from .model_adapter import ModelAdapter
        adapter: ModelAdapter = request.app.state.model_adapter

        # Get model info before deleting
        model = adapter.get_model(model_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_id}"
            )

        ollama_name = model.ollama_name

        # Delete from registry
        adapter.delete_model(model_id)
        adapter.save_registry()

        # Optionally delete from Ollama
        if delete_from_ollama:
            ollama_client: OllamaClient = request.app.state.ollama_client
            await ollama_client.delete_model(ollama_name)
            logger.info(f"Deleted model from Ollama: {ollama_name}")

        return {
            "status": "success",
            "model_id": model_id,
            "ollama_name": ollama_name,
            "deleted_from_ollama": delete_from_ollama,
            "message": f"Model {model_id} deleted from registry" +
                      (" and Ollama" if delete_from_ollama else "")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}"
        )


@router.post("/models/pull", response_model=Dict[str, Any])
async def pull_model(
    model_name: str,
    request: Request
) -> Dict[str, Any]:
    """
    Pull a model from Ollama registry.

    Args:
        model_name: Ollama model name (e.g., "llama3:latest")

    Returns:
        Pull status
    """
    logger.info(f"Pulling model: {model_name}")

    try:
        ollama_client: OllamaClient = request.app.state.ollama_client

        # Pull model (streaming, but we'll consume all progress)
        async for progress in ollama_client.pull_model(model_name):
            status_msg = progress.get("status")
            if status_msg:
                logger.debug(f"Pull progress: {status_msg}")

        return {
            "status": "success",
            "model_name": model_name,
            "message": f"Model {model_name} pulled successfully"
        }

    except Exception as e:
        logger.exception(f"Error pulling model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull model: {str(e)}"
        )
