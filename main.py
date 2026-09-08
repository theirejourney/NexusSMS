# main.py
import argparse
import sys
from core.database import init_db, get_recent_messages
from core.server import app

def main():
    parser = argparse.ArgumentParser(description="NexusSMS: Institutional OTP & Message Ingestion Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'server' command
    server_parser = subparsers.add_parser("server", help="Start the webhook ingestion server")
    server_parser.add_argument("--port", type=int, default=5000, help="Port to run the webhook server on")

    # 'logs' command
    logs_parser = subparsers.add_parser("logs", help="View recently captured messages and OTPs")
    logs_parser.add_argument("--limit", type=int, default=10, help="Number of recent records to display")

    args = parser.parse_args()

    init_db()

    if args.command == "server":
        print(f"[*] Starting NexusSMS webhook server on port {args.port}...")
        app.run(host="0.0.0.0", port=args.port, debug=False)
    elif args.command == "logs":
        rows = get_recent_messages(args.limit)
        print(f"\n{'TIMESTAMP':<26} | {'SENDER':<15} | {'CATEGORY':<12} | {'CODE':<10}")
        print("-" * 75)
        for row in rows:
            timestamp, sender, category, code = row
            print(f"{timestamp:<26} | {sender:<15} | {category:<12} | {str(code):<10}")
        print()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
