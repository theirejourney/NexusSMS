import argparse
import sys
import uvicorn
from core.database import init_db, get_messages as get_recent_messages

def main():
    parser = argparse.ArgumentParser(description="NexusSMS: Universal OTP & Message Ingestion Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    server_parser = subparsers.add_parser("server", help="Start the webhook ingestion server")
    server_parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    server_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")

    logs_parser = subparsers.add_parser("logs", help="View recently captured messages")
    logs_parser.add_argument("--limit", type=int, default=10)
    logs_parser.add_argument("--provider", type=str, default=None)

    args = parser.parse_args()

    init_db()

    if args.command == "server":
        print(f"[*] Starting NexusSMS on {args.host}:{args.port}")
        uvicorn.run("core.server:app", host=args.host, port=args.port, reload=False)
    elif args.command == "logs":
        rows = get_recent_messages(limit=args.limit, provider=args.provider)
        print(f"\n{'TIMESTAMP':<26} | {'PROVIDER':<10} | {'SENDER':<15} | {'CATEGORY':<12} | {'CODE':<10}")
        print("-" * 85)
        for row in rows:
            ts = row.get("timestamp", "")
            prov = row.get("provider", "")
            sender = row.get("sender", "")
            cat = row.get("category", "")
            code = row.get("extracted_code") or ""
            print(f"{ts:<26} | {prov:<10} | {sender:<15} | {cat:<12} | {str(code):<10}")
        print()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
