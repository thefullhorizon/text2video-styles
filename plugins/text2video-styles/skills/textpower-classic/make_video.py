#!/usr/bin/env python3
"""经典风 出片脚本：python3 make_video.py spec.json out_dir [music.m4a]"""
import os, sys, json, shutil, subprocess, tempfile, numpy as np
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,BEAT=1080,1920,30,0.5
FONT_DIRS=['/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc','/opt/homebrew/share/fonts/NotoSansCJK-%s.ttc',os.path.expanduser('~/Library/Fonts/NotoSansCJK-%s.ttc'),'/Library/Fonts/NotoSansCJK-%s.ttc']
FONT_GLOBS=[next((f for f in FONT_DIRS if os.path.exists(f%'Regular')),FONT_DIRS[0])]  # 需安装思源黑体 Noto Sans CJK（ttc）
WHITE=(240,236,230); GRAY=(178,170,163); BAR=(120,110,104); LINE=(150,140,132)
ACCENTS=[(232,85,47),(93,185,138),(90,160,220),(200,120,220)]   # 橙 绿 蓝 紫，按屏轮换
GOLD=(255,204,38)                                               # 最后一屏固定金黄
_fc={}
def font(w,s):
    k=(w,int(s))
    if k not in _fc: _fc[k]=ImageFont.truetype(FONT_GLOBS[0]%w,int(s),index=2)  # index 2 = SC
    return _fc[k]
def make_bg():
    yy,xx=np.mgrid[0:H,0:W]; r=np.clip(np.sqrt(((xx-540)/620)**2+((yy-900)/1000)**2),0,1)**1.3
    c0=np.array([60,38,37]); c1=np.array([18,15,18])
    return Image.fromarray((c0*(1-r[...,None])+c1*r[...,None]).astype('uint8'),'RGB')
ROLE={'lead':("Medium",120,WHITE),'conn':("Regular",66,GRAY),'accent':("Bold",180,None)}
def fit(w,size,txt,maxw=860):
    while font(w,size).getlength(txt)>maxw: size-=4
    return size
def layout(screens):
    """screens: [[{"t":"清醒的人","role":"lead"},{"t":"不合群","role":"accent"}], ...]"""
    out=[]; t=0.0; n=len(screens)
    for si,els in enumerate(screens):
        last=si==n-1; items=[]
        for k,e in enumerate(els):
            w,size,col=ROLE[e['role']]
            if e['role']=='lead' and len(e['t'])>4: size=100
            if e['role']=='accent': col=GOLD if last else ACCENTS[si%len(ACCENTS)]; size=190 if last else 180
            size=fit(w,size,e['t']); offs=0 if k==0 else 1.0+0.5*(k-1)   # 断句卡 120BPM 节拍
            items.append(dict(t=e['t'],w=w,size=size,col=col,role=e['role'],ti=t+offs))
        gap=70; hs=[i['size'] for i in items]; tot=sum(hs)+gap*(len(hs)-1); y=900-tot/2
        for i,h in zip(items,hs): i['y']=y+h/2; y+=h+gap
        dur=(items[-1]['ti']-t)+(0.25+1.25 if last else 1.5)    # 末屏静止<=1.5s
        out.append(dict(t0=t,t1=None if last else t+dur,els=items,deco='underline' if last else 'bars')); t+=dur
    return out,t
