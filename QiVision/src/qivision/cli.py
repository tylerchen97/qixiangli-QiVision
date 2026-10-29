from __future__ import annotations

import argparse
import json
import sys

from .orchestrator import Orchestrator
from .schemas import UserProfile


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="qivision", description="QiVision 望衡 命令行")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="分析一张舌象图片")
    a.add_argument("--image", required=True)
    a.add_argument("--user", default="cli-user")
    a.add_argument("--symptoms", default="", help="逗号分隔,如 fatigue,cold_limbs")
    a.add_argument("--medications", default="")
    a.add_argument("--allergies", default="")
    a.add_argument("--pregnant", action="store_true")

    s = sub.add_parser("serve", help="启动 API 服务")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)

    args = p.parse_args(argv)
    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("qivision.api:app", host=args.host, port=args.port)
        return 0

    with open(args.image, "rb") as f:
        data = f.read()
    split = lambda x: [i.strip() for i in x.split(",") if i.strip()]  # noqa: E731
    profile = UserProfile(user_id=args.user, pregnant=args.pregnant,
                          medications=split(args.medications), allergies=split(args.allergies))
    res = Orchestrator().analyze(profile, data, split(args.symptoms))
    print(json.dumps(res.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
