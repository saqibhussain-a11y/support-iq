import json
from collections.abc import AsyncIterator

import groq
from opentelemetry.trace import Status, StatusCode

from app.llm.exceptions import LLMError
from app.llm.provider import ModelProvider
from app.llm.schemas import ChatMessage, LLMResponse, TokenUsage, ToolCall
from app.observability.tracing import get_tracer


def _to_api_message(message: ChatMessage) -> dict:
    payload: dict = {"role": message.role, "content": message.content}
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {"name": tool_call.name, "arguments": json.dumps(tool_call.arguments)},
            }
            for tool_call in message.tool_calls
        ]
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    return payload


class GroqProvider(ModelProvider):
    def __init__(
        self,
        api_key: str | None,
        model: str,
        max_retries: int = 2,
        timeout: float = 30.0,
    ) -> None:
        self._model = model
        self._client = groq.AsyncGroq(
            api_key=api_key,
            max_retries=max_retries,
            timeout=timeout,
        )

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
        json_mode: bool = False,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self._model,
            "messages": [_to_api_message(m) for m in messages],
            "temperature": temperature,
            "top_p": top_p,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        with get_tracer().start_as_current_span("groq.chat.completions") as span:
            span.set_attribute("llm.model", self._model)
            span.set_attribute("llm.temperature", temperature)
            span.set_attribute("llm.json_mode", json_mode)
            span.set_attribute("llm.tools_enabled", bool(tools))
            try:
                response = await self._client.chat.completions.create(**kwargs)
            except groq.GroqError as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise LLMError(str(exc)) from exc

            choice = response.choices[0]
            usage = response.usage
            span.set_attribute("llm.finish_reason", choice.finish_reason)
            if usage:
                span.set_attribute("llm.usage.prompt_tokens", usage.prompt_tokens)
                span.set_attribute("llm.usage.completion_tokens", usage.completion_tokens)
                span.set_attribute("llm.usage.total_tokens", usage.total_tokens)

            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments or "{}"),
                    )
                    for tool_call in choice.message.tool_calls
                ]
                span.set_attribute("llm.tool_call_count", len(tool_calls))

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
            tool_calls=tool_calls,
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> AsyncIterator[str]:
        try:
            response_stream = await self._client.chat.completions.create(
                model=self._model,
                messages=[m.model_dump() for m in messages],
                temperature=temperature,
                top_p=top_p,
                stream=True,
            )
            async for chunk in response_stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except groq.GroqError as exc:
            raise LLMError(str(exc)) from exc
