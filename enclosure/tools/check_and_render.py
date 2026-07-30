import numpy as np, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def read_stl(path):
    with open(path,'rb') as f: head=f.read(84); n=int.from_bytes(head[80:84],'little')
    data=np.fromfile(path,dtype=np.uint8,offset=84)
    rec=50; n=min(n, len(data)//rec)
    d=data[:n*rec].reshape(n,rec)
    tris=np.frombuffer(d[:,12:48].tobytes(),dtype='<f4').reshape(n,3,3)
    return tris

def manifold_report(tris):
    v=tris.reshape(-1,3)
    q=np.round(v,4)
    _,idx=np.unique(q,axis=0,return_inverse=True)
    f=idx.reshape(-1,3)
    e=np.vstack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]])
    e=np.sort(e,axis=1)
    _,cnt=np.unique(e,axis=0,return_counts=True)
    return len(f), int((cnt!=2).sum())

def render(tris, path, title, views):
    fig=plt.figure(figsize=(5.2*len(views),5.4), facecolor='#14100e')
    ctr=tris.reshape(-1,3).mean(axis=0)
    rng=(tris.reshape(-1,3).max(axis=0)-tris.reshape(-1,3).min(axis=0)).max()/2*1.15
    for i,(el,az,lbl) in enumerate(views):
        ax=fig.add_subplot(1,len(views),i+1,projection='3d',facecolor='#14100e')
        n=np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
        ln=np.linalg.norm(n,axis=1); ln[ln==0]=1; n=n/ln[:,None]
        light=np.array([0.35,-0.55,0.76]); sh=np.clip(n@light,0,1)*0.72+0.28
        cols=np.stack([sh*1.00, sh*0.55, sh*0.20],axis=1)  # ember-orange shading
        pc=Poly3DCollection(tris, facecolors=cols, edgecolors='none')
        ax.add_collection3d(pc)
        for s,c in (('set_xlim',0),('set_ylim',1),('set_zlim',2)):
            getattr(ax,s)(ctr[c]-rng, ctr[c]+rng)
        ax.set_box_aspect((1,1,1)); ax.view_init(elev=el,azim=az)
        ax.set_axis_off(); ax.set_title(lbl,color='#e8a24a',fontsize=11)
    fig.suptitle(title,color='#f5e9dc',fontsize=13)
    fig.tight_layout(); fig.savefig(path,dpi=98,facecolor='#14100e'); plt.close(fig)

print("=== MESH VALIDITY ===")
for f in sorted(os.listdir('.')):
    if f.endswith('.stl'):
        t=read_stl(f); nf,bad=manifold_report(t)
        print(f"  {f:26s} {nf:6d} tris   non-manifold edges: {bad}   "
              f"{'WATERTIGHT' if bad==0 else '*** LEAK ***'}")

VIEWS_FRONT=[(24,-62,'front 3/4'),(88,-90,'face on'),(-18,-62,'underside')]
VIEWS_BACK =[(20,118,'back 3/4'),(-86,-90,'back face'),(6,-178,'bottom edge')]
render(read_stl('ember-front-bezel.stl'),'preview-bezel.png',
       'ember-front-bezel',VIEWS_FRONT)
render(read_stl('ember-back-shell.stl'),'preview-shell.png',
       'ember-back-shell',VIEWS_BACK)
render(read_stl('ember-stand.stl'),'preview-stand.png','ember-stand',
       [(18,-56,'front 3/4'),(4,-90,'front face'),(16,120,'back 3/4')])
print("rendered previews")
