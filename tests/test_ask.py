import importlib
import sys
from types import SimpleNamespace
from unittest.mock import Mock


def test_main_keeps_chat_for_follow_up_questions(monkeypatch, capsys):
    ask_module = importlib.import_module("app.ask")
    chat = Mock()
    chat.send_message.side_effect = [
        SimpleNamespace(text="first answer", usage_metadata=None),
        SimpleNamespace(text="follow-up answer", usage_metadata=None),
    ]
    responses = iter(chat.send_message.side_effect)
    client = SimpleNamespace(
        chats=SimpleNamespace(create=Mock(return_value=chat)),
        close=Mock(),
    )

    def send_message(question):
        assert not client.close.called
        return next(responses)

    chat.send_message.side_effect = send_message

    monkeypatch.setattr(ask_module.genai, "Client", lambda api_key: client)
    monkeypatch.setattr(ask_module, "get_api_key", lambda: "test-key")
    monkeypatch.setattr(sys, "argv", ["app.ask"])
    questions = iter(["first question", "follow-up question", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(questions))

    ask_module.main()

    assert [call.args[0] for call in chat.send_message.call_args_list] == [
        "first question",
        "follow-up question",
    ]
    client.close.assert_called_once()
    output = capsys.readouterr().out
    assert "first answer" in output
    assert "follow-up answer" in output
