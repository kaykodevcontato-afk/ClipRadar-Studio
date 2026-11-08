"""Local ClipRadar API. Serves the same UI as GitHub Pages plus local-only generation."""
from __future__ import annotations
import json, threading, uuid
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from engine import make

BASE=Path(__file__).resolve().parent.parent
WORK=BASE/'workspace'; WORK.mkdir(exist_ok=True)
SITE=BASE/'site'
app=FastAPI(title='ClipRadar Local Processor')
jobs={}
lock=threading.Lock()
MAX_BYTES=2*1024**3

@app.get('/api/health')
def health():return {'ok':True,'mode':'local','details':'Arquivos processados no seu computador'}

@app.post('/api/generate')
async def generate(file:UploadFile=File(...),duration:int=Form(60),count:int=Form(3),resolution:str=Form('720'),captions:bool=Form(True)):
    if not lock.acquire(blocking=False):raise HTTPException(409,'Já existe um processamento em andamento.')
    if duration not in (15,30,60) or count not in (1,3,5) or resolution not in ('720','1080'):
        lock.release(); raise HTTPException(400,'Configuração inválida.')
    jid=uuid.uuid4().hex[:12];folder=WORK/jid;folder.mkdir()
    ext=Path(file.filename or '').suffix.lower()
    if ext not in ('.mp4','.mov','.mkv','.webm','.avi'):
        lock.release();raise HTTPException(400,'Formato não suportado. Envie MP4, MOV, MKV, WEBM ou AVI.')
    source=folder/('input'+ext)
    size=0
    try:
        with source.open('wb') as dst:
            while chunk:=await file.read(1024*1024):
                size+=len(chunk)
                if size>MAX_BYTES:raise HTTPException(413,'Máximo de 2 GB por vídeo.')
                dst.write(chunk)
    except Exception:
        source.unlink(missing_ok=True);lock.release();raise
    finally:await file.close()
    jobs[jid]={'status':'queued','progress':0,'message':'Arquivo recebido','results':[],'warning':None}
    def update(p,msg):jobs[jid].update(progress=p,message=msg,status='processing')
    def task():
        try:
            results,warn=make(source,folder,{'duration':duration,'count':count,'resolution':resolution,'captions':captions},update)
            for r in results:
                r['url']=f'/api/jobs/{jid}/files/{r["file"]}'
                if r.get('srt'):r['srt_url']=f'/api/jobs/{jid}/files/{r["srt"]}'
            jobs[jid].update(status='done',progress=100,message='Seus Shorts estão prontos!',results=results,warning=warn)
        except Exception as e:jobs[jid].update(status='error',message=str(e))
        finally:lock.release()
    threading.Thread(target=task,daemon=True).start()
    return {'id':jid}

@app.get('/api/jobs/{jid}')
def job(jid:str):
    if jid not in jobs:raise HTTPException(404,'Trabalho não encontrado. Reiniciar o servidor limpa o histórico.')
    return jobs[jid]

@app.get('/api/jobs/{jid}/files/{filename}')
def retrieve(jid:str,filename:str):
    if jid not in jobs:raise HTTPException(404)
    if '/' in filename or '\\' in filename or filename.startswith('.') or filename not in {f['file'] for f in jobs[jid].get('results',[])} | {f.get('srt') for f in jobs[jid].get('results',[])}:
        raise HTTPException(404)
    f=WORK/jid/filename
    if not f.is_file():raise HTTPException(404)
    return FileResponse(f,filename=f.name)

app.mount('/',StaticFiles(directory=SITE,html=True),name='site')