def ease(x): x=max(0,min(1,x)); return 1-(1-x)**3
def frame(BG,S,t):
    im=BG.copy().convert('RGBA'); ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for s in S:
        if t<s['t0'] or (s['t1'] and t>=s['t1']): continue
        out,oy=1.0,0
        if s['t1']:
            p=(t-(s['t1']-0.3))/0.3
            if p>0: out=1-ease(p); oy=-14*ease(p)
        acc=None
        for e in s['els']:
            if t<e['ti']: continue
            if e['role']=='accent':
                p=ease((t-e['ti'])/0.22); sc=1.18-0.18*p; acc=e
                d.text((W/2,e['y']+oy),e['t'],font=font(e['w'],e['size']*sc),fill=e['col']+(int(255*p*out),),anchor='mm')
            else:
                p=ease((t-e['ti'])/0.3)
                d.text((W/2,e['y']+oy+(1-p)*24),e['t'],font=font(e['w'],e['size']),fill=e['col']+(int(255*p*out),),anchor='mm')
        if acc:
            p=ease((t-acc['ti']-0.05)/0.35)
            if s['deco']=='bars':
                h=120*p
                for x in (150,928): d.rectangle((x,acc['y']+oy-h/2,x+2,acc['y']+oy+h/2),fill=BAR+(int(255*p*out),))
            else:
                hw=110*p; yl=acc['y']+acc['size']*0.68
                d.rectangle((W/2-hw,yl,W/2+hw,yl+3),fill=LINE+(int(220*p),))
    return Image.alpha_composite(im,ov).convert('RGB')
def cover(BG,spec,path):
    """完整文案封面：每屏一行，lead 白 Medium 96 + accent 彩色 Bold 120；末屏 lead 一行 + 金黄大字 + 下划线"""
    im=BG.copy().convert('RGBA'); ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    sc=spec['screens']; n=len(sc); rows=[]
    for si,els in enumerate(sc):
        last=si==n-1; lead=''.join(e['t'] for e in els if e['role']!='accent'); accent=''.join(e['t'] for e in els if e['role']=='accent')
        if last:   # 末屏：lead 单独一行，连接词+关键词合成金黄大字（如「值得深交」）
            rows+= [('line',''.join(e['t'] for e in els if e['role']=='lead'),'',None,96),('big',''.join(e['t'] for e in els if e['role']!='lead'),GOLD,150)]
        else: rows.append(('pair',lead,accent,ACCENTS[si%len(ACCENTS)],120))
    hs=[150 if r[0]=='big' else 120 for r in rows]; gap=80; tot=sum(hs)+gap*(len(hs)-1); y=900-tot/2+40
    for r,h in zip(rows,hs):
        cy=y+h/2
        if r[0]=='pair':
            fa,fb=font("Medium",fit("Medium",96,r[1],500)),font("Bold",r[4]); wa,wb=fa.getlength(r[1]),fb.getlength(r[2]); x=(W-wa-wb)/2
            d.text((x,cy),r[1],font=fa,fill=WHITE+(255,),anchor='lm'); d.text((x+wa,cy),r[2],font=fb,fill=r[3]+(255,),anchor='lm')
        elif r[0]=='line': d.text((W/2,cy),r[1],font=font("Medium",fit("Medium",96,r[1])),fill=WHITE+(255,),anchor='mm')
        else:
            d.text((W/2,cy),r[1],font=font("Bold",fit("Bold",150,r[1])),fill=GOLD+(255,),anchor='mm')
            d.rectangle((W/2-120,cy+100,W/2+120,cy+103),fill=LINE+(220,))
        y+=h+gap
    Image.alpha_composite(im,ov).convert('RGB').save(path)
if __name__=='__main__':
    spec=json.load(open(sys.argv[1])); od=sys.argv[2]; music=sys.argv[3] if len(sys.argv)>3 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'assets','starlight.m4a'); os.makedirs(od,exist_ok=True)
    BG=make_bg(); S,END=layout(spec['screens']); tmp=tempfile.mkdtemp()
    for i in range(int(round(END*FPS))): frame(BG,S,i/FPS).save(f'{tmp}/{i:04d}.png')
    name=spec['name']; mp4=os.path.join(od,name+'.mp4')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{tmp}/%04d.png','-stream_loop','-1','-i',music,'-map','0:v','-map','1:a',
        '-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-af',f'afade=t=in:d=0.2,afade=t=out:st={END-1.1:.2f}:d=1.1',
        '-c:a','aac','-b:a','192k','-t',f'{END:.2f}',mp4],check=True)
    cover(BG,spec,os.path.join(od,name+'_封面.png')); shutil.rmtree(tmp); print(mp4,END)
