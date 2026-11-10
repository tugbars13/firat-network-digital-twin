import csv, matplotlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
rows=list(csv.DictReader(open(ROOT/'data'/'topoloji.csv',encoding='utf-8')))
P={r['kod']:(float(r['boylam']),float(r['enlem'])) for r in rows}
C={'Batı':'#7F77DD','Orta':'#1D9E75','Doğu':'#D85A30','Çekirdek':'#222'}
fig,ax=plt.subplots(figsize=(11,10.5),dpi=150)
for x in (39.192,39.199): ax.axvline(x,color='#bbb',ls=':',lw=1)
for r in rows:
    k=r['kod']
    for col,ls,lw in (('birincil','-',1.6),('yedek','--',1.2)):
        v=r[col]
        if '-DS01' in v:
            d=v.split('-')[0]; (x1,y1),(x2,y2)=P[k],P[d]
            ax.plot([x1,x2],[y1,y2],ls=ls,lw=lw,color='#e3a23b' if ls=='--' else '#888',zorder=1)
for d in ('MUH','TEK','REK'):
    (x1,y1),(x2,y2)=P[d],P['BIDB'];ax.plot([x1,x2],[y1,y2],color='#222',lw=3,zorder=1)
OFF={'BIDB':(8,-14),'REK':(-34,8),'SUR':(8,0),'IIBF':(8,4),'SAG':(8,-6),'EGT':(-30,-12),'AKM':(8,-10)}
for r in rows:
    k=r['kod'];x,y=P[k];big=k in('MUH','TEK','REK','BIDB')
    ax.scatter(x,y,s=300 if k=='BIDB' else 220 if big else 90,marker='s' if big else 'o',color=C[r['bolge']],edgecolor='white',lw=1.5,zorder=3)
    ax.annotate(k,(x,y),xytext=OFF.get(k,(7,5)),textcoords='offset points',fontsize=10,weight='bold' if big else 'normal')
for x,t,c in ((39.1880,'BATI\nMühendislik Yerleşkesi','Batı'),(39.1930,'ORTA\nRektörlük Yerleşkesi','Orta'),(39.2000,'DOĞU\nRektörlük Yerleşkesi','Doğu')):
    ax.text(x,38.6868,t,color=C[c],fontsize=10.5,weight='bold',va='bottom')
ax.legend(handles=[Line2D([],[],color='#222',lw=3,label='Dağıtım → çekirdek (2 × 40 Gbps: CS01 ve CS02)'),Line2D([],[],color='#888',lw=1.6,label='Birincil hat (10 Gbps)'),Line2D([],[],color='#e3a23b',ls='--',lw=1.2,label='Yedek hat'),Line2D([],[],marker='s',ls='',color='#555',ms=11,label='Dağıtım / çekirdek (BIDB)'),Line2D([],[],marker='o',ls='',color='#555',ms=8,label='Bina (erişim)')],loc='lower right',fontsize=9)
ax.set_title('Fırat Üniversitesi Kampüs Ağı — Mantıksal Topoloji\n(gerçek bina konumları üzerinde)',fontsize=13,weight='bold')
ax.set_xlabel('Boylam');ax.set_ylabel('Enlem');ax.set_aspect(1.28)
ax.grid(alpha=.15);ax.set_ylim(38.6715,38.688);ax.set_xlim(39.1875,39.2058)
plt.tight_layout();plt.savefig(ROOT/'docs'/'diagrams'/'topoloji-harita.png')
