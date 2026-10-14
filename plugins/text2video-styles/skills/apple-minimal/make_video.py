#!/usr/bin/env python3
"""极简苹果风 出片脚本
用法: python3 make_video.py spec.json out.mp4
spec.json: {"lines":["第一行","第二行",...], "final":["结尾第1行","结尾第2行",...]}
  lines: 每屏一行，在玻璃框里逐行出现（会自动缩字号保证单行）
  final: 结尾完整文案的分行（省略则使用 lines）
依赖: python3 playwright(chromium)、ffmpeg、Noto Sans CJK(思源黑体)、
      在本目录执行一次 `npm install lxgw-wenkai-webfont`（霞鹜文楷，OFL）
"""
import asyncio, json, os, sys, html, shutil, subprocess
from playwright.async_api import async_playwright
D=os.path.dirname(os.path.abspath(__file__)); FPS=30; LINE=1.8; T0=0.15
def build(spec):
    lines=spec['lines']; final=spec.get('final') or lines; n=len(lines)
    last=T0+LINE*n; total=round(last+2.5,2)
    card=open(os.path.join(D,'card.tpl')).read()
    cards='\n'.join(card.replace('__ID__',f'c{i+1}').replace('__TEXT__',html.escape(t)) for i,t in enumerate(lines))
    s=open(os.path.join(D,'template.html')).read()
    rep={'__CARDS__':cards,'__IDS__':json.dumps([f'c{i+1}' for i in range(n)]),'__FINAL__':'<br>'.join(html.escape(x) for x in final),
         '__C0__':f'{last-0.05:.2f}','__C1__':f'{last+0.8:.2f}','__F0__':f'{last+0.4:.2f}','__F1__':f'{last+1.1:.2f}','__TOTAL__':f'{total}'}
    for k,v in rep.items(): s=s.replace(k,v)
    p=os.path.join(D,'_page.html'); open(p,'w').write(s); return p,total
async def render(page,total,fdir):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(args=['--force-color-profile=srgb'])
        pg=await b.new_page(viewport={'width':540,'height':960},device_scale_factor=2)
        await pg.goto('file://'+page); await pg.evaluate('document.fonts.ready'); await pg.evaluate(f'render({total-0.5})'); await pg.wait_for_timeout(1500)
        for i in range(int(round(total*FPS))):
            await pg.evaluate(f'render({i/FPS})'); await pg.screenshot(path=f'{fdir}/{i:05d}.png')
        await b.close()
def main():
    spec=json.load(open(sys.argv[1])); out=os.path.abspath(sys.argv[2])
    page,total=build(spec); fdir=os.path.join(D,'_frames'); shutil.rmtree(fdir,ignore_errors=True); os.makedirs(fdir)
    asyncio.run(render(page,total,fdir))
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',f'{fdir}/%05d.png','-stream_loop','-1','-i',os.path.join(D,'assets','starlight.m4a'),
        '-map','0:v','-map','1:a','-c:v','libx264','-pix_fmt','yuv420p','-crf','17','-af',f'afade=t=in:d=0.2,afade=t=out:st={total-1.1:.2f}:d=1.1',
        '-c:a','aac','-b:a','192k','-t',f'{total}',out],check=True)
    shutil.rmtree(fdir,ignore_errors=True); print(out,total)
if __name__=='__main__': main()
