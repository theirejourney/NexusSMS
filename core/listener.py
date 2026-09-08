from core.database import init_db, log_message
from core.extractor import parse_institution_message
from colorama import Fore, Style, init

init(autoreset=True)

def handle_incoming_sms(sender: str, body: str):
    init_db()
    result = parse_institution_message(sender, body)
    
    log_message(
        sender=result["sender"],
        category=result["category"],
        extracted_code=result["extracted_code"],
        raw_body=result["raw_body"]
    )
    
    code_display = result['extracted_code'] or f"{Fore.RED}None{Style.RESET_ALL}"
    print(f"{Fore.GREEN}[+] Captured{Style.RESET_ALL} | Sender: {sender} | Category: {result['category']} | Code: {code_display}")
