"""HybridMemoryAgent — combines episodic vector memory with stable user profile features."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from rank_bm25 import BM25Okapi

from app.embeddings import Embedder

REPO_ROOT = Path(__file__).resolve().parent.parent
FEAST_DIR = REPO_ROOT / "app" / "feast_repo"


class HybridMemoryAgent:
    """Agent that integrates episodic memory (Vector Store) and stable user profile (Feature Store)."""

    def __init__(self, collection_name: str = "episodic_memory"):
        self.collection_name = collection_name
        self.embedder = Embedder()
        self.client = QdrantClient(":memory:")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.embedder.dim, distance=Distance.COSINE),
        )

        # Local episodic memory text store for BM25 and ID mapping
        self.memories: list[dict[str, Any]] = []
        self._point_id = 0

        # Initialize Feast feature store if available
        self.fs = None
        if (FEAST_DIR / "registry.db").exists():
            try:
                from feast import FeatureStore
                self.fs = FeatureStore(repo_path=str(FEAST_DIR))
            except Exception:
                self.fs = None

    def remember(self, text: str, user_id: str = "u_001", metadata: dict | None = None) -> None:
        """Add a new piece of episodic memory for a specific user."""
        if not text.strip():
            return

        meta = metadata or {}
        # Embed chunk
        vec = next(self.embedder.embed([text])).tolist()

        point_id = self._point_id
        self._point_id += 1

        mem_entry = {
            "id": point_id,
            "user_id": user_id,
            "text": text,
            **meta
        }
        self.memories.append(mem_entry)

        # Upsert point to Qdrant with user_id filter payload
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={"user_id": user_id, "text": text, **meta}
                )
            ]
        )

    def _get_user_features(self, user_id: str) -> dict[str, Any]:
        """Fetch user profile and recent query velocity from Feast online store."""
        defaults = {
            "reading_speed_wpm": 220,
            "preferred_language": "vi",
            "topic_affinity": "cloud",
            "queries_last_hour": 12,
            "distinct_topics_24h": 4,
        }
        if self.fs is None:
            return defaults

        try:
            feats = self.fs.get_online_features(
                features=[
                    "user_profile_features:reading_speed_wpm",
                    "user_profile_features:preferred_language",
                    "user_profile_features:topic_affinity",
                    "query_velocity_features:queries_last_hour",
                    "query_velocity_features:distinct_topics_24h",
                ],
                entity_rows=[{"user_id": user_id}],
            ).to_dict()

            res = {}
            for k, v in feats.items():
                short_k = k.split(":")[-1]
                val = v[0] if (v and v[0] is not None) else defaults.get(short_k)
                res[short_k] = val
            return res
        except Exception:
            return defaults

    def recall(self, query: str, user_id: str = "u_001", top_k: int = 3, rrf_k: int = 60) -> str:
        """Retrieve top-K memories + user profile features -> return assembled context."""
        # 1. Fetch features from Feast
        profile = self._get_user_features(user_id)

        # 2. Hybrid search on episodic memory filtered by user_id
        user_mems = [m for m in self.memories if m["user_id"] == user_id]
        top_memories: list[str] = []

        if user_mems:
            # Semantic search
            q_vec = next(self.embedder.embed([query])).tolist()
            user_filter = Filter(must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))])
            sem_res = self.client.query_points(
                collection_name=self.collection_name,
                query=q_vec,
                query_filter=user_filter,
                limit=max(top_k * 3, 10),
            ).points
            sem_ids = [p.id for p in sem_res]

            # BM25 search
            tokenized_corpus = [m["text"].lower().split() for m in user_mems]
            bm25 = BM25Okapi(tokenized_corpus)
            bm25_scores = bm25.get_scores(query.lower().split())
            ranked_idx = sorted(range(len(bm25_scores)), key=lambda i: -bm25_scores[i])[:max(top_k * 3, 10)]
            kw_ids = [user_mems[i]["id"] for i in ranked_idx]

            # RRF Fusion
            rrf_scores: dict[int, float] = {}
            for rank, mid in enumerate(kw_ids, start=1):
                rrf_scores[mid] = rrf_scores.get(mid, 0.0) + 1.0 / (rrf_k + rank)
            for rank, mid in enumerate(sem_ids, start=1):
                rrf_scores[mid] = rrf_scores.get(mid, 0.0) + 1.0 / (rrf_k + rank)

            top_ranked_ids = sorted(rrf_scores.keys(), key=lambda mid: -rrf_scores[mid])[:top_k]
            mem_lookup = {m["id"]: m["text"] for m in user_mems}
            top_memories = [mem_lookup[mid] for mid in top_ranked_ids if mid in mem_lookup]

        # 3. Assemble context
        mem_str = "\n".join(f"  [{i+1}] {m}" for i, m in enumerate(top_memories)) if top_memories else "  (Không tìm thấy ký ức liên quan)"

        assembled_context = (
            f"=== NGỮ CẢNH NGƯỜI DÙNG (FEAST ONLINE FEATURE STORE) ===\n"
            f"- Mã người dùng (User ID)    : {user_id}\n"
            f"- Ngôn ngữ ưu tiên           : {profile.get('preferred_language', 'vi')}\n"
            f"- Sở thích chủ đề (Affinity) : {profile.get('topic_affinity', 'cloud')}\n"
            f"- Tốc độ đọc ước tính        : {profile.get('reading_speed_wpm', 220)} wpm\n"
            f"- Tần suất hoạt động 1h qua  : {profile.get('queries_last_hour', 12)} truy vấn / {profile.get('distinct_topics_24h', 4)} chủ đề\n\n"
            f"=== KÝ ỨC NGẮN/DÀI HẠN PHÙ HỢP (EPISODIC VECTOR MEMORY - TOP {len(top_memories)}) ===\n"
            f"{mem_str}\n"
            f"========================================================="
        )
        return assembled_context
