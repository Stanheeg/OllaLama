from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    mode: str = _env("TRUSTFLOW_MODE", "fixture")
    db_path: str = _env("TRUSTFLOW_DB_PATH", "./trustflow.db")
    serpapi_api_key: str = _env("SERPAPI_API_KEY")
    nutrient_api_key: str = _env("NUTRIENT_API_KEY")
    nutrient_extract_url: str = _env(
        "NUTRIENT_EXTRACT_URL", "https://api.nutrient.io/extraction/extract"
    )
    gemini_api_key: str = _env("GEMINI_API_KEY")
    gemini_model: str = _env("GEMINI_MODEL", "gemini-2.5-flash")
    xano_workflow_upsert_url: str = _env("XANO_WORKFLOW_UPSERT_URL")
    xano_audit_event_url: str = _env("XANO_AUDIT_EVENT_URL")
    xano_api_token: str = _env("XANO_API_TOKEN")
    doctavian_generate_url: str = _env("DOCTAVIAN_GENERATE_URL")
    doctavian_api_key: str = _env("DOCTAVIAN_API_KEY")
    doctavian_auth_header: str = _env("DOCTAVIAN_AUTH_HEADER", "Authorization")
    doctavian_auth_prefix: str = _env("DOCTAVIAN_AUTH_PREFIX", "Bearer")
    doctavian_template_id: str = _env("DOCTAVIAN_TEMPLATE_ID")
    foxit_client_id: str = _env("FOXIT_CLIENT_ID")
    foxit_client_secret: str = _env("FOXIT_CLIENT_SECRET")
    foxit_esign_create_url: str = _env(
        "FOXIT_ESIGN_CREATE_URL",
        "https://na1.fusion.foxit.com/esign/api/v1/folders/createfolder",
    )

    @property
    def live(self) -> bool:
        return self.mode.lower() == "live"
