"""Sampler: sends one request to a model API and records what came back.

This is the "Sampler" part of the harness from the Week 2 slide "Putting it
together: your harness". It is the code version of the slides "The same
request, two ways", "What you send", and "What comes back".

What is sent, for every request:
    model              the exact model name from conditions.json
    the prompt         the task description, wrapped in the fixed template
    temperature        how much randomness is allowed when picking tokens
    top_p              left unset in this assignment
    reasoning effort   "none", so the model answers without a hidden
                       reasoning step
    max output tokens  the longest answer we are willing to pay for

What is kept from the reply (the Generation class below):
    text           the answer itself, the part a chat website shows you
    returned_model the version string the provider says actually answered
    token counts   the usage you are billed for
    stop_reason    why the answer ended: finished, or cut off at the limit

The runner (harness/runner.py) creates one provider object per model
condition and calls its generate method once per attempt.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class Condition:
    """One model condition, read from an entry in conditions.json.

    id                 "A" or "B"
    provider           "openai" or "anthropic"
    model              the model name to request
    temperature        randomness setting sent with every request
    top_p              optional cutoff for unlikely tokens (null here)
    seed               optional repeatability number (null here)
    effort             reasoning effort setting ("none" here)
    max_output_tokens  length cap for each answer
    """

    id: str
    provider: str
    model: str
    temperature: float | None
    top_p: float | None
    seed: int | None
    effort: str | None
    max_output_tokens: int

    def sampling_signature(self) -> tuple[object, ...]:
        """Return every sampling setting as one tuple.

        The runner requires this tuple to be identical for both conditions.
        That is what makes the comparison controlled: the model is the only
        thing that differs between A and B.
        """
        return (
            self.temperature,
            self.top_p,
            self.seed,
            self.effort,
            self.max_output_tokens,
        )


@dataclass(frozen=True)
class Generation:
    """What came back from one request.

    text            the answer text
    provider        which API produced it
    requested_model the model name the harness asked for
    returned_model  the version string the API reported, which can be more
                    specific than the name requested
    input_tokens    prompt size in tokens, if reported
    output_tokens   answer size in tokens, if reported
    total_tokens    the two added together, if reported
    stop_reason     why the answer ended, if reported. "completed" or
                    "end_turn" means it finished. "max_output_tokens" or
                    "max_tokens" means it was cut off at the length cap.
    """

    text: str
    provider: str
    requested_model: str
    returned_model: str | None
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    stop_reason: str | None = None


class BaseProvider:
    """The interface every provider follows.

    The runner only calls generate, so it does not need to know which
    company's API is behind it.
    """

    def generate(self, prompt: str, condition: Condition) -> Generation:
        raise NotImplementedError


class OpenAIProvider(BaseProvider):
    """Sends requests to the OpenAI Responses API. Used by the default conditions.json."""

    def __init__(self) -> None:
        # The openai package is imported here rather than at the top of the
        # file, so commands that never call the API, such as --plan and the
        # tests, never load it.
        from openai import OpenAI

        # The key is read from an environment variable and never from a file,
        # so it cannot end up in your repository by accident.
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, condition: Condition) -> Generation:
        """Send one prompt and return the answer with its metadata."""
        kwargs: dict[str, Any] = {
            "model": condition.model,
            "input": prompt,
            "max_output_tokens": condition.max_output_tokens,
            # Do not save this response on OpenAI's side for later retrieval.
            "store": False,
        }
        # Only settings that are actually set are sent. A setting left out
        # uses the provider's default, which is why the run record stores
        # null for it rather than a guessed value.
        if condition.temperature is not None:
            kwargs["temperature"] = condition.temperature
        if condition.top_p is not None:
            kwargs["top_p"] = condition.top_p
        if condition.effort is not None:
            # GPT-5.6 models accept a temperature only when reasoning effort
            # is "none", which is the setting in conditions.json.
            kwargs["reasoning"] = {"effort": condition.effort}
        if condition.seed is not None:
            # Refuse rather than silently drop the seed. A run record that
            # lists a seed which was never sent would be false.
            raise ValueError("The supplied OpenAI Responses adapter does not use a seed parameter.")

        response = self.client.responses.create(**kwargs)

        usage = getattr(response, "usage", None)
        # A finished answer has status "completed". An answer that was cut
        # short has status "incomplete", and incomplete_details.reason says
        # why, for example "max_output_tokens".
        status = getattr(response, "status", None)
        details = getattr(response, "incomplete_details", None)
        reason = getattr(details, "reason", None) if details else None
        return Generation(
            text=response.output_text,
            provider="openai",
            requested_model=condition.model,
            returned_model=getattr(response, "model", None),
            input_tokens=getattr(usage, "input_tokens", None) if usage else None,
            output_tokens=getattr(usage, "output_tokens", None) if usage else None,
            total_tokens=getattr(usage, "total_tokens", None) if usage else None,
            stop_reason=reason or status,
        )


class AnthropicProvider(BaseProvider):
    """Sends requests to the Anthropic Messages API.

    Used only if the instructor distributes a class-wide Anthropic version of
    conditions.json.
    """

    def __init__(self) -> None:
        from anthropic import Anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, condition: Condition) -> Generation:
        """Send one prompt and return the answer with its metadata."""
        if condition.seed is not None:
            raise ValueError("The supplied Anthropic adapter does not use a seed parameter.")
        # This adapter never turns on extended thinking, so the only effort
        # values it accepts are "none" or unset.
        if condition.effort not in (None, "none"):
            raise ValueError(
                "This harness supports Anthropic only with thinking disabled. "
                "Use an instructor-supplied class-wide configuration."
            )
        kwargs: dict[str, Any] = {
            "model": condition.model,
            "max_tokens": condition.max_output_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if condition.temperature is not None:
            kwargs["temperature"] = condition.temperature
        if condition.top_p is not None:
            kwargs["top_p"] = condition.top_p

        response = self.client.messages.create(**kwargs)

        # The reply is a list of content blocks. Only the text blocks form
        # the answer.
        text = "".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        )
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None) if usage else None
        output_tokens = getattr(usage, "output_tokens", None) if usage else None
        # Anthropic does not report a total, so it is added up here, but only
        # when both parts are known.
        total_tokens = (
            input_tokens + output_tokens
            if isinstance(input_tokens, int) and isinstance(output_tokens, int)
            else None
        )
        return Generation(
            text=text,
            provider="anthropic",
            requested_model=condition.model,
            returned_model=getattr(response, "model", None),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            stop_reason=getattr(response, "stop_reason", None),
        )


def provider_for(name: str) -> BaseProvider:
    """Return a ready-to-use provider for the name given in conditions.json."""
    if name == "openai":
        return OpenAIProvider()
    if name == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unsupported provider: {name}")
