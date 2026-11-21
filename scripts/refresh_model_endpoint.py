#!/usr/bin/env python3
"""Re-point ncmath3's .env at the LIVE Hermes desktop llama.cpp supervisor.

Port + key rotate every time the Hermes desktop app restarts (symptom of
drift: agent replies die with APIConnectionError/401). Discovery: the
supervisor process in `ps` (--api-key *** --models-max), verified by an
authorized /v1/models listing; fallback: reuse the key caduceus stored in
~/.env files and probe the port. Prints only the port — never the key.

    python3 scripts/refresh_model_endpoint.py
"""
import json, pathlib, re, subprocess, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent.parent
ENV = HERE / ".env"
KEY_SOURCES = [  # (file, key name) — caduceus shares the same supervisor
    (pathlib.Path.home() / "mywork/caduceus/.env.docker", "CADUCEUS_MODEL_KEY"),
]


def candidates():
    out = subprocess.run(["ps", "-ax", "-o", "command"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "llama-server" in line and "--models-max" in line:
            m = re.search(r"--port[= ](\d+)", line)
            k = re.search(r"--api-key[= ](\S+)", line)
            if m:
                yield int(m.group(1)), (k.group(1) if k else None)


def stored_key():
    for path, name in KEY_SOURCES:
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def verified(port, key):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/models",
                                 headers=({"Authorization": f"Bearer {key}"} if key else {}))
    try:
        json.load(urllib.request.urlopen(req, timeout=5))
        return True
    except Exception:
        return False


def main():
    fallback = stored_key()
    for port, key in candidates():
        key = key or fallback
        if key and verified(port, key):
            url = f"http://192.168.65.254:{port}/v1"   # Docker-Desktop host IP
            lines = ENV.read_text().splitlines() if ENV.exists() else []
            def setline(lines, name, value):
                for i, l in enumerate(lines):
                    if l.startswith(name + "="):
                        lines[i] = f"{name}={value}"; return lines
                lines.append(f"{name}={value}"); return lines
            lines = setline(lines, "NCMATH3_MODEL_URL", url)
            lines = setline(lines, "NCMATH3_MODEL_KEY", key)
            ENV.write_text("\n".join(lines) + "\n")
            print(f"supervisor found on port {port}; {ENV} updated (key not shown)")
            return
    sys.exit("no verified supervisor found — is the Hermes desktop app running?")


if __name__ == "__main__":
    main()
