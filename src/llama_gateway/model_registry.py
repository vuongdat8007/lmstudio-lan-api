"""Model registry for managing model configurations."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from .logging_config import get_logger
from .settings import settings

logger = get_logger("model_registry")


class ModelConfig(BaseModel):
    """Configuration for a model."""

    context_length: int = Field(default=4096, ge=512, description="Context size")
    n_gpu_layers: int = Field(default=999, ge=0, description="Number of GPU layers")
    batch_size: int = Field(default=2048, ge=1, description="Batch size")
    host: str = Field(default="10.0.0.181", description="llama-server bind host")
    port: int = Field(default=8080, ge=1, le=65535, description="llama-server bind port")
    flash_attention: bool = Field(default=False, description="Enable flash attention")
    no_mmap: bool = Field(default=False, description="Disable memory mapping")
    parallel: int = Field(default=1, ge=1, description="Number of parallel sequences")
    timeout: int = Field(default=600, ge=60, description="Server timeout in seconds")
    additional_args: List[str] = Field(default_factory=list, description="Additional CLI args")


class InferenceDefaults(BaseModel):
    """Default inference parameters for a model."""

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class Model(BaseModel):
    """Model definition."""

    model_id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    description: Optional[str] = Field(default=None, description="Model description")
    path: str = Field(..., description="Path to model file (GGUF)")
    config: ModelConfig = Field(default_factory=ModelConfig, description="Model configuration")
    default_inference: InferenceDefaults = Field(
        default_factory=InferenceDefaults,
        description="Default inference parameters"
    )


class ModelRegistry:
    """Registry for managing model configurations."""

    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize the model registry.

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path or settings.MODEL_REGISTRY_PATH)
        self._models: Dict[str, Model] = {}
        self.load()

    def load(self) -> None:
        """Load models from registry file."""
        if not self.registry_path.exists():
            logger.warning(f"Registry file not found: {self.registry_path}")
            logger.info("Creating empty registry")
            self.save()
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            models_data = data.get("models", [])
            self._models = {}

            for model_data in models_data:
                model = Model(**model_data)
                self._models[model.model_id] = model

            logger.info(f"Loaded {len(self._models)} model(s) from registry")

        except Exception as e:
            logger.exception(f"Failed to load registry: {e}")
            raise

    def save(self) -> None:
        """Save models to registry file."""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "models": [
                    model.model_dump() for model in self._models.values()
                ]
            }

            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._models)} model(s) to registry")

        except Exception as e:
            logger.exception(f"Failed to save registry: {e}")
            raise

    def list_models(self) -> List[Model]:
        """Get all models."""
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[Model]:
        """
        Get a model by ID.

        Args:
            model_id: Model identifier

        Returns:
            Model or None if not found
        """
        return self._models.get(model_id)

    def add_model(self, model: Model) -> None:
        """
        Add a new model to the registry.

        Args:
            model: Model to add

        Raises:
            ValueError: If model_id already exists
        """
        if model.model_id in self._models:
            raise ValueError(f"Model with ID '{model.model_id}' already exists")

        self._models[model.model_id] = model
        self.save()
        logger.info(f"Added model: {model.model_id}")

    def update_model(self, model_id: str, model: Model) -> None:
        """
        Update an existing model.

        Args:
            model_id: Model identifier
            model: Updated model

        Raises:
            ValueError: If model not found
        """
        if model_id not in self._models:
            raise ValueError(f"Model with ID '{model_id}' not found")

        # Ensure model_id doesn't change
        model.model_id = model_id
        self._models[model_id] = model
        self.save()
        logger.info(f"Updated model: {model_id}")

    def remove_model(self, model_id: str) -> None:
        """
        Remove a model from the registry.

        Args:
            model_id: Model identifier

        Raises:
            ValueError: If model not found
        """
        if model_id not in self._models:
            raise ValueError(f"Model with ID '{model_id}' not found")

        del self._models[model_id]
        self.save()
        logger.info(f"Removed model: {model_id}")

    def model_exists(self, model_id: str) -> bool:
        """Check if a model exists."""
        return model_id in self._models
