"""Tests for context and memory overhaul behavior."""

import inspect
import json
import os
import sys
from unittest.mock import MagicMock

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)


def test_progress_limit_50_in_context():
    from ouroboros.context import build_recent_sections
    source = inspect.getsource(build_recent_sections)
    assert "limit=50" in source


def test_recent_chat_limit_1000_in_context():
    from ouroboros.context import build_recent_sections
    source = inspect.getsource(build_recent_sections)
    assert 'read_jsonl_tail("chat.jsonl", 1000)' in source


def test_no_taskid_filter_in_recent_sections():
    from ouroboros.context import build_recent_sections
    source = inspect.getsource(build_recent_sections)
    assert 'if task_id:' not in source


def test_should_consolidate_chat_blocks_alias(tmp_path):
    from ouroboros.consolidator import should_consolidate_chat_blocks, BLOCK_SIZE
    chat_path = tmp_path / 'chat.jsonl'
    meta_path = tmp_path / 'dialogue_meta.json'
    entries = [json.dumps({"ts": f"2026-03-09T10:{i % 60:02d}:00Z", "direction": "in", "text": "msg"}) for i in range(BLOCK_SIZE + 5)]
    chat_path.write_text("\n".join(entries) + "\n", encoding='utf-8')
    assert should_consolidate_chat_blocks(meta_path, chat_path) is True


def test_consolidate_chat_alias_creates_block(tmp_path):
    from ouroboros.consolidator import consolidate_chat_blocks, _load_meta, _load_blocks, BLOCK_SIZE
    chat_path = tmp_path / 'chat.jsonl'
    blocks_path = tmp_path / 'dialogue_blocks.json'
    meta_path = tmp_path / 'dialogue_meta.json'
    entries = [json.dumps({"ts": f"2026-03-09T10:{i % 60:02d}:00Z", "direction": "in", "text": f"msg {i}"}) for i in range(BLOCK_SIZE + 5)]
    chat_path.write_text("\n".join(entries) + "\n", encoding='utf-8')
    mock_llm = MagicMock()
    mock_llm.chat.return_value = ({"content": "### Block: test\n\nSummary."}, {"prompt_tokens": 100, "completion_tokens": 50, "cost": 0.001})
    usage = consolidate_chat_blocks(chat_path, blocks_path, meta_path, mock_llm)
    assert usage is not None
    meta = _load_meta(meta_path)
    assert meta["last_consolidated_offset"] == BLOCK_SIZE
    blocks = _load_blocks(blocks_path)
    assert len(blocks) == 1


def test_no_identity_truncation_in_consolidator_prompts():
    from ouroboros.consolidator import _create_block_summary, consolidate_scratchpad_blocks
    assert 'identity_text[:' not in inspect.getsource(_create_block_summary)
    assert 'identity_text[:' not in inspect.getsource(consolidate_scratchpad_blocks)
