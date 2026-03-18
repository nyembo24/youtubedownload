import os
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from download import get_formats, download_format

app = FastAPI(title="télécharger des vidéos youtube")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "form_data": None
        }
    )
@app.post("/verifier", response_class=HTMLResponse)
async def verification(request: Request, url: str = Form("")):
    data = None
    error = None
    if url.strip():
        try:
            formats = get_formats(url.strip())
            data = [
                f for f in formats
                if f.get("format_id")
                and (f.get("acodec") and f.get("acodec") != "none"
                     or f.get("vcodec") and f.get("vcodec") != "none")
            ]
            if not data:
                error = "Aucun format disponible pour ce lien."
        except Exception as exc:
            error = f"Erreur pendant la verification: {exc}"
    else:
        error = "Veuillez saisir une URL."
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "form_data": data,
            "error": error,
            "url": url.strip(),
        }
    )


@app.get("/download")
async def download(url: str, format_id: str):
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL manquante.")
    if not format_id.strip():
        raise HTTPException(status_code=400, detail="Format manquant.")
    try:
        filepath = download_format(url.strip(), format_id.strip())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur de téléchargement: {exc}")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    return FileResponse(filepath, filename=os.path.basename(filepath), media_type="application/octet-stream")
