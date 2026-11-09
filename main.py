from __future__ import annotations

import math
import re
import shutil
import time

from rich.console import Console
from rich.text import Text
from rich.theme import Theme

from provider.adakami_provider import send_otp as adakami_send_otp
from provider.indosaku_provider import send_otp as indosaku_send_otp
from provider.kredione_provider import send_otp as kredione_send_otp
from provider.rc_provider import send_otp as rc_send_otp
from provider.kreditnavigator_provider import send_otp as kreditnavigator_send_otp

COOLDOWN_SECONDS = 62

PROVIDERS: list[tuple[str, object]] = [
    ("AdaKami",          adakami_send_otp),
    ("Indosaku",         indosaku_send_otp),
    ("KrediOne",         kredione_send_otp),
    ("RupiahCepat",      rc_send_otp),
    ("KreditNavigator",  kreditnavigator_send_otp),
]

_BLOCK_GLYPHS: dict[str, tuple[str, ...]] = {
    "S": ("███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"),
    "P": ("██████╗ ", "██╔══██╗", "██████╔╝", "██╔═══╝ ", "██║     ", "╚═╝     "),
    "A": (" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"),
    "M": ("███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"),
    "C": (" ██████╗", "██╔════╝", "██║     ", "██║     ", "╚██████╗", " ╚═════╝"),
}
_WORD = "SPAMSCAM"

THEME = Theme(
    {
        "accent": "cyan",
        "muted": "dim",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
    }
)

console = Console(theme=THEME, highlight=False, color_system="standard")


def _term_width() -> int:
    return min(88, shutil.get_terminal_size((88, 24)).columns)


def _build_block_rows(word: str) -> list[Text]:
    rows: list[Text] = []
    for row in range(6):
        line = Text()
        for letter in word:
            for ch in _BLOCK_GLYPHS[letter][row]:
                line.append(ch, "bold white" if ch == "█" else "dim")
        rows.append(line)
    return rows


def print_banner() -> None:
    width = _term_width()
    console.print()
    sample = "".join(_BLOCK_GLYPHS[c][0] for c in _WORD)
    if len(sample) <= width:
        for row in _build_block_rows(_WORD):
            console.print(row, width=width)
    else:
        console.print("SPAMSCAM", style="bold white")
    console.print()
    console.print("SPAMSCAM / OTP SPAM TOOL", style="bold")
    console.print("Multi-provider · Rotating cycle · Auto cooldown", style="muted")
    console.print()


def normalize_phone(value: str) -> str:
    value = re.sub(r"\D", "", value)
    if value.startswith("62"):
        value = "0" + value[2:]
    return value


def countdown(seconds: float) -> None:
    end = time.monotonic() + seconds
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            break
        mins, secs = divmod(math.ceil(remaining), 60)
        print(f"\r  Cooldown: {mins:02d}:{secs:02d} ...", end="", flush=True)
        time.sleep(min(0.5, remaining))
    print("\r" + " " * 30 + "\r", end="", flush=True)


def read_input() -> tuple[str, int] | None:
    no_hp = normalize_phone(input("  Nomor HP     : ").strip())

    if not re.fullmatch(r"08\d{8,14}", no_hp):
        console.print("\n  [!] Nomor HP tidak valid. Contoh: 08978397772\n", style="error")
        return None

    raw = input("  Jumlah resend : ").strip()
    try:
        jml_resend = int(raw) if raw else 0
    except ValueError:
        console.print("\n  [!] Jumlah resend harus berupa angka.\n", style="error")
        return None

    if jml_resend < 1:
        console.print("\n  [!] Jumlah resend minimal 1.\n", style="error")
        return None

    return no_hp, jml_resend


def run_cycle(no_hp: str, cycle: int, total: int) -> None:
    width = _term_width()
    divider = "─" * min(50, width - 2)

    console.print()
    console.print(f"  {divider}", style="muted")
    header = Text()
    header.append(f"  Siklus {cycle}/{total}", style="bold accent")
    header.append(f"  ·  Target: {no_hp}", style="muted")
    console.print(header)
    console.print(f"  {divider}", style="muted")

    col_w = 32
    for name, send_fn in PROVIDERS:
        label = f"  Meminta request OTP ke {name}..."
        print(f"{label:{col_w}}", end="", flush=True)

        ok = False
        try:
            ok = send_fn(no_hp)  # type: ignore[call-arg]
        except Exception:  # pylint: disable=broad-except
            ok = False

        if ok:
            console.print("[ [success]OK[/success] ]")
        else:
            console.print("[ [error]Gagal[/error] ]")

    console.print(f"  {divider}", style="muted")


def main() -> None:
    print_banner()

    data = read_input()
    if data is None:
        return

    no_hp, jml_resend = data

    try:
        for i in range(1, jml_resend + 1):
            run_cycle(no_hp, i, jml_resend)

            if i < jml_resend:
                console.print(
                    f"\n  Cooldown {COOLDOWN_SECONDS} detik sebelum siklus berikutnya...",
                    style="muted",
                )
                countdown(COOLDOWN_SECONDS)

    except KeyboardInterrupt:
        console.print("\n\n  [!] Dibatalkan oleh pengguna.\n", style="warning")
        return

    console.print("\n  Selesai. Semua siklus telah dijalankan.\n", style="success")


if __name__ == "__main__":
    main()
