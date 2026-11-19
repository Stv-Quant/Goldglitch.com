"""Usar la suscripción de Claude (Pro/Max) a través de Claude Code instalado en este PC, con Haiku 5.5.

Claude Code (`claude`) inicia sesión con tu cuenta de Claude; aquí se llama en modo no interactivo (`claude -p`).
No se usan claves de API ni se tocan tus credenciales: Claude Code las maneja solo. Lo que gasten los agentes sale de
tu cupo de Pro, igual que si lo usaras tú.

    python goldglitch_claude_cli.py      # comprueba que Claude Code está instalado y con sesión
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

MODEL = os.environ.get("REDES_MODELO", "claude-haiku-5-5")
HERE = os.path.dirname(os.path.abspath(__file__))
WORKDIR = os.path.join(HERE, "redes_claude")      # empty folder: no project files or settings get loaded


class CliError(RuntimeError):
    pass


class UsageLimit(CliError):
    """Pro usage cap reached: wait for the reset (nothing is lost, the next run retries)."""


def find_claude() -> str | None:
    p = shutil.which("claude")
    if p:
        return p
    home = os.path.expanduser("~")
    for c in (os.path.join(home, ".local", "bin", "claude.exe"), os.path.join(home, ".local", "bin", "claude"),
              os.path.join(home, "AppData", "Local", "Programs", "claude", "claude.exe")):
        if os.path.exists(c):
            return c
    return None


def available() -> bool:
    return find_claude() is not None and os.environ.get("REDES_USAR_PRO", "1") != "0"


def run(prompt: str, system: str, *, mcp_config: dict | None = None, allowed_tools: str | None = None,
        max_turns: int = 1, timeout: int = 300, model: str = MODEL) -> str:
    """One non-interactive Claude Code run. Returns the final text. Raises UsageLimit / CliError."""
    exe = find_claude()
    if not exe:
        raise CliError("Claude Code no está instalado (ver instrucciones en instalar_claude_code.bat)")
    os.makedirs(WORKDIR, exist_ok=True)
    args = [exe, "-p", "--model", model, "--output-format", "json", "--no-session-persistence",
            "--max-turns", str(max_turns), "--permission-mode", "dontAsk", "--permission-prompts", "none",
            "--tools", "", "--disable-slash-commands"]
    cfg_path = None
    if mcp_config:
        fd, cfg_path = tempfile.mkstemp(prefix="gg_mcp_", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f)
        args += ["--strict-mcp-config", "--mcp-config", cfg_path]
        if allowed_tools:
            args += ["--allowedTools", allowed_tools]
    else:
        args += ["--strict-mcp-config", "--disallowedTools", "mcp__*"]
    sys_fd, sys_path = tempfile.mkstemp(prefix="gg_sys_", suffix=".txt")
    with os.fdopen(sys_fd, "w", encoding="utf-8") as f:
        f.write(system)
    args += ["--system-prompt-file", sys_path]
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}  # use the Pro login
    try:
        p = subprocess.run(args, input=prompt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, cwd=WORKDIR, env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise CliError(f"Claude Code tardó más de {timeout} s")
    finally:
        for fp in (cfg_path, sys_path):
            if fp:
                try:
                    os.remove(fp)
                except OSError:
                    pass
    out = (p.stdout or "").strip()
    try:
        j = json.loads(out[out.find("{"):]) if out else {}
    except ValueError:
        j = {}
    text = str(j.get("result") or "")
    blob = f"{text} {p.stderr or ''} {out[:500]}".lower()
    if re.search(r"usage limit|limit reached|rate.?limit|l[ií]mite de uso|5-hour limit|weekly limit", blob):
        raise UsageLimit("se alcanzó el límite de uso de tu plan; se reintentará después del reinicio")
    if "not logged in" in blob or "please run /login" in blob or "authentication" in blob and j.get("is_error"):
        raise CliError("Claude Code no tiene sesión iniciada: abre una terminal, escribe  claude  e inicia sesión")
    if p.returncode != 0 or j.get("is_error"):
        raise CliError(f"Claude Code falló ({p.returncode}): {(text or p.stderr or out)[:300]}")
    return text


def ask_json(system: str, task: str, timeout: int = 300) -> dict:
    """Text-only call that must answer with one JSON object."""
    text = run(task, system + "\n\nResponde SOLO con un objeto JSON válido, sin texto adicional ni bloques de código.",
               timeout=timeout)
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except ValueError as e:
        raise CliError(f"respuesta sin JSON válido: {e}: {text[:200]}")


def ask_text(system: str, task: str, timeout: int = 300) -> str:
    return run(task, system, timeout=timeout)


if __name__ == "__main__":
    exe = find_claude()
    if not exe:
        print("Claude Code NO está instalado. Corre instalar_claude_code.bat")
        sys.exit(1)
    print(f"Claude Code: {exe}")
    st = subprocess.run([exe, "auth", "status"], capture_output=True, text=True)
    print(st.stdout.strip() or st.stderr.strip())
    try:
        print("Prueba con", MODEL, "→", ask_text("Responde en una línea.", "Di 'Goldglitch listo' y nada más."))
    except CliError as e:
        print("ERROR:", e)
        sys.exit(1)
