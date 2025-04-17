from datetime import datetime

def is_april_fools():
    return datetime.now().month == 4 and datetime.now().day == 1

def format_date(date: str) -> str:
    return datetime.strptime(date, "%d.%m.%Y").strftime("%B %d, %Y")
