"""ClipRadar: local, explainable highlight ranking from own gameplay footage."""
from __future__ import annotations
import json, math, os, random, re, shutil, subprocess, tempfile
from pathlib import Path
import cv2
import numpy as np


def run(cmd, **kwargs):
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-1800:])
    return p.stdout


def probe(path):
    data = json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
    vid = next((s for s in data['streams'] if s['codec_type']=='video'), None)
    if vid is None: raise ValueError('O arquivo não contém vídeo.')
    duration = float(data['format'].get('duration') or vid.get('duration') or 0)
    if duration < 3: raise ValueError('Envie um vídeo de pelo menos 3 segundos.')
    return duration, any(s['codec_type']=='audio' for s in data['streams'])


def analyze(path, duration, audio=True):
    """Samples at about 2 frames/sec. High differences and loud audio get higher scores."""
    secs = max(1, int(math.ceil(duration)))
    energy = np.zeros(secs, dtype=float)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened(): raise ValueError('Não foi possível abrir o vídeo com OpenCV.')
    prev = None
    try:
        for t in np.arange(0, duration, .5):
            cap.set(cv2.CAP_PROP_POS_MSEC, float(t*1000))
            ok, frame = cap.read()
            if not ok: continue
            small = cv2.resize(frame, (160,90))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            if prev is not None:
                score = float(np.mean(cv2.absdiff(gray, prev)))
                energy[min(secs-1,int(t))] += score
            prev = gray
    finally: cap.release()
    if audio:
        # Decode low-resolution audio, maximum 1h supported by default file length cap.
        p = subprocess.run(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','8000','-f','s16le','pipe:1'], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if p.returncode == 0 and p.stdout:
            pcm = np.frombuffer(p.stdout,dtype=np.int16)
            rms = np.zeros(secs)
            for i in range(secs):
                chunk = pcm[i*8000:(i+1)*8000]
                if len(chunk): rms[i] = np.sqrt(np.mean(chunk.astype(float)**2))
            if np.max(rms)>0: energy += 18*rms/(np.max(rms)+1e-9)
    if np.max(energy)>0: energy=energy/np.max(energy)
    return energy


def choose_clips(energy, duration, target, index):
    """Non-overlapping shots within a short; seed changes the selection per output."""
    target=min(float(target), duration)
    if target<3: raise ValueError('Vídeo muito curto.')
    if duration<=target+.5: return [(0.,round(target,2))]
    rng=random.Random(28411 + index*101)
    candidates=[]
    for start in np.arange(0, max(0.1,duration-3), 2.5):
        for length in (5., 7., 9., 12.):
            end=min(duration,float(start+length))
            if end-start < 3: continue
            lo=int(start); hi=min(len(energy),max(lo+1,int(math.ceil(end))))
            score=float(np.mean(energy[lo:hi])) + rng.uniform(-.12,.12)
            candidates.append((score,float(start),float(end)))
    candidates.sort(reverse=True)
    chosen=[]; total=0.
    def free(a,b): return all(b<=x+.08 or a>=y-.08 for x,y in chosen)
    for _,a,b in candidates:
        if total >= target-.15: break
        if not free(a,b): continue
        need=target-total
        if need < 3: break
        b=min(b,a+need)
        if b-a>=3:
            chosen.append((a,b)); total+=b-a
    if total < target-.2:
        # Fill remaining gaps while avoiding reused time ranges within this short.
        cur=0.
        for a,b in sorted(chosen)+[(duration,duration)]:
            if cur<a and target-total>.1:
                end=min(a,cur+(target-total))
                if end>cur: chosen.append((cur,end)); total+=end-cur
            cur=max(cur,b)
    if total<target-.35: raise ValueError('Não foi possível selecionar trechos suficientes.')
    # For a dynamic montage, high-energy moments first, with some variation.
    chosen=sorted(chosen,key=lambda x: -float(np.mean(energy[int(x[0]):max(int(x[0])+1,int(math.ceil(x[1])))])))
    if index==1: chosen=chosen[1::2]+chosen[::2]
    if index==2: chosen=list(reversed(chosen))
    return [(round(a,3),round(b,3)) for a,b in chosen]


def transcribe(path, model='tiny'):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None, 'Legendas por voz indisponíveis: instale faster-whisper (opcional).'
    try:
        whisper=WhisperModel(model,device='cpu',compute_type='int8')
        segments,_=whisper.transcribe(str(path),language='pt',vad_filter=True,word_timestamps=True)
        words=[]
        for seg in segments:
            if seg.words:
                for w in seg.words: words.append((float(w.start),float(w.end),w.word.strip()))
            else: words.append((float(seg.start),float(seg.end),seg.text.strip()))
        return words, None if words else 'Não foi detectada fala para legendar.'
    except Exception as e:
        return None, 'Não foi possível transcrever: '+str(e)[:120]


def srt_time(t):
    ms=int(round(t*1000)); h,rem=divmod(ms,3600000); m,rem=divmod(rem,60000); s,ms=divmod(rem,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def write_srt(words, clips, out):
    items=[]; offset=0.
    for a,b in clips:
        for wstart,wend,word in words:
            if wend<=a or wstart>=b or not word: continue
            st=offset+max(0.,wstart-a); en=offset+min(b-a,wend-a)
            if en-st>.04: items.append((st,en,word))
        offset += b-a
    # Group words into readable captions ~2.6 seconds.
    groups=[]; g=[]
    for entry in items:
        if g and (entry[1]-g[0][0]>2.6 or len(g)>=7 or entry[0]-g[-1][1]>.7):
            groups.append(g);g=[]
        g.append(entry)
    if g:groups.append(g)
    out.write_text(''.join(f'{i}\n{srt_time(g[0][0])} --> {srt_time(g[-1][1])}\n{" ".join(w[2] for w in g)}\n\n' for i,g in enumerate(groups,1)),encoding='utf-8')
    return len(groups)


def render(source, clips, mp4, srt=None, title='', resolution='720'):
    w,h=(1080,1920) if resolution=='1080' else (720,1280)
    with tempfile.TemporaryDirectory(prefix='clipradar_') as td:
        td=Path(td);parts=[]
        for idx,(a,b) in enumerate(clips):
            segment=td/f'shot_{idx:02}.mp4'
            vf=f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps=30'
            run(['ffmpeg','-hide_banner','-y','-loglevel','error','-ss',str(a),'-i',str(source),'-t',str(b-a),'-vf',vf,'-an','-c:v','libx264','-preset','veryfast','-crf','25','-pix_fmt','yuv420p',str(segment)])
            parts.append(segment)
        concat=td/'list.txt'
        concat.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in parts),encoding='utf-8')
        merged=td/'merged.mp4'
        run(['ffmpeg','-hide_banner','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(merged)])
        # Input audio cut per clip, then concatenate to preserve soundtracks, if present.
        audios=[]
        _,has_audio=probe(source)
        if has_audio:
            for i,(a,b) in enumerate(clips):
                sound=td/f'audio_{i:02}.m4a'
                try:
                    run(['ffmpeg','-hide_banner','-y','-loglevel','error','-ss',str(a),'-i',str(source),'-t',str(b-a),'-vn','-c:a','aac','-b:a','128k',str(sound)])
                    audios.append(sound)
                except Exception: audios=[];break
        soundtrack=None
        if len(audios)==len(clips):
            ac=td/'audios.txt'
            ac.write_text(''.join("file '"+str(p)+"'\n" for p in audios))
            soundtrack=td/'soundtrack.m4a'
            try:run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(ac),'-c','copy',str(soundtrack)])
            except Exception:soundtrack=None
        title=title[:64].strip()
        # Built-in drawtext may not be available on every system; text overlays are optional.
        filters=[]
        if title:
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            tfile=td/'title.txt';tfile.write_text(title,encoding='utf-8')
            if Path(font).exists():
                filters.append(f"drawtext=fontfile={font}:textfile={tfile}:fontsize={round(w*.050)}:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h*0.11:enable='lt(t,3.8)'")
        if srt and srt.exists() and srt.stat().st_size:
            escaped=str(srt).replace('\\','/').replace(':','\\:').replace("'","\\'")
            filters.append(f"subtitles=filename='{escaped}':force_style='Fontsize=18,Outline=2,Alignment=2,MarginV=190'")
        cmd=['ffmpeg','-hide_banner','-y','-loglevel','error','-i',str(merged)]
        if soundtrack:cmd+=['-i',str(soundtrack)]
        if filters:cmd+=['-vf',','.join(filters)]
        cmd+=['-map','0:v:0']
        if soundtrack:cmd+=['-map','1:a:0','-c:a','aac','-b:a','128k','-shortest']
        else:cmd+=['-an']
        cmd+=['-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(mp4)]
        try:run(cmd)
        except Exception:
            # On Windows builds ffmpeg might not support drawtext/subtitles; still deliver video.
            fallback=['ffmpeg','-hide_banner','-y','-loglevel','error','-i',str(merged)]
            if soundtrack:fallback+=['-i',str(soundtrack),'-map','0:v:0','-map','1:a:0','-c:a','aac','-shortest']
            fallback+=['-c:v','libx264','-preset','veryfast','-crf','24','-movflags','+faststart',str(mp4)]
            run(fallback)
        return mp4


def make(source, dest, settings, onprogress):
    duration,audio=probe(source)
    limit=int(settings.get('duration',60));count=int(settings.get('count',3))
    if duration<limit: raise ValueError(f'O vídeo tem {duration:.1f}s. Para gerar Shorts de {limit}s, envie um gameplay com pelo menos {limit}s.')
    onprogress(5,'Analisando movimento e intensidade do áudio…')
    energy=analyze(source,duration,audio)
    words=None;warn=None
    if settings.get('captions',True):
        onprogress(20,'Tentando transcrever a fala para criar legendas…')
        words,warn=transcribe(source)
    meta=[]; dest.mkdir(parents=True,exist_ok=True)
    names=['O momento mais ABSURDO!','Você viu o que aconteceu?!','Esse final é inacreditável!']
    for i in range(count):
        onprogress(25+int(65*i/count),f'Gerando Short {i+1} de {count}…')
        clips=choose_clips(energy,duration,limit,i)
        srt=dest/f'short_{i+1}.srt'
        if words:
            n=write_srt(words,clips,srt)
            if not n:srt=None
        else:srt=None
        title=f'GTA VI • {names[i%len(names)]}'
        mp4=dest/f'clipradar_short_{i+1:02d}.mp4'
        render(source,clips,mp4,srt=srt,title=title,resolution=settings.get('resolution','720'))
        meta.append({'name':f'Short {i+1}','file':mp4.name,'srt':srt.name if srt else None,'title':title,'description':f'🎮 GTA VI: {names[i%len(names)]} #GTA6 #GTAVI #Shorts #Gaming #ViceCity','clips':[{'start':a,'end':b} for a,b in clips]})
    (dest/'manifest.json').write_text(json.dumps({'items':meta,'warning':warn,'duration':duration},ensure_ascii=False,indent=2),encoding='utf-8')
    onprogress(100,'Concluído')
    return meta,warn
