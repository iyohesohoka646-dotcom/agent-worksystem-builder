"""Existing deterministic interface. The enhancement imports it without modifying it."""
def parse(text):
    items = [line.strip() for line in text.splitlines() if line.strip()]
    return {"count": len(items), "items": items}
