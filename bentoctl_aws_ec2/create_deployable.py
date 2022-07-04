from __future__ import annotations

from typing import Any


def create_deployable(
    bento_path: str,
    destination_dir: str,
    bento_metadata: dict[str, Any],
    overwrite_deployable: bool,
) -> str:
    return destination_dir
