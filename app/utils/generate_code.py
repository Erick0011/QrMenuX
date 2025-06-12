from app.utils.now_angola import now_angola
import secrets


def generate_code():
    now = now_angola().strftime("%y%m%d%H%M")  # Ex: "2506051230"
    rand = secrets.token_hex(2)  # Ex: "a1b2"
    return f"R-{now}-{rand}"  # Ex: "R-2506051230-a1b2"
