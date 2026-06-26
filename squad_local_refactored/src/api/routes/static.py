"""Static file serving endpoints (frontend ``dist/``).

Migrated 1:1 from the legacy monolith ``read_index`` and ``read_assets``.
"""

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

router = APIRouter()

# The frontend build lives at <repo_root>/dist/
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@router.get("/")
@router.get("/index.html")
def read_index():
    """Serve the built React ``index.html`` (or fallback local copy)."""
    dist_html = os.path.join(_REPO_ROOT, "dist", "index.html")
    if os.path.exists(dist_html):
        return FileResponse(dist_html)
    html_path = os.path.join(_BACKEND_ROOT, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("Error: index.html no encontrado", status_code=404)


@router.get("/assets/{asset_path:path}")
def read_assets(asset_path: str):
    """Serve Vite-built JS/CSS assets from ``dist/assets/``."""
    dist_asset = os.path.abspath(os.path.join(_REPO_ROOT, "dist", "assets", asset_path))
    dist_folder = os.path.abspath(os.path.join(_REPO_ROOT, "dist"))
    if dist_asset.startswith(dist_folder) and os.path.exists(dist_asset):
        mime_type = "application/octet-stream"
        if dist_asset.endswith(".js"):
            mime_type = "application/javascript"
        elif dist_asset.endswith(".css"):
            mime_type = "text/css"
        return FileResponse(dist_asset, media_type=mime_type)
    raise HTTPException(status_code=404, detail="Asset no encontrado")
