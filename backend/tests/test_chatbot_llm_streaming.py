import json

from backend.services.chatbot.llm_client import ChatbotLLMClient


class FakeStreamResponse:
    status_code = 200

    def iter_lines(self, decode_unicode=True):
        chunks = [
            {"choices": [{"delta": {"content": "첫 "}, "finish_reason": None}], "usage": None},
            {"choices": [{"delta": {"content": "답변"}, "finish_reason": "stop"}], "usage": None},
            {"choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}},
        ]
        for chunk in chunks:
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}"
        yield "data: [DONE]"


def test_stream_reply_emits_openai_text_deltas(monkeypatch):
    client = ChatbotLLMClient()
    client.api_key = "test"
    monkeypatch.setattr(client, "_consume_shared_usage", lambda *args: None)
    monkeypatch.setattr(
        "backend.services.chatbot.llm_client.requests.post",
        lambda *args, **kwargs: FakeStreamResponse(),
    )
    deltas = []

    result = client.stream_reply(
        system_prompt="system",
        user_message="질문",
        user_id="user-1",
        auth_header="Bearer test",
        function_schemas=[],
        history=[],
        on_delta=deltas.append,
    )

    assert deltas == ["첫 ", "답변"]
    assert result["reply"] == "첫 답변"
    assert result["usage"]["total_tokens"] == 12


def test_stream_reply_accumulates_tool_call_argument_deltas(monkeypatch):
    class FakeToolStreamResponse:
        status_code = 200

        def iter_lines(self, decode_unicode=True):
            chunks = [
                {"choices": [{"delta": {"tool_calls": [{
                    "index": 0,
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "get_portfolio_summary", "arguments": "{\"broker_"},
                }]}, "finish_reason": None}]},
                {"choices": [{"delta": {"tool_calls": [{
                    "index": 0,
                    "function": {"arguments": "env\":\"REAL\"}"},
                }]}, "finish_reason": "tool_calls"}]},
            ]
            for chunk in chunks:
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}"
            yield "data: [DONE]"

    client = ChatbotLLMClient()
    client.api_key = "test"
    monkeypatch.setattr(client, "_consume_shared_usage", lambda *args: None)
    monkeypatch.setattr(
        "backend.services.chatbot.llm_client.requests.post",
        lambda *args, **kwargs: FakeToolStreamResponse(),
    )

    result = client.stream_reply(
        system_prompt="system",
        user_message="자산 알려줘",
        user_id="user-1",
        auth_header="Bearer test",
        function_schemas=[],
        history=[],
        on_delta=lambda text: None,
    )

    assert result["tool_calls"] == [{
        "id": "call-1",
        "type": "function",
        "function": {
            "name": "get_portfolio_summary",
            "arguments": "{\"broker_env\":\"REAL\"}",
        },
    }]
