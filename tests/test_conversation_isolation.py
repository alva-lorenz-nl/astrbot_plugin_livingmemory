"""对话线（conversation_id）隔离的测试：过滤、补偿取样与检索缓存。"""

from pathlib import Path

import pytest

from astrbot_plugin_livingmemory.core.managers.memory_engine import MemoryEngine
from astrbot_plugin_livingmemory.core.memory_scope import conversation_visible
from tests.test_memory_engine import _FakeFaissDB

SESSION = "test:GroupMessage:1001"
KEYWORD = "黑麦面包配方"


async def _make_engine(tmp_path: Path, name: str = "cid.db") -> MemoryEngine:
    engine = MemoryEngine(
        db_path=str(tmp_path / name),
        faiss_db=_FakeFaissDB(),
        config={
            "fallback_enabled": True,
            "rrf_k": 60,
            "recent_memory_count": 0,
            "min_similarity_for_retrieval": 0.0,
            "min_importance_for_retrieval": 0.0,
        },
    )
    await engine.initialize()
    return engine


class TestConversationVisible:
    def test_no_current_cid_means_no_filtering(self):
        assert conversation_visible({"conversation_id": "a"}, None) is True

    def test_matching_cid_visible(self):
        assert conversation_visible({"conversation_id": "a"}, "a") is True

    def test_other_cid_hidden(self):
        assert conversation_visible({"conversation_id": "b"}, "a") is False

    def test_legacy_memory_follows_fallback_flag(self):
        assert conversation_visible({}, "a", fallback_to_global=True) is True
        assert conversation_visible({}, "a", fallback_to_global=False) is False


class TestSearchMemoriesConversationFilter:
    @pytest.mark.asyncio
    async def test_only_current_conversation_returned(self, tmp_path):
        engine = await _make_engine(tmp_path)
        await engine.add_memory(
            content=f"{KEYWORD} 甲 用全麦粉",
            session_id=SESSION,
            metadata={"conversation_id": "cid_a"},
        )
        await engine.add_memory(
            content=f"{KEYWORD} 乙 用黑麦粉",
            session_id=SESSION,
            metadata={"conversation_id": "cid_b"},
        )

        results = await engine.search_memories(
            KEYWORD, k=2, session_id=SESSION, conversation_id="cid_a"
        )

        assert results
        assert all(
            (r.metadata or {}).get("conversation_id") == "cid_a" for r in results
        )

    @pytest.mark.asyncio
    async def test_over_sampling_keeps_k_after_filtering(self, tmp_path):
        engine = await _make_engine(tmp_path)
        for i in range(2):
            await engine.add_memory(
                content=f"{KEYWORD} 干扰项 {i}",
                session_id=SESSION,
                metadata={"conversation_id": "cid_other"},
            )
        await engine.add_memory(
            content=f"{KEYWORD} 目标项 低盐",
            session_id=SESSION,
            metadata={"conversation_id": "cid_a"},
        )

        results = await engine.search_memories(
            KEYWORD, k=1, session_id=SESSION, conversation_id="cid_a"
        )

        assert len(results) == 1
        assert (results[0].metadata or {}).get("conversation_id") == "cid_a"

    @pytest.mark.asyncio
    async def test_fallback_flag_controls_legacy_memories(self, tmp_path):
        engine = await _make_engine(tmp_path)
        await engine.add_memory(content=f"{KEYWORD} 老记忆", session_id=SESSION)

        with_fallback = await engine.search_memories(
            KEYWORD, k=2, session_id=SESSION, conversation_id="cid_a"
        )
        assert with_fallback

        without_fallback = await engine.search_memories(
            KEYWORD,
            k=2,
            session_id=SESSION,
            conversation_id="cid_a",
            fallback_to_global_conversations=False,
        )
        assert without_fallback == []

    @pytest.mark.asyncio
    async def test_cache_does_not_leak_between_conversations(self, tmp_path):
        engine = await _make_engine(tmp_path)
        await engine.add_memory(
            content=f"{KEYWORD} 甲",
            session_id=SESSION,
            metadata={"conversation_id": "cid_a"},
        )
        await engine.add_memory(
            content=f"{KEYWORD} 乙",
            session_id=SESSION,
            metadata={"conversation_id": "cid_b"},
        )

        first = await engine.search_memories(
            KEYWORD, k=2, session_id=SESSION, conversation_id="cid_a"
        )
        second = await engine.search_memories(
            KEYWORD, k=2, session_id=SESSION, conversation_id="cid_b"
        )

        assert {r.doc_id for r in first}.isdisjoint({r.doc_id for r in second})
        assert all((r.metadata or {}).get("conversation_id") == "cid_b" for r in second)
