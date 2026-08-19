"""Demo script showcasing HybridMemoryAgent with 5 distinct retrieval scenarios."""
from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bonus.agent import HybridMemoryAgent


def main() -> int:
    print("================================================================================")
    print("DEMO: HYBRID MEMORY AGENT FOR VIETNAMESE AI ASSISTANT (TRACK 2 - DAY 19 BONUS)")
    print("================================================================================\n")

    agent = HybridMemoryAgent()

    # Seed some user memories for u_001
    user_id = "u_001"
    sample_notes = [
        "Đã đọc tài liệu Kubernetes Deep Dive: Cấu hình Horizontal Pod Autoscaler (HPA) và Cluster Autoscaler trên AWS EKS.",
        "Ghi chú nghiên cứu Cloud Security: Quản lý Identity & Access Management (IAM), phân quyền Least Privilege và mã hóa KMS.",
        "Nghiên cứu về cơ sở dữ liệu phân tán: Triển khai CockroachDB và tối ưu hóa Raft consensus cho multi-region deployment.",
        "Đọc bài viết về MLOps: Quản lý Feature Store với Feast, kiểm soát Data Leakage qua Point-in-Time joins.",
        "Tóm tắt kiến trúc Microservices: Sử dụng gRPC cho internal communication và Istio Service Mesh để kiểm soát traffic.",
    ]

    print(f"[*] Nạp {len(sample_notes)} ghi chú/ký ức vào Episodic Memory cho user '{user_id}'...")
    for note in sample_notes:
        agent.remember(note, user_id=user_id)
    print("[+] Hoàn tất nạp ký ức vào Qdrant vector collection.\n")

    test_queries = [
        ("1. Truy xuất ký ức trực tiếp (Exact/Vector hit)", "Tôi đã đọc gì về Kubernetes?"),
        ("2. Gợi ý theo hồ sơ sở thích (Profile context)", "Recommend đọc gì tiếp theo?"),
        ("3. Truy vấn hoạt động tức thời (Recent velocity)", "Tôi đang quan tâm gì gần đây?"),
        ("4. Truy vấn diễn đạt lại (Paraphrase semantics)", "Tài liệu về tự động mở rộng hạ tầng?"),
        ("5. Truy vấn kết hợp (Hybrid episodic + Profile context)", "Cho tôi summary cloud security."),
    ]

    for title, query in test_queries:
        print("-" * 80)
        print(f"KỊCH BẢN {title}")
        print(f">> Câu hỏi của người dùng: '{query}'")
        print("-" * 80)
        context = agent.recall(query, user_id=user_id, top_k=2)
        print(context)
        print()

    print("================================================================================")
    print("DEMO HOÀN TẤT THÀNH CÔNG (Exit code 0)")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
