from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import uvicorn

from book_to_audiovideo.config import get_settings
from book_to_audiovideo.logging_config import configure_logging
from book_to_audiovideo.web.app import create_app
from book_to_audiovideo.web.dependencies import get_orchestrator


def run() -> None:
    parser = argparse.ArgumentParser(prog="book-to-audiovideo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    server_parser = subparsers.add_parser("serve", help="Avvia dashboard e API locali")
    server_parser.add_argument("--host", default=None)
    server_parser.add_argument("--port", type=int, default=None)

    pipeline_parser = subparsers.add_parser("run", help="Esegue un job CLI una tantum")
    pipeline_parser.add_argument("source_file")

    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)

    if args.command == "serve":
        uvicorn.run(
            "book_to_audiovideo.web.app:create_app",
            host=args.host or settings.app_host,
            port=args.port or settings.app_port,
            factory=True,
            reload=False,
        )
        return

    orchestrator = get_orchestrator()
    state = orchestrator.create_job(Path(args.source_file))
    asyncio.run(orchestrator.run_job(state.job_id))


if __name__ == "__main__":
    run()
