from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from app.cli import configure_utf8_stdio
from langfuse import Langfuse


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Quản lý prompt version trên Langfuse")
    parser.add_argument("action", choices=["status", "promote", "rollback"], help="Hành động cần làm")
    parser.add_argument("--name", default="day13-chat", help="Tên prompt (mặc định: day13-chat)")
    args = parser.parse_args()

    client = Langfuse()

    if args.action == "status":
        p_base = client.get_prompt(args.name, label="baseline")
        p_cand = client.get_prompt(args.name, label="candidate")
        p_prod = client.get_prompt(args.name, label="production")
        print("=== Langfuse Prompt Versions ===")
        print(f"Prompt Name: {args.name}")
        print(f" - Baseline (v{p_base.version}): {p_base.labels}")
        print(f" - Candidate (v{p_cand.version}): {p_cand.labels}")
        print(f" - Production trỏ tới: v{p_prod.version}")

    elif args.action == "promote":
        # Promote: gán label production sang version 2 (candidate)
        print("Promoting version 2 to 'production'...")
        client.update_prompt(name=args.name, version=2, new_labels=["candidate", "production"])
        p_prod = client.get_prompt(args.name, label="production")
        print(f"-> Thành công! Label 'production' hiện trỏ tới version: {p_prod.version}")

    elif args.action == "rollback":
        # Rollback: gán label production quay lại version 1 (baseline)
        print("Rolling back: gán label 'production' quay lại version 1...")
        client.update_prompt(name=args.name, version=1, new_labels=["baseline", "production"])
        p_prod = client.get_prompt(args.name, label="production")
        print(f"-> Thành công! Label 'production' đã rollback về version: {p_prod.version}")


if __name__ == "__main__":
    main()
