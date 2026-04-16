"""
LLM backend factory and command-based client implementations.
"""
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, Union, runtime_checkable

from ollama_client import OllamaClient

logger = logging.getLogger(__name__)

PROMPT_PLACEHOLDER = "{prompt}"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Common interface expected by the simulation."""

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response for the given prompt."""

    def check_connection(self) -> bool:
        """Return whether the backend is reachable or runnable."""

    def check_model_exists(self) -> bool:
        """Return whether the configured model exists."""

    def list_models(self) -> List[str]:
        """List available models when supported."""


class CommandLLMClient:
    """Run an external CLI as the LLM backend."""

    def __init__(
        self,
        command: Union[Sequence[str], str],
        response_format: str = "text",
        response_json_field: Optional[str] = None,
        timeout_seconds: int = 180,
        prompt_mode: str = "auto",
        env: Optional[Dict[str, str]] = None,
        working_directory: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.command = self._normalize_command(command)
        self.response_format = response_format
        self.response_json_field = response_json_field
        self.timeout_seconds = timeout_seconds
        self.prompt_mode = prompt_mode
        self.env = env or {}
        self.working_directory = working_directory
        self.model = model

    def _normalize_command(self, command: Union[Sequence[str], str]) -> List[str]:
        """Normalize the configured command into an argv list."""
        if isinstance(command, str):
            return shlex.split(command)
        return [str(part) for part in command]

    def _build_invocation(self, prompt: str) -> Tuple[List[str], Optional[str]]:
        """Build the command argv and optional stdin input."""
        if not self.command:
            raise ValueError("CLI backend requires a non-empty 'llm.command' setting.")

        has_placeholder = any(PROMPT_PLACEHOLDER in part for part in self.command)

        if self.prompt_mode not in {"auto", "stdin", "append_arg"}:
            raise ValueError(
                "llm.prompt_mode must be one of: auto, stdin, append_arg"
            )

        if has_placeholder:
            argv = [part.replace(PROMPT_PLACEHOLDER, prompt) for part in self.command]
            return argv, None

        if self.prompt_mode == "stdin":
            return list(self.command), prompt

        return [*self.command, prompt], None

    def _extract_json_field(self, payload: Any) -> str:
        """Extract a nested field from a parsed JSON payload."""
        if self.response_json_field:
            current = payload
            for part in self.response_json_field.split("."):
                if not isinstance(current, dict) or part not in current:
                    raise KeyError(
                        f"response_json_field '{self.response_json_field}' not found"
                    )
                current = current[part]
            if isinstance(current, str):
                return current.strip()
            return json.dumps(current, ensure_ascii=False)

        for key in ("result", "output_text", "text", "content"):
            if isinstance(payload, dict) and isinstance(payload.get(key), str):
                return payload[key].strip()

        if isinstance(payload, str):
            return payload.strip()

        return json.dumps(payload, ensure_ascii=False)

    def _clean_output(self, text: str) -> str:
        """Remove ANSI escapes and surrounding whitespace from CLI output."""
        return ANSI_ESCAPE_RE.sub("", text).strip()

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text by spawning the configured command."""
        del temperature
        del max_tokens

        try:
            argv, stdin_input = self._build_invocation(prompt)
            run_env = os.environ.copy()
            run_env.update(self.env)
            completed = subprocess.run(
                argv,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=self.working_directory,
                env=run_env,
                check=False,
            )
        except FileNotFoundError:
            logger.error("Configured CLI backend executable was not found: %s", self.command[0])
            return ""
        except subprocess.TimeoutExpired:
            logger.error(
                "CLI backend timed out after %s seconds: %s",
                self.timeout_seconds,
                " ".join(self.command),
            )
            return ""
        except Exception as e:
            logger.error("Unexpected error while running CLI backend: %s", e)
            return ""

        stdout = self._clean_output(completed.stdout)
        stderr = self._clean_output(completed.stderr)

        if completed.returncode != 0:
            logger.error(
                "CLI backend exited with code %s: %s",
                completed.returncode,
                stderr or stdout or "(no output)",
            )
            return ""

        if not stdout:
            logger.warning("CLI backend returned no stdout output.")
            return ""

        if self.response_format == "json":
            try:
                payload = json.loads(stdout)
                return self._extract_json_field(payload)
            except Exception as e:
                logger.error("Failed to parse JSON from CLI backend output: %s", e)
                return ""

        return stdout

    def check_connection(self) -> bool:
        """Check whether the configured executable is available."""
        executable = self.command[0] if self.command else ""
        return bool(executable) and shutil.which(executable) is not None

    def check_model_exists(self) -> bool:
        """Command-backed clients cannot usually validate model availability upfront."""
        return True

    def list_models(self) -> List[str]:
        """Return the configured model when one was supplied."""
        return [self.model] if self.model else []


def create_llm_client(llm_config: Dict[str, Any]) -> LLMClientProtocol:
    """Create an LLM client from config."""
    provider = llm_config.get("provider", "ollama").lower()

    if provider == "ollama":
        return OllamaClient(
            base_url=llm_config["base_url"],
            model=llm_config["model"],
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 200),
            repeat_penalty=llm_config.get("repeat_penalty", 1.1),
            repeat_last_n=llm_config.get("repeat_last_n", 128),
            min_p=llm_config.get("min_p", 0.05),
        )

    if provider in {"command", "cli"}:
        env = {
            str(key): str(value)
            for key, value in llm_config.get("env", {}).items()
        }
        return CommandLLMClient(
            command=llm_config["command"],
            response_format=llm_config.get("response_format", "text"),
            response_json_field=llm_config.get("response_json_field"),
            timeout_seconds=int(llm_config.get("timeout_seconds", 180)),
            prompt_mode=llm_config.get("prompt_mode", "auto"),
            env=env,
            working_directory=llm_config.get("working_directory"),
            model=llm_config.get("model"),
        )

    raise ValueError(f"Unsupported llm.provider: '{provider}'")
