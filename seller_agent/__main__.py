"""CLI: python -m seller_agent  (needs ANTHROPIC_API_KEY; runs on synthetic fixture data)."""
import sys

from .assistant import Assistant


def main():
    a = Assistant()
    print("Seller assistant (synthetic data). Commands: /pending, /approve ID, /reject ID, /quit")
    who = "cli-user"
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if line in ("/quit", ""):
            if line:
                break
            continue
        if line == "/pending":
            for p in a.queue.pending():
                print(p.id, p.summary)
        elif line.startswith("/approve "):
            r = a.queue.approve(line.split()[1], who); print(r.status, r.result)
        elif line.startswith("/reject "):
            print(a.queue.reject(line.split()[1], who).status)
        else:
            print(a.ask(line))


if __name__ == "__main__":
    sys.exit(main())
