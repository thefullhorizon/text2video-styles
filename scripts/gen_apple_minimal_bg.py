"""程序生成「极简苹果风」背景：青蓝-松石绿弥散渐变（原创，无第三方素材）"""
import numpy as np
from PIL import Image, ImageFilter
W,H=1080,2340
ys=[0.0,0.2,0.4,0.6,0.75,0.9,1.0]; xs=[0.0,0.5,1.0]
G=[[(85,120,129),(49,88,106),(16,54,75)],[(81,119,129),(49,92,112),(22,66,90)],[(73,124,123),(56,106,118),(45,86,105)],
   [(59,126,120),(53,122,121),(71,107,120)],[(32,120,116),(39,118,119),(74,115,121)],[(26,92,105),(31,99,117),(34,107,128)],
   [(23,75,99),(28,85,114),(33,96,129)]]
G=np.array(G,float)
yy=np.linspace(0,1,H)[:,None]; xx=np.linspace(0,1,W)[None,:]
def interp(v,pts):
    i=np.clip(np.searchsorted(pts,v,side='right')-1,0,len(pts)-2); t=(v-np.array(pts)[i])/(np.array(pts)[i+1]-np.array(pts)[i]); return i,np.clip(t,0,1)
iy,ty=interp(yy[:,0],ys); ix,tx=interp(xx[0],xs)
out=np.zeros((H,W,3))
for c in range(3):
    g=G[:,:,c]
    a=g[iy][:,ix]*(1-tx)[None,:]+g[iy][:,ix+1]*tx[None,:]
    b=g[iy+1][:,ix]*(1-tx)[None,:]+g[iy+1][:,ix+1]*tx[None,:]
    out[:,:,c]=a*(1-ty)[:,None]+b*ty[:,None]
img=Image.fromarray(out.clip(0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(120))
n=np.random.default_rng(1).normal(0,1.2,(H,W,1)); img=Image.fromarray((np.array(img)+n).clip(0,255).astype('uint8'))  # 轻微噪点防色带
img.save('bg_generated.png',optimize=True)
