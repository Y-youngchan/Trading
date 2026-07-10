from datetime import UTC, datetime, timedelta

from backend.services.chatbot.conversation_repository import ChatbotConversationRepository


class FakeConversationStateBoundary:
    def __init__(self, insert_conflict_once: bool = False):
        self.rows = {}
        self.insert_conflict_once = insert_conflict_once

    def query(self, auth_header, endpoint, method="GET", json_data=None, params=None):
        assert endpoint == "chatbot_conversation_states"
        params = params or {}
        user_id = str(params.get("user_id") or "").removeprefix("eq.")

        if method == "GET":
            row = self.rows.get(user_id)
            return [dict(row)] if row else []
        if method == "POST":
            payload = dict(json_data or {})
            user_id = str(payload.get("user_id") or "")
            if self.insert_conflict_once:
                self.insert_conflict_once = False
                self.rows[user_id] = {"user_id": user_id}
                raise RuntimeError("duplicate key value violates unique constraint")
            self.rows[user_id] = payload
            return [dict(payload)]
        if method == "PATCH":
            self.rows.setdefault(user_id, {"user_id": user_id}).update(json_data or {})
            return [dict(self.rows[user_id])]
        raise AssertionError(f"지원하지 않는 메서드: {method}")


def test_load_recent_history_reads_supabase_on_every_request(monkeypatch):
    calls = []

    def fake_query(auth_header, endpoint, method="GET", json_data=None, params=None):
        calls.append((endpoint, method, params))
        return [
            {"id": 2, "role": "assistant", "message": "두 번째", "created_at": "2026-07-10T01:00:02Z"},
            {"id": 1, "role": "user", "message": "첫 번째", "created_at": "2026-07-10T01:00:01Z"},
        ]

    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        fake_query,
    )
    repository = ChatbotConversationRepository()

    first = repository.load_recent_history("Bearer test", "user-1")
    second = repository.load_recent_history("Bearer test", "user-1")

    assert first == [
        {"role": "user", "content": "첫 번째"},
        {"role": "assistant", "content": "두 번째"},
    ]
    assert second == first
    assert len(calls) == 2


def test_expired_recommendations_are_not_reused(monkeypatch):
    expired_at = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        lambda *args, **kwargs: [{
            "user_id": "user-1",
            "recommendation_items": [{"symbol": "DOGE"}],
            "recommendation_expires_at": expired_at,
        }],
    )

    result = ChatbotConversationRepository().load_recommendations(
        "Bearer test",
        "user-1",
        now=datetime.now(UTC),
    )

    assert result == []


def test_recorded_exchange_is_visible_to_another_repository_instance(monkeypatch):
    rows = []

    def fake_query(auth_header, endpoint, method="GET", json_data=None, params=None):
        assert endpoint == "chat_history"
        if method == "POST":
            for row in json_data:
                rows.append({
                    **row,
                    "id": len(rows) + 1,
                    "created_at": f"2026-07-10T01:00:0{len(rows) + 1}Z",
                })
            return list(rows)
        return list(reversed(rows))

    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        fake_query,
    )

    ChatbotConversationRepository().record_exchange(
        "Bearer test",
        "user-1",
        " 첫 질문 ",
        " 첫 답변 ",
    )
    history = ChatbotConversationRepository().load_recent_history(
        "Bearer test",
        "user-1",
    )

    assert history == [
        {"role": "user", "content": "첫 질문"},
        {"role": "assistant", "content": "첫 답변"},
    ]


def test_pending_action_is_consumed_across_repository_instances(monkeypatch):
    boundary = FakeConversationStateBoundary()
    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        boundary.query,
    )
    writer = ChatbotConversationRepository()
    reader = ChatbotConversationRepository()

    writer.set_pending_action(
        "Bearer test",
        "user-1",
        "portfolio_summary",
        {"exchange": "TOSS"},
    )

    assert reader.peek_pending_action("Bearer test", "user-1") == "portfolio_summary"
    assert reader.consume_pending_action("Bearer test", "user-1") == (
        "portfolio_summary",
        {"exchange": "TOSS"},
    )
    assert writer.peek_pending_action("Bearer test", "user-1") is None


def test_expired_pending_action_is_not_consumed(monkeypatch):
    expired_at = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    boundary = FakeConversationStateBoundary()
    boundary.rows["user-1"] = {
        "user_id": "user-1",
        "pending_action": "portfolio_summary",
        "pending_payload": {"exchange": "TOSS"},
        "pending_expires_at": expired_at,
    }
    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        boundary.query,
    )
    repository = ChatbotConversationRepository()

    assert repository.peek_pending_action("Bearer test", "user-1") is None
    assert repository.consume_pending_action("Bearer test", "user-1") == (None, {})


def test_state_insert_race_recovers_by_patching_existing_row(monkeypatch):
    boundary = FakeConversationStateBoundary(insert_conflict_once=True)
    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        boundary.query,
    )
    repository = ChatbotConversationRepository()

    repository.set_pending_action(
        "Bearer test",
        "user-1",
        "portfolio_summary",
    )

    assert repository.peek_pending_action("Bearer test", "user-1") == "portfolio_summary"


def test_recommendations_are_shared_across_repository_instances(monkeypatch):
    boundary = FakeConversationStateBoundary()
    monkeypatch.setattr(
        "backend.services.chatbot.conversation_repository.query_supabase",
        boundary.query,
    )
    items = [{"symbol": "005930"}, {"symbol": "000660"}]

    ChatbotConversationRepository().store_recommendations(
        "Bearer test",
        "user-1",
        items,
        "ML_ACTIVE_SIGNAL",
    )
    loaded = ChatbotConversationRepository().load_recommendations(
        "Bearer test",
        "user-1",
    )

    assert loaded == items
