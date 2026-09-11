from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def env(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name, default)
    return val if val not in ("", None) else default


def cargar_modelos() -> dict:
    with open(ROOT / "config" / "modelos.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["modelos"]


def presupuesto() -> tuple[float, float]:
    return float(env("BUDGET_MAX_PER_JOB", "3")), float(env("BUDGET_MAX_PER_DAY", "25"))
