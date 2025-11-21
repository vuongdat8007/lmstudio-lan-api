"""
Ollama API Client

This module provides an async HTTP client for interacting with the Ollama API.
Replaces the process_manager.py subprocess approach with direct API communication.
"""

import logging
from typing import Dict, Any, List, Optional, AsyncIterator
import httpx
from datetime import datetime

logger = logging.getLogger("llama_gateway.ollama_client")


class OllamaClient:
    """
    Async client for Ollama API.

    Provides methods for model management, inference, and monitoring.
    Ollama runs as a system service, so no process lifecycle management needed.
    """

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 300):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            timeout: Request timeout in seconds (default: 300)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        logger.info("OllamaClient initialized with base_url=%s", self.base_url)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        """Close HTTP client and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("OllamaClient closed")

    # Health Check

    async def is_healthy(self) -> bool:
        """
        Check if Ollama service is running and accessible.

        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/version")
            response.raise_for_status()
            logger.info("Ollama health check passed")
            return True
        except Exception as e:
            logger.error("Ollama health check failed: %s", e)
            return False

    async def get_version(self) -> Dict[str, Any]:
        """
        Get Ollama version information.

        Returns:
            Version info dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        response = await client.get("/api/version")
        response.raise_for_status()
        return response.json()

    # Model Management

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available models in Ollama.

        Returns:
            List of model dictionaries with name, size, modified date, etc.

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        response = await client.get("/api/tags")
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        logger.info("Listed %d models from Ollama", len(models))
        return models

    async def pull_model(self, name: str, insecure: bool = False) -> AsyncIterator[Dict[str, Any]]:
        """
        Pull (download) a model from Ollama registry.

        This is a streaming operation that yields progress updates.

        Args:
            name: Model name (e.g., "qwen3:30b", "llama3:latest")
            insecure: Allow insecure connections (default: False)

        Yields:
            Progress dictionaries with status, digest, total, completed

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {"name": name, "insecure": insecure}

        logger.info("Pulling model: %s", name)

        async with client.stream("POST", "/api/pull", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    import json
                    yield json.loads(line)

    async def delete_model(self, name: str) -> Dict[str, Any]:
        """
        Delete a model from Ollama.

        Args:
            name: Model name to delete

        Returns:
            Response dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {"name": name}
        response = await client.request("DELETE", "/api/delete", json=payload)
        response.raise_for_status()
        logger.info("Deleted model: %s", name)
        return response.json() if response.text else {}

    async def show_model(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.

        Args:
            name: Model name

        Returns:
            Model details including modelfile, parameters, template, etc.

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {"name": name}
        response = await client.post("/api/show", json=payload)
        response.raise_for_status()
        return response.json()

    async def copy_model(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a model (create an alias).

        Args:
            source: Source model name
            destination: Destination model name

        Returns:
            Response dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {"source": source, "destination": destination}
        response = await client.post("/api/copy", json=payload)
        response.raise_for_status()
        logger.info("Copied model %s → %s", source, destination)
        return response.json() if response.text else {}

    async def create_model(
        self,
        name: str,
        modelfile: str,
        stream: bool = False
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Create a model from a Modelfile.

        Args:
            name: Model name to create
            modelfile: Modelfile content
            stream: Stream creation progress (default: False)

        Yields:
            Progress dictionaries if stream=True

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {"name": name, "modelfile": modelfile, "stream": stream}

        logger.info("Creating model: %s", name)

        if stream:
            async with client.stream("POST", "/api/create", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        yield json.loads(line)
        else:
            response = await client.post("/api/create", json=payload)
            response.raise_for_status()
            yield response.json()

    # Model Status

    async def list_running_models(self) -> List[Dict[str, Any]]:
        """
        List currently running (loaded) models.

        Returns:
            List of running model dictionaries with name, size, expires_at, etc.

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        response = await client.get("/api/ps")
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        logger.info("Listed %d running models", len(models))
        return models

    # Inference

    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        **options
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate a completion.

        Args:
            model: Model name
            prompt: Input prompt
            stream: Stream response (default: False)
            **options: Additional parameters (temperature, num_predict, etc.)

        Yields:
            Response dictionaries with response, done, context, etc.

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            **options
        }

        if stream:
            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        yield json.loads(line)
        else:
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            yield response.json()

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **options
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Chat completion (multi-turn conversation).

        Args:
            model: Model name
            messages: List of message dicts with 'role' and 'content'
            stream: Stream response (default: False)
            **options: Additional parameters (temperature, num_predict, etc.)

        Yields:
            Response dictionaries with message, done, etc.

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **options
        }

        if stream:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        yield json.loads(line)
        else:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            yield response.json()

    # Embeddings

    async def embeddings(
        self,
        model: str,
        prompt: str,
        **options
    ) -> Dict[str, Any]:
        """
        Generate embeddings for a prompt.

        Args:
            model: Model name
            prompt: Input prompt
            **options: Additional parameters

        Returns:
            Embeddings response with embedding vector

        Raises:
            httpx.HTTPError: If request fails
        """
        client = await self._get_client()
        payload = {
            "model": model,
            "prompt": prompt,
            **options
        }
        response = await client.post("/api/embeddings", json=payload)
        response.raise_for_status()
        return response.json()

    # Utility Methods

    async def check_model_exists(self, name: str) -> bool:
        """
        Check if a model exists in Ollama.

        Args:
            name: Model name to check

        Returns:
            True if model exists, False otherwise
        """
        try:
            models = await self.list_models()
            return any(m.get("name") == name for m in models)
        except Exception as e:
            logger.error("Error checking if model exists: %s", e)
            return False

    async def ensure_model_loaded(self, name: str) -> bool:
        """
        Ensure a model is loaded by making a warm-up request.

        Ollama loads models on-demand, so this triggers loading if needed.

        Args:
            name: Model name

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Warming up model: %s", name)
            # Make a minimal generation request to trigger loading
            async for _ in self.generate(model=name, prompt="", stream=False):
                pass
            return True
        except Exception as e:
            logger.error("Error warming up model %s: %s", name, e)
            return False

    async def get_model_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive model information combining list and show data.

        Args:
            name: Model name

        Returns:
            Combined model info or None if not found
        """
        try:
            # Get basic info from list
            models = await self.list_models()
            model_basic = next((m for m in models if m.get("name") == name), None)

            if not model_basic:
                return None

            # Get detailed info from show
            try:
                model_details = await self.show_model(name)
                return {**model_basic, **model_details}
            except Exception as e:
                logger.warning("Could not get detailed info for %s: %s", name, e)
                return model_basic

        except Exception as e:
            logger.error("Error getting model info for %s: %s", name, e)
            return None
