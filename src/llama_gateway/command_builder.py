"""Command builder for generating llama-server CLI commands."""

from typing import List

from .logging_config import get_logger
from .model_registry import Model
from .settings import settings

logger = get_logger("command_builder")


def build_llama_server_command(model: Model) -> List[str]:
    """
    Build llama-server command from model configuration.

    Args:
        model: Model with configuration

    Returns:
        List of command arguments
    """
    config = model.config
    cmd = [settings.LLAMA_SERVER_BINARY]

    # Model path (required)
    cmd.extend(["-m", model.path])

    # Context length
    cmd.extend(["-c", str(config.context_length)])

    # GPU layers
    cmd.extend(["-ngl", str(config.n_gpu_layers)])

    # Batch size
    cmd.extend(["-b", str(config.batch_size)])

    # Host and port
    cmd.extend(["--host", config.host])
    cmd.extend(["--port", str(config.port)])

    # Flash attention
    if config.flash_attention:
        cmd.extend(["-fa", "1"])

    # No mmap
    if config.no_mmap:
        cmd.append("--no-mmap")

    # Parallel sequences (slots)
    cmd.extend(["-np", str(config.parallel)])

    # Timeout
    cmd.extend(["-to", str(config.timeout)])

    # Additional arguments
    if config.additional_args:
        cmd.extend(config.additional_args)

    logger.debug(f"Built command: {' '.join(cmd)}")
    return cmd


def command_to_string(cmd: List[str]) -> str:
    """
    Convert command list to string for logging.

    Args:
        cmd: Command arguments

    Returns:
        Command string
    """
    return " ".join(cmd)
