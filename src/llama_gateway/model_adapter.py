"""
Model Adapter for Ollama

This module provides a bridge between the custom model registry and Ollama's
native model names. It allows keeping user-friendly model IDs, default inference
parameters, and metadata while using Ollama for actual model storage.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger("llama_gateway.model_adapter")


class InferenceDefaults(BaseModel):
    """Default inference parameters for a model."""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = Field(None, alias="num_predict")
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    repeat_penalty: Optional[float] = None
    seed: Optional[int] = None
    num_ctx: Optional[int] = None  # Context length
    num_gpu: Optional[int] = None  # GPU layers


class ModelMetadata(BaseModel):
    """
    Model metadata stored in registry.

    Maps custom model IDs to Ollama model names with additional metadata.
    """
    model_id: str = Field(..., description="Custom model identifier")
    ollama_name: str = Field(..., description="Ollama model name (e.g., 'qwen3:30b')")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Model description")
    default_inference: InferenceDefaults = Field(
        default_factory=InferenceDefaults,
        description="Default inference parameters"
    )
    tags: List[str] = Field(default_factory=list, description="Custom tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata")


class ModelRegistry(BaseModel):
    """Registry of model metadata."""
    models: List[ModelMetadata] = Field(default_factory=list)


class ModelAdapter:
    """
    Adapter for managing model registry and mapping to Ollama models.

    Provides:
    - Mapping custom model IDs to Ollama model names
    - Storage of default inference parameters per model
    - Model metadata management
    - Backward compatibility with existing API
    """

    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize model adapter.

        Args:
            registry_path: Path to registry JSON file (optional)
        """
        self.registry_path = Path(registry_path) if registry_path else None
        self.registry: ModelRegistry = ModelRegistry()

        if self.registry_path and self.registry_path.exists():
            self.load_registry()
        else:
            logger.info("No registry file found, starting with empty registry")

    def load_registry(self):
        """
        Load registry from JSON file.

        Raises:
            json.JSONDecodeError: If file is not valid JSON
            ValidationError: If registry structure is invalid
        """
        if not self.registry_path:
            logger.warning("No registry path configured")
            return

        try:
            with open(self.registry_path, "r") as f:
                data = json.load(f)
                self.registry = ModelRegistry(**data)
                logger.info("Loaded %d models from registry: %s", len(self.registry.models), self.registry_path)
        except FileNotFoundError:
            logger.warning("Registry file not found: %s", self.registry_path)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in registry file: %s", e)
            raise
        except Exception as e:
            logger.error("Error loading registry: %s", e)
            raise

    def save_registry(self):
        """
        Save registry to JSON file.

        Raises:
            IOError: If file cannot be written
        """
        if not self.registry_path:
            logger.warning("No registry path configured, cannot save")
            return

        try:
            # Create parent directory if it doesn't exist
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.registry_path, "w") as f:
                json.dump(
                    self.registry.model_dump(),
                    f,
                    indent=2,
                    default=str
                )
            logger.info("Saved registry with %d models to %s", len(self.registry.models), self.registry_path)
        except Exception as e:
            logger.error("Error saving registry: %s", e)
            raise

    def get_ollama_name(self, model_id: str) -> Optional[str]:
        """
        Get Ollama model name for a custom model ID.

        Args:
            model_id: Custom model identifier

        Returns:
            Ollama model name or None if not found
        """
        model = self.get_model(model_id)
        return model.ollama_name if model else None

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """
        Get model metadata by ID.

        Args:
            model_id: Custom model identifier

        Returns:
            ModelMetadata or None if not found
        """
        return next((m for m in self.registry.models if m.model_id == model_id), None)

    def get_by_ollama_name(self, ollama_name: str) -> Optional[ModelMetadata]:
        """
        Get model metadata by Ollama model name.

        Args:
            ollama_name: Ollama model name

        Returns:
            ModelMetadata or None if not found
        """
        return next((m for m in self.registry.models if m.ollama_name == ollama_name), None)

    def list_models(self) -> List[ModelMetadata]:
        """
        List all models in registry.

        Returns:
            List of ModelMetadata
        """
        return self.registry.models

    def add_model(self, model: ModelMetadata) -> bool:
        """
        Add a new model to registry.

        Args:
            model: ModelMetadata to add

        Returns:
            True if added, False if already exists
        """
        if self.get_model(model.model_id):
            logger.warning("Model already exists: %s", model.model_id)
            return False

        self.registry.models.append(model)
        logger.info("Added model: %s → %s", model.model_id, model.ollama_name)
        return True

    def update_model(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update model metadata.

        Args:
            model_id: Model ID to update
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        model = self.get_model(model_id)
        if not model:
            logger.warning("Model not found: %s", model_id)
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)

        logger.info("Updated model: %s", model_id)
        return True

    def delete_model(self, model_id: str) -> bool:
        """
        Delete model from registry.

        Args:
            model_id: Model ID to delete

        Returns:
            True if deleted, False if not found
        """
        model = self.get_model(model_id)
        if not model:
            logger.warning("Model not found: %s", model_id)
            return False

        self.registry.models = [m for m in self.registry.models if m.model_id != model_id]
        logger.info("Deleted model: %s", model_id)
        return True

    def get_inference_defaults(self, model_id: str) -> Dict[str, Any]:
        """
        Get default inference parameters for a model.

        Args:
            model_id: Custom model identifier

        Returns:
            Dictionary of default parameters (empty if not found)
        """
        model = self.get_model(model_id)
        if not model:
            return {}

        # Convert to dict and remove None values
        defaults = model.default_inference.model_dump(exclude_none=True)
        return defaults

    def merge_with_ollama_models(self, ollama_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge registry metadata with Ollama model list.

        Combines Ollama's native model information with custom metadata from registry.

        Args:
            ollama_models: List of models from Ollama API

        Returns:
            Enhanced model list with custom metadata
        """
        result = []

        for ollama_model in ollama_models:
            ollama_name = ollama_model.get("name")
            enhanced = ollama_model.copy()

            # Find matching registry entry
            registry_model = self.get_by_ollama_name(ollama_name)

            if registry_model:
                # Add custom metadata
                enhanced.update({
                    "model_id": registry_model.model_id,
                    "display_name": registry_model.name,
                    "description": registry_model.description,
                    "default_inference": registry_model.default_inference.model_dump(exclude_none=True),
                    "tags": registry_model.tags,
                    "custom_metadata": registry_model.metadata,
                    "in_registry": True,
                })
            else:
                # Not in registry, use Ollama name as-is
                enhanced.update({
                    "model_id": ollama_name,
                    "display_name": ollama_name,
                    "in_registry": False,
                })

            result.append(enhanced)

        return result

    def resolve_model_name(self, identifier: str) -> str:
        """
        Resolve a model identifier to Ollama model name.

        Accepts either custom model ID or direct Ollama name.

        Args:
            identifier: Either custom model_id or Ollama model name

        Returns:
            Ollama model name

        Raises:
            ValueError: If identifier cannot be resolved
        """
        # Try as custom model ID first
        ollama_name = self.get_ollama_name(identifier)
        if ollama_name:
            return ollama_name

        # Assume it's a direct Ollama name
        logger.info("Treating '%s' as direct Ollama model name", identifier)
        return identifier

    def create_from_ollama_model(
        self,
        ollama_name: str,
        model_id: Optional[str] = None,
        **kwargs
    ) -> ModelMetadata:
        """
        Create registry entry from Ollama model.

        Args:
            ollama_name: Ollama model name
            model_id: Custom model ID (defaults to ollama_name)
            **kwargs: Additional metadata fields

        Returns:
            Created ModelMetadata
        """
        model_id = model_id or ollama_name

        return ModelMetadata(
            model_id=model_id,
            ollama_name=ollama_name,
            name=kwargs.get("name", ollama_name),
            description=kwargs.get("description"),
            default_inference=InferenceDefaults(**kwargs.get("default_inference", {})),
            tags=kwargs.get("tags", []),
            metadata=kwargs.get("metadata", {})
        )


def migrate_legacy_registry(legacy_path: str, adapter: ModelAdapter) -> int:
    """
    Migrate legacy llama-server registry to Ollama format.

    Args:
        legacy_path: Path to old registry.json
        adapter: ModelAdapter to populate

    Returns:
        Number of models migrated
    """
    try:
        with open(legacy_path, "r") as f:
            legacy_data = json.load(f)

        count = 0
        for model in legacy_data.get("models", []):
            # Extract model name from path (last part of filename without extension)
            model_path = model.get("path", "")
            filename = Path(model_path).stem

            # Create metadata
            metadata = adapter.create_from_ollama_model(
                ollama_name=f"{filename}:latest",  # Assume :latest tag
                model_id=model.get("model_id"),
                name=model.get("name", filename),
                description=model.get("description"),
                default_inference=model.get("default_inference", {}),
            )

            if adapter.add_model(metadata):
                count += 1

        adapter.save_registry()
        logger.info("Migrated %d models from legacy registry", count)
        return count

    except Exception as e:
        logger.error("Error migrating legacy registry: %s", e)
        raise
