"""Admin API endpoints for model management."""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from .logging_config import get_logger
from .model_registry import Model, ModelRegistry
from .process_manager import LlamaServerManager, ProcessStatus

logger = get_logger("admin")

router = APIRouter(prefix="/admin", tags=["admin"])


# Request/Response models
class LoadModelRequest(BaseModel):
    """Request to load a model."""

    model_id: str = Field(..., description="Model ID from registry")


class LoadModelResponse(BaseModel):
    """Response after loading a model."""

    status: str
    model_id: str
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
    status: str
    uptime_seconds: Optional[int] = None


@router.get("/models", response_model=ModelListResponse)
async def list_models(request: Request) -> ModelListResponse:
    """
    List all models in the registry.

    Returns:
        List of available models
    """
    logger.info("Listing models from registry")

    try:
        registry: ModelRegistry = request.app.state.model_registry
        models = registry.list_models()

        models_data = [
            {
                "model_id": model.model_id,
                "name": model.name,
                "description": model.description,
                "path": model.path,
                "config": model.config.model_dump(),
                "default_inference": model.default_inference.model_dump(),
            }
            for model in models
        ]

        return ModelListResponse(models=models_data, count=len(models_data))

    except Exception as e:
        logger.exception(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/models/active", response_model=ActiveModelResponse)
async def get_active_model(request: Request) -> ActiveModelResponse:
    """
    Get information about the currently active model.

    Returns:
        Active model information or null if no model is loaded
    """
    logger.info("Getting active model")

    try:
        manager: LlamaServerManager = request.app.state.process_manager
        process_status = manager.get_status()

        is_active = process_status["status"] == ProcessStatus.RUNNING.value

        return ActiveModelResponse(
            active=is_active,
            model=process_status["model"],
            status=process_status["status"],
            uptime_seconds=process_status["uptime_seconds"]
        )

    except Exception as e:
        logger.exception(f"Error getting active model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active model: {str(e)}"
        )


@router.post("/models/load", response_model=LoadModelResponse)
async def load_model(
    payload: LoadModelRequest,
    request: Request
) -> LoadModelResponse:
    """
    Load a model by ID. Stops current model if running.

    Args:
        payload: Model ID to load

    Returns:
        Load status and model information
    """
    logger.info(f"Loading model: {payload.model_id}")

    try:
        registry: ModelRegistry = request.app.state.model_registry
        manager: LlamaServerManager = request.app.state.process_manager

        # Get model from registry
        model = registry.get_model(payload.model_id)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {payload.model_id}"
            )

        # Stop current model if running
        if manager.status not in [ProcessStatus.STOPPED, ProcessStatus.ERROR]:
            logger.info("Stopping current model before loading new one")
            await manager.stop()

        # Start new model
        await manager.start(model)

        return LoadModelResponse(
            status="success",
            model_id=payload.model_id,
            message=f"Model {payload.model_id} loaded successfully",
            details=manager.get_status()
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
async def unload_model(request: Request) -> UnloadModelResponse:
    """
    Unload the currently running model.

    Returns:
        Unload status
    """
    logger.info("Unloading current model")

    try:
        manager: LlamaServerManager = request.app.state.process_manager

        if manager.status == ProcessStatus.STOPPED:
            return UnloadModelResponse(
                status="success",
                message="No model is currently loaded"
            )

        await manager.stop()

        return UnloadModelResponse(
            status="success",
            message="Model unloaded successfully"
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
    Reload the currently running model.

    Returns:
        Reload status
    """
    logger.info("Reloading current model")

    try:
        manager: LlamaServerManager = request.app.state.process_manager

        if manager.current_model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No model is currently loaded"
            )

        model_id = manager.current_model.model_id
        await manager.restart()

        return LoadModelResponse(
            status="success",
            model_id=model_id,
            message=f"Model {model_id} reloaded successfully",
            details=manager.get_status()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error reloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload model: {str(e)}"
        )


@router.post("/models/register", response_model=Dict[str, Any])
async def register_model(
    model: Model,
    request: Request
) -> Dict[str, Any]:
    """
    Register a new model in the registry.

    Args:
        model: Model configuration

    Returns:
        Registration status
    """
    logger.info(f"Registering new model: {model.model_id}")

    try:
        registry: ModelRegistry = request.app.state.model_registry

        # Check if model already exists
        if registry.model_exists(model.model_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model with ID '{model.model_id}' already exists"
            )

        registry.add_model(model)

        return {
            "status": "success",
            "model_id": model.model_id,
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
    model: Model,
    request: Request
) -> Dict[str, Any]:
    """
    Update an existing model in the registry.

    Args:
        model_id: Model ID to update
        model: Updated model configuration

    Returns:
        Update status
    """
    logger.info(f"Updating model: {model_id}")

    try:
        registry: ModelRegistry = request.app.state.model_registry

        if not registry.model_exists(model_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_id}"
            )

        registry.update_model(model_id, model)

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
    request: Request
) -> Dict[str, Any]:
    """
    Delete a model from the registry.

    Args:
        model_id: Model ID to delete

    Returns:
        Deletion status
    """
    logger.info(f"Deleting model: {model_id}")

    try:
        registry: ModelRegistry = request.app.state.model_registry
        manager: LlamaServerManager = request.app.state.process_manager

        if not registry.model_exists(model_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {model_id}"
            )

        # Check if model is currently loaded
        if (manager.current_model and
            manager.current_model.model_id == model_id and
            manager.status == ProcessStatus.RUNNING):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete model '{model_id}' while it is loaded. Unload it first."
            )

        registry.remove_model(model_id)

        return {
            "status": "success",
            "model_id": model_id,
            "message": f"Model {model_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}"
        )
