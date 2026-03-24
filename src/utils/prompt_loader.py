"""
Prompt loading utilities for GenAI agents.

This module provides functions to load system prompts from external files,
enabling prompt versioning and modification without code changes.
"""

import logging
from pathlib import Path
from typing import Dict

from ..exceptions import PromptLoadError

logger = logging.getLogger(__name__)


def load_prompt(prompt_name: str, prompts_dir: Path = Path("prompts")) -> str:
    """
    Load a system prompt from a text file.

    Args:
        prompt_name: Name of the prompt file (without .txt extension)
        prompts_dir: Directory containing prompt files

    Returns:
        The loaded prompt text as a string

    Raises:
        PromptLoadError: If the prompt file cannot be found or read

    Example:
        >>> prompt = load_prompt("clinical_analyst")
        >>> print(prompt[:50])
        'You are a Clinical Analyst Agent. Your goal is...'
    """
    prompt_path = prompts_dir / f"{prompt_name}.txt"

    try:
        logger.debug(f"Loading prompt from: {prompt_path}")

        if not prompt_path.exists():
            raise PromptLoadError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()

        if not prompt_text:
            raise PromptLoadError(f"Prompt file is empty: {prompt_path}")

        logger.debug(f"Successfully loaded prompt (length: {len(prompt_text)} chars)")
        return prompt_text

    except OSError as e:
        raise PromptLoadError(f"Failed to read prompt file {prompt_path}: {e}") from e


def load_all_prompts(prompts_dir: Path = Path("prompts")) -> Dict[str, str]:
    """
    Load all available prompts from the prompts directory.

    Args:
        prompts_dir: Directory containing prompt files

    Returns:
        Dictionary mapping prompt names to their content

    Raises:
        PromptLoadError: If the prompts directory doesn't exist

    Example:
        >>> prompts = load_all_prompts()
        >>> print(prompts.keys())
        dict_keys(['clinical_analyst', 'validator_supervisor'])
    """
    if not prompts_dir.exists():
        raise PromptLoadError(f"Prompts directory not found: {prompts_dir}")

    prompts = {}

    for prompt_file in prompts_dir.glob("*.txt"):
        prompt_name = prompt_file.stem
        prompts[prompt_name] = load_prompt(prompt_name, prompts_dir)
        logger.debug(f"Loaded prompt: {prompt_name}")

    logger.info(f"Loaded {len(prompts)} prompts from {prompts_dir}")
    return prompts
