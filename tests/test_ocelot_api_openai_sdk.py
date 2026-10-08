"""Optional interoperability check against the official OpenAI Python SDK."""
from __future__ import annotations

import threading

import pytest

openai = pytest.importorskip("openai")

from scripts.ocelot_api import build_default_baseline, make_server
from domains.cow_sessions import CowSessionManager


def test_openai_python_client_base_url_chat_completion(tmp_path):
    server = make_server("127.0.0.1", 0, build_default_baseline(),
                         {"sdk-secret": "sdk-principal"},
                         storage_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        session_id = server.manager.ensure_default_session("sdk-principal")
        client = openai.OpenAI(
            base_url=f"http://127.0.0.1:{server.server_port}/v1",
            api_key="sdk-secret")
        models = client.models.list()
        assert [model.id for model in models.data] == ["ocelot"]
        response = client.chat.completions.create(
            model="ocelot",
            messages=[{"role": "user", "content": "hello"}],
            extra_headers={"Ocelot-Session-ID": session_id},
        )
        assert response.model == "ocelot"
        assert response.choices[0].message.role == "assistant"
        assert response.choices[0].message.content
        assert response.usage.total_tokens == 0
        with pytest.raises(openai.APIStatusError) as rejected:
            client.chat.completions.create(
                model="ocelot", stream=True,
                messages=[{"role": "user", "content": "stream?"}],
            )
        assert rejected.value.status_code == 501
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    resumed = CowSessionManager(build_default_baseline(), storage_dir=tmp_path)
    sessions = resumed.list_sessions("sdk-principal")
    assert sessions[0]["id"] == session_id
    assert sessions[0]["revision"] >= 2
    session = resumed.get_session("sdk-principal", session_id)
    assert any(turn["text"] == "hello" for turn in session.adapter.chat_transcript())
