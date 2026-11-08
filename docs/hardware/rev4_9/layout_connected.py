import re
"""Functional schematic layout; electrical model remains unchanged.
Executed inside build_rev4_9.py. Every terminal and routed conductor has a net.
Also records symbol artwork/units and routes for the native KiCad exporter.
"""
PINPOS={};INSTANCES=[];ROUTES=[];PORTS=[];DECOR=[];ACTIVE=None;CURRENT_SHEET=0;IN_DRAW=False
original_ln=ln;original_txt=txt;original_circle=circle

def ln(x,y,X,Y,color=NAVY,w=.6):
 original_ln(x,y,X,Y,color,w)
 if ACTIVE is not None:ACTIVE['art'].append({'kind':'line','points':[[x,y],[X,Y]],'width':w})
 elif IN_DRAW:DECOR.append({'sheet':CURRENT_SHEET,'kind':'line','points':[[x,y],[X,Y]],'width':w})
def txt(x,y,s,size=7,color=BLACK,font='T',align='left'):
 original_txt(x,y,s,size,color,font,align)
 if ACTIVE is not None:ACTIVE['art'].append({'kind':'text','at':[x,y],'text':str(s),'size':size,'align':align})
 elif IN_DRAW:DECOR.append({'sheet':CURRENT_SHEET,'kind':'text','at':[x,y],'text':str(s),'size':size,'align':align})
def circle(x,y,r=.95):
 original_circle(x,y,r)
 if ACTIVE is not None:ACTIVE['art'].append({'kind':'circle','at':[x,y],'radius':r})
def start(ref,unit=1):
 global ACTIVE
 assert ACTIVE is None
 ACTIVE={'ref':ref,'unit':unit,'sheet':CURRENT_SHEET,'pins':{},'art':[]};rendered.add(ref)
def finish():
 global ACTIVE
 INSTANCES.append(ACTIVE);ACTIVE=None

def pin(ref,p,x,y):
 p=str(p);key=(ref,p)
 assert key not in PINPOS,key
 assert x%5==0 and y%5==0,(key,x,y)
 PINPOS[key]=(x,y);terminal_rendered.add(key)
 ACTIVE['pins'][p]=[x,y]
def ppos(ref,p):return PINPOS[(ref,str(p))]
def pnet(ref,p):return byref[ref]['pins'][str(p)]
def route(net,pts):
 assert net is not None
 for a,b in zip(pts,pts[1:]):
  assert a[0]==b[0] or a[1]==b[1],pts
  original_ln(*a,*b)
 ROUTES.append({'sheet':CURRENT_SHEET,'net':net,'points':[list(v) for v in pts]})
def link(a,b,*bends):
 assert pnet(*a)==pnet(*b),(a,b,pnet(*a),pnet(*b))
 route(pnet(*a),[ppos(*a),*bends,ppos(*b)])
def frompin(ref,p,*pts):route(pnet(ref,p),[ppos(ref,p),*pts])
def dotat(x,y):
 cv.setFillColor(NAVY);cv.circle(x,595-y,1.35,stroke=0,fill=1)
 DECOR.append({'sheet':CURRENT_SHEET,'kind':'junction','at':[x,y]})
def dotpin(ref,p):dotat(*ppos(ref,p))
def gndat(x,y):
 ln(x,y,x,y+4,MAROON)
 for d,w in [(4,4),(6,2.8),(8,1.4)]:ln(x-w,y+d,x+w,y+d,MAROON)
 txt(x,y+18,'GND',6.5,MAROON,align='center')
 PORTS.append({'sheet':CURRENT_SHEET,'net':'GND','at':[x,y],'kind':'ground'})
def ground(ref,p,at=None):
 assert pnet(ref,p)=='GND',(ref,p)
 xy=ppos(ref,p)
 if at:
  route('GND',[xy,at]);xy=at
 gndat(*xy)
def net_pages(net):
 pages=set()
 for a in components:
  for p,n in a['pins'].items():
   if n!=net:continue
   sh=a['sheet']
   if a['ref']=='U1':sh=7 if p in ('4','8') else 2 if p in ('1','2','3') else 4
   if a['ref']=='U3' and p in ('4','8'):sh=7
   pages.add(sh)
 return pages

def netport(ref,p,at=None,side='left',display=None,power=False,power_down=False):
 net=pnet(ref,p);xy=ppos(ref,p)
 if at:route(net,[xy,at]);xy=at
 x,y=xy
 label=re.sub(r' \(F[1-7]\)','',display or net)
 if not power:
  others=sorted(net_pages(net)-{CURRENT_SHEET})
  if others:label+='  [F'+', F'.join(map(str,others))+']'
 if power:
  down=power_down;d=1 if down else -1
  ln(x,y,x,y+5*d,MAROON);ln(x-4,y+5*d,x+4,y+5*d,MAROON)
  txt(x,y+16 if down else y-10,label,7,MAROON,align='center')
 else:
  align='right' if side=='left' else 'left';tx=x-3 if side=='left' else x+3
  txt(tx,y-5,label,7,MAROON,align=align)
  width=pdfmetrics.stringWidth(label,'T',7)
  ln(tx-width if side=='left' else tx,y-3,tx if side=='left' else tx+width,y-3,MAROON,.35)
 PORTS.append({'sheet':CURRENT_SHEET,'net':net,'at':[x,y],'kind':'power' if power else 'net'})
def nc(ref,p):
 assert pnet(ref,p) is None
 x,y=ppos(ref,p);ln(x-2,y-2,x+2,y+2,BLUE);ln(x-2,y+2,x+2,y-2,BLUE)
 PORTS.append({'sheet':CURRENT_SHEET,'net':None,'ref':ref,'pin':str(p),'at':[x,y],'kind':'nc'})
def block(x,y,w,h,title,subtitle=None):
 # Match the approved pre-conditioning schematic: open sections, no cards.
 title=re.sub(r'^[1-7](?=[A-Z]  )',str(CURRENT_SHEET),title)
 txt(x+12,y+18,title,9,NAVY,'HB')
 if subtitle:txt(x+12,y+31,subtitle,6.6,'#404040')
def element(ref,a,b,labels=True):
 c=byref[ref];k=c['kind'];assert len(c['pins'])==2,ref
 assert a[0]==b[0] or a[1]==b[1]
 start(ref);pin(ref,'1',*a);pin(ref,'2',*b)
 dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);ux=dx/length;uy=dy/length
 cx=(a[0]+b[0])/2;cy=(a[1]+b[1])/2
 def pt(s,t=0):return (cx+ux*s-uy*t,cy+uy*s+ux*t)
 def seg(s,t,S,T):ln(*pt(s,t),*pt(S,T),BLUE)
 ln(*a,*pt(-5));ln(*pt(5),*b)
 if k=='F':
  poly([pt(-5,-3),pt(5,-3),pt(5,3),pt(-5,3),pt(-5,-3)]);seg(-5,0,5,0)
 elif k=='R':poly([pt(s,t) for s,t in [(-5,0),(-4,-2),(-2.4,2),(-.8,-2),(.8,2),(2.4,-2),(4,2),(5,0)]])
 elif k in ('C','CP','CB'):
  seg(-2,-5,-2,5);seg(-5,0,-2,0)
  if k=='CP':
   # Negative plate bows toward the straight positive plate.
   pts=[pt(3,-5),pt(1.7,-3),pt(1,-1.5),pt(.8,0),pt(1,1.5),pt(1.7,3),pt(3,5)]
   poly(pts);seg(.8,0,5,0)
   px,py=pt(-8,-8);txt(px,py,'+',7,BLUE,align='center')
   px,py=pt(8,-8);txt(px,py,'-',7,BLUE,align='center')
  else:seg(2,-5,2,5);seg(2,0,5,0)
 elif k in ('D','LED'):
  shape=cv.beginPath();verts=[pt(-3,-3),pt(-3,3),pt(3,0)]
  shape.moveTo(verts[0][0],595-verts[0][1])
  for vx,vy in verts[1:]:shape.lineTo(vx,595-vy)
  shape.close();cv.setFillColor(BLUE);cv.drawPath(shape,fill=1,stroke=0)
  ACTIVE['art'].append({'kind':'polygon','points':[list(v) for v in verts]})
  poly([pt(-3,-3),pt(-3,3),pt(3,0),pt(-3,-3)]);seg(3,-4,3,4);seg(-5,0,-3,0);seg(3,0,5,0)
  if k=='LED':
   for s,t in [(0,-6),(5,-4)]:
    poly([pt(s,t),pt(s+4,t-4)]);poly([pt(s+2,t-4),pt(s+4,t-4),pt(s+4,t-2)])
 marker=''
 if labels:
  if uy==0:
   txt(cx,cy-13,ref+marker,8,NAVY,align='center');txt(cx,cy+17,c['value'] if k!='LED' else 'LED',7,NAVY,align='center')
  else:
   txt(cx+11,cy-3,ref+marker,8,NAVY);txt(cx+11,cy+10,c['value'],7,NAVY)
 finish()

def opunit(ref,unit,x,y):
 # All electrical terminals are on a 5 pt lattice for native CAD connectivity.
 u=1 if unit=='A' else 2;start(ref,u)
 pn,pp,po=('2','3','1') if u==1 else ('6','5','7')
 pin(ref,pn,x-40,y-10);pin(ref,pp,x-40,y+10);pin(ref,po,x+40,y)
 cv.setFillColor('#FFFFB0');cv.setStrokeColor(BLUE)
 pp_=cv.beginPath();pp_.moveTo(x-15,595-y+22);pp_.lineTo(x-15,595-y-22);pp_.lineTo(x+20,595-y);pp_.close();cv.drawPath(pp_,fill=1,stroke=0)
 poly([(x-15,y-22),(x-15,y+22),(x+20,y),(x-15,y-22)])
 ln(x-40,y-10,x-15,y-10,BLACK);ln(x-40,y+10,x-15,y+10,BLACK);ln(x+20,y,x+40,y,BLACK)
 txt(x-11,y-7,'-',8);txt(x-11,y+13,'+',8)
 for p,xx,yy in [(pn,x-30,y-14),(pp,x-30,y+6),(po,x+27,y-4)]:txt(xx,yy,p,6,align='center')
 txt(x-85 if ref=='U3' else x,y-10 if ref=='U3' else y-30,ref+unit,8,NAVY,align='center')
 txt(x,y+34,'TL072',7,BLACK,align='center');finish()

def powerunit(ref,x,y):
 start(ref,3)
 cv.setFillColor('#FFFFB0');cv.setStrokeColor(MAROON);cv.setLineWidth(.6)
 cv.rect(x-20,595-y-38,75,28,fill=1,stroke=1)
 ACTIVE['art'].append({'kind':'rect','rect':[x-20,y+10,75,28]})
 for p,yy,end in [('8',y,y+10),('4',y+50,y+38)]:
  pin(ref,p,x,yy);ln(x,yy,x,end,BLACK);txt(x+5,(yy+end)/2+2,p,6)
 txt(x+17,y+22,ref+' · alimentação',7,NAVY,align='center')
 txt(x+17,y+33,'TL072',6.5,BLACK,align='center');finish()
 netport(ref,'8',power=True);netport(ref,'4',power=True,power_down=True)

def device(ref,rect_,rows):
 """Rows: (physical pin, side, absolute endpoint x/y, display name)."""
 x,y,w,h=rect_;start(ref)
 cv.setFillColor('#FFFFB0');cv.setStrokeColor(MAROON);cv.setLineWidth(.6);cv.rect(x,595-y-h,w,h,fill=1,stroke=1)
 ACTIVE['art'].append({'kind':'rect','rect':[x,y,w,h]})
 if ref.startswith('J'):
  txt(x+w/2,y+13,ref,8,NAVY,align='center')
 else:
  txt(x+w/2,y+18 if ref=='U4' else y-15,ref,8,NAVY,align='center')
  txt(x+w/2,y+30 if ref=='U4' else y-5,byref[ref]['value'],7,BLACK,align='center')
 for p,side,px,py,name in rows:
  pin(ref,p,px,py);xx=x if side=='L' else x+w
  ln(px,py,xx,py,BLACK)
  txt((px+xx)/2,py-4,p,5.8,align='center')
  txt(xx+4 if side=='L' else xx-4,py+2,name,6.7,BLACK,align='left' if side=='L' else 'right')
 finish()

def jack(ref,x,y,name):
 # Functional tip/sleeve contacts, to be identified by continuity on the real jack.
 device(ref,(x-55,y-20,40,65),[('1','R',x,y,'TIP' if ref!='J1' else '+'),('2','R',x,y+35,'GND')])
 txt(x-35,y+56,name,7,BLACK,align='center')

def switch(ref,x,y):
 start(ref)
 for p,xx,yy in [('C',x-30,y),('1',x+30,y),('2',x+30,y-15)]:pin(ref,p,xx,yy)
 ln(x-30,y,x-5,y);ln(x+5,y,x+30,y);ln(x+5,y-15,x+30,y-15)
 for xx,yy in [(x-5,y),(x+5,y),(x+5,y-15)]:circle(xx,yy,1.15)
 ln(x-4,y-1,x+4,y-10,BLUE)
 txt(x,y-29,ref,8,NAVY,align='center')
 txt(x,y+27,'MTS-102',7,BLACK,align='center')
 for p,xx,yy in [('C',x-21,y+9),('1',x+21,y+9),('2',x+21,y-19)]:txt(xx,yy,p,5.8)
 finish();nc(ref,'2')


def testpoint(ref,x,y,side='above'):
 start(ref);pin(ref,'1',x,y);circle(x,y,2)
 if side=='right':txt(x+7,y-2,ref,7,NAVY)
 elif side=='below':txt(x,y+17,ref,7,NAVY,align='center')
 else:txt(x,y-12,ref,7,NAVY,align='center')
 finish()

def page1():
 block(40,65,760,190,'1A  Fonte única e proteção → CW7805 → distribuição de 5 V','12 V regulados · GND comum · sem fonte negativa · confirmar CW antes de montar')
 jack('J1',100,135,'12 V / 1,5 A')
 element('F1',(120,135),(170,135));link(('J1','1'),('F1','1'))
 element('D1',(200,135),(250,135));link(('F1','2'),('D1','1'));ground('J1','2',(115,170))
 element('C33',(285,135),(285,205));link(('D1','2'),('C33','1'));ground('C33','2',(285,225))
 device('U5',(450,110,100,70),[('1','L',420,135,'IN'),('3','R',580,135,'OUT'),('2','L',420,170,'GND / TAB')])
 element('C21',(380,135),(380,205));link(('C33','1'),('C21','1'));link(('C21','1'),('U5','1'));ground('C21','2');ground('U5','2',(420,205))
 element('C22',(620,135),(620,205));element('R21',(690,135),(690,205));element('C37',(755,135),(755,205))
 link(('U5','3'),('C22','1'));link(('C22','1'),('R21','1'));link(('R21','1'),('C37','1'));netport('C37','1',(785,135),power=True)
 for r in ('C22','R21','C37'):ground(r,'2')
 element('D8',(580,260),(420,260));frompin('D8','1',(600,260),(600,135));frompin('D8','2',(360,260),(360,135))
 txt(495,293,'D8: descarga reversa de OUT para IN.',7,BLACK,align='center')
 netport('C33','1',(330,135),power=True);testpoint('TP1',330,135,'below');testpoint('TP2',660,135);testpoint('TP10',285,225,'right')
 block(40,295,340,170,'1B  Referência dos amplificadores','VREF_OP ≈ +RAW / 2 · aguardar pelo menos 5 s')
 element('R22',(125,350),(125,390));element('R23',(125,390),(125,450));netport('R22','1',power=True);link(('R22','2'),('R23','1'));ground('R23','2')
 element('C38',(220,390),(220,450));element('C39',(300,390),(300,450));link(('R23','1'),('C38','1'));link(('C38','1'),('C39','1'));ground('C38','2');ground('C39','2')
 netport('C39','1',(350,390),side='right');testpoint('TP4',350,390)
 block(430,295,370,170,'1C  Referência independente do ADC','ADC_BIAS = 0,48 × +5V · não carregar a saída VCOM')
 element('R27',(500,350),(500,390));element('R28',(500,390),(500,450));netport('R27','1',power=True);link(('R27','2'),('R28','1'));ground('R28','2')
 element('C40',(600,390),(600,450));element('C41',(700,390),(700,450));link(('R28','1'),('C40','1'));link(('C40','1'),('C41','1'));ground('C40','2');ground('C41','2')
 netport('C41','1',(770,390));testpoint('TP11',650,390)

def page2():
 block(40,65,260,225,'2A  Guitarra, buffer e proteção','Sinal nominal ≤0,5 V de pico · Zin ≈ 1 MΩ')
 jack('J2',100,175,'ENTRADA P10')
 element('C1',(110,175),(140,175));element('R26',(145,175),(175,175));link(('J2','1'),('C1','1'));link(('C1','2'),('R26','1'));ground('J2','2',(110,210))
 opunit('U1','A',220,165);link(('R26','2'),('U1','3'));link(('U1','1'),('U1','2'),(285,165),(285,125),(175,125),(175,155))
 element('R3',(125,205),(125,270));element('D6',(190,205),(190,235));element('D13',(190,235),(190,270));element('D7',(255,270),(255,235));element('D14',(255,235),(255,205));link(('D6','2'),('D13','1'));link(('D7','2'),('D14','1'))
 frompin('R26','2',(175,205),(125,205));link(('R3','1'),('D6','1'));link(('D6','1'),('D14','2'))
 link(('R3','2'),('D13','2'));link(('D13','2'),('D7','1'));netport('R3','2',(125,290),power=True,power_down=True)
 block(310,65,485,400,'2B  Driver diferencial e acoplamento ao codec','U3A = +1 · U3B = -1 · VREF_OP isolado de ADC_BIAS')
 opunit('U3','A',470,165);opunit('U3','B',470,375)
 link(('U1','1'),('U3','3'),(340,165),(340,175));testpoint('TP6',315,165)
 element('R24',(300,365),(360,365));frompin('U1','1',(300,165),(300,365));link(('R24','2'),('U3','6'))
 netport('U3','5',(395,385),power=True)
 for rf,cc,rs,pn,po,fb_y,cf_y,out_y in [('R17','C18','R18','2','1',115,145,165),('R19','C19','R20','6','7',315,345,375)]:
  element(rf,(430,fb_y),(490,fb_y));element(cc,(470,cf_y),(530,cf_y),labels=False);txt(500,cf_y-13,cc,8,NAVY,align='center');txt(560,cf_y-3,byref[cc]['value'],6.5,NAVY);element(rs,(550,out_y),(610,out_y))
  link(('U3',pn),(rf,'1'));link((rf,'1'),(cc,'1'),(430,cf_y));link(('U3',po),(rs,'1'));link((cc,'2'),(rs,'1'),(530,out_y));link((rf,'2'),(rs,'1'),(550,fb_y))
 element('C2',(635,165),(685,165));element('C16',(635,375),(685,375));link(('R18','2'),('C2','1'));link(('R20','2'),('C16','1'))
 element('R15',(700,165),(700,225));element('R16',(700,375),(700,435));link(('C2','2'),('R15','1'));link(('C16','2'),('R16','1'));netport('R15','2',side='right');netport('R16','2',side='right')
 element('C20',(735,165),(735,375));link(('R15','1'),('C20','1'));link(('R16','1'),('C20','2'))
 netport('C20','1',(755,165),side='right');netport('C20','2',(755,375),side='right');testpoint('TP7',720,165);testpoint('TP8',720,375)
 # Matched common-mode RF capacitors below each bias resistor.
 element('C35',(620,235),(620,275));netport('C35','1',(440,235),display='AINA_P');ground('C35','2')
 element('C36',(620,435),(620,475));netport('C36','1',(440,435),display='AINA_N');ground('C36','2')
 for high,low,cap,y in [('D9','D10','C35',235),('D11','D12','C36',435)]:
  element(high,(500,y),(500,y-30));element(low,(540,y+40),(540,y));link((high,'1'),(cap,'1'));link((low,'2'),(high,'1'));netport(high,'2',power=True);ground(low,'1')
 txt(52,335,'Clamps: dois diodos em série por sentido.',7)
 txt(52,350,'Não são uma proteção contra surtos de rede.',7)
 txt(52,412,'U1/U3: alimentação e bypass na F7.',7)

def page3():
 block(40,65,305,410,'3A  Codec físico TSSOP-28')
 L=[('3',135,'MCLK'),('4',155,'LRCK'),('5',175,'SCLK'),('7',195,'SDIN'),('6',215,'SDOUT'),('11',250,'SCL / CCLK'),('12',270,'SDA / CDIN'),('14',290,'/RST'),('13',320,'AD0 / CS'),('2',340,'XTI'),('1',365,'XTO'),('8',425,'DGND'),('21',445,'AGND')]
 R=[('20',130,'VA'),('9',150,'VD'),('10',170,'VL'),('15',200,'VCOM'),('22',230,'FILT+'),('17',270,'AINA+'),('16',290,'AINA-'),('18',320,'AINB+'),('19',340,'AINB-'),('25',370,'AOUTA+'),('24',390,'AOUTA-'),('26',410,'AOUTB+'),('27',425,'AOUTB-'),('23',440,'AMUTEC'),('28',455,'BMUTEC')]
 device('U2',(140,110,145,355),[(p,'L',110,y,n) for p,y,n in L]+[(p,'R',315,y,n) for p,y,n in R])
 for p in ['3','4','5','7','6','11','12','14']:netport('U2',p)
 link(('U2','13'),('U2','2'),(80,320),(80,340));ground('U2','2',(80,340));nc('U2','1')
 link(('U2','8'),('U2','21'),(85,425),(85,445));ground('U2','21',(85,445))
 netport('U2','20',(355,130),power=True);link(('U2','9'),('U2','10'),(365,150),(365,170));netport('U2','9',(400,150),power=True);dotat(365,150)
 for p in ['17','16','25','24']:netport('U2',p,side='right')
 for p in ['26','27','23','28']:nc('U2',p)
 block(375,65,425,230,'3B  Referências e filtros locais','VCOM: bias de alta impedância · FILT+: referência interna')
 element('C12',(435,230),(435,275));element('C13',(505,230),(505,275));link(('U2','22'),('C12','1'));link(('C12','1'),('C13','1'));dotpin('C12','1')
 link(('C12','2'),('C13','2'));ground('C13','2');txt(470,210,'FILT+',7,MAROON,align='center')
 element('C14',(635,200),(635,275));element('C15',(715,200),(715,275));link(('U2','15'),('C14','1'));link(('C14','1'),('C15','1'));dotpin('C14','1')
 link(('C14','2'),('C15','2'));ground('C15','2');netport('C14','1',side='right',display='VCOM');testpoint('TP5',675,200)
 block(375,305,425,170,'3C  Canal ADC B não utilizado','As duas entradas ficam no mesmo bias; saídas DAC B em NC.')
 link(('U2','18'),('U2','19'),(365,320),(365,340));dotat(365,340)
 element('R10',(505,385),(445,385));frompin('U2','19',(365,340),(365,355),(420,355),(420,385),(445,385));netport('R10','1',(545,385),side='right',display='ADC_BIAS')
 element('C34',(650,420),(650,455));frompin('R10','2',(420,385),(420,420),(650,420));ground('C34','2');dotat(420,385)
 txt(425,460,'Canal B mutado na configuração do codec.',7)


def page4():
 block(40,65,760,255,'2A  Receptor diferencial do DAC','AOUTA+/- da F3 → receptor polarizado em VREF_OP → ganho 0,499')
 element('C11',(95,145),(155,145));netport('C11','1',(85,145),display='AOUTA_N')
 element('R7',(195,145),(255,145));link(('C11','2'),('R7','1'))
 element('C10',(95,245),(155,245));netport('C10','1',(85,245),display='AOUTA_P')
 element('R1',(195,245),(255,245));link(('C10','2'),('R1','1'))
 opunit('U1','B',390,200)
 link(('R7','2'),('U1','6'),(310,145),(310,190))
 link(('R1','2'),('U1','5'),(280,245),(280,210));dotat(280,245)
 element('R2',(280,245),(280,290));netport('R2','2',power=True,power_down=True)
 element('R8',(320,115),(380,115));link(('R8','1'),('U1','6'),(310,115),(310,190));dotat(310,190);dotat(310,145)
 link(('R8','2'),('U1','7'),(465,115),(465,200));dotat(465,200)
 netport('U1','7',(540,200),side='right',display='DAC_BUF');testpoint('TP9',505,200)
 txt(585,150,'R1/R7 = 100 kΩ; R2/R8 = 49,9 kΩ',8)
 txt(585,166,'Preferir casamento de 0,1%.',7)
 txt(585,190,'Ganho diferencial = 0,499.',7)
 txt(585,216,'U1 pinos 8/4: alimentação na F7.',7)
 block(40,345,760,130,'2B  Filtro e saída de áudio','DAC_BUF de 4A → filtro RC → acoplamento → saída P10')
 element('R4',(95,400),(155,400));netport('R4','1',(85,400),display='DAC_BUF')
 element('C4',(200,400),(200,445));link(('R4','2'),('C4','1'));ground('C4','2');dotpin('C4','1')
 element('R5',(265,400),(325,400));link(('C4','1'),('R5','1'))
 element('C6',(370,400),(370,445));link(('R5','2'),('C6','1'));ground('C6','2');dotpin('C6','1')
 element('C5',(470,400),(530,400));link(('C6','1'),('C5','1'))
 element('R6',(590,400),(590,445));link(('C5','2'),('R6','1'));dotpin('R6','1');ground('R6','2')
 # Output jack faces the incoming signal.
 device('J3',(710,385,65,60),[('1','L',680,400,'TIP'),('2','L',680,435,'GND')]);link(('R6','1'),('J3','1'));ground('J3','2',(660,435))
 txt(743,457,'SAÍDA P10',7,BLACK,align='center')


def page5():
 block(40,65,505,410,'4A  STM32H723 WeAct V1.2','À esquerda: codec (F3) · à direita: ESP32 e controles (F6)')
 left=[('P1.4',130),('P2.5',155),('P2.6',180),('P2.7',205),('P2.17',230),('P1.6',270),('P1.5',295),('P1.38',330),('P1.2',390),('P2.2',415),('P1.1',445)]
 right=[('P1.40',130),('P1.39',155),('P2.11',205),('P2.12',230),('P2.13',255),('P2.14',280),('P2.30',315),('P2.31',340),('P2.32',365),('P2.38',390)]
 a=byref['H_STM32']
 device('H_STM32',(300,110,155,345),[(p,'L',270,y,a['names'][p]) for p,y in left]+[(p,'R',485,y,a['names'][p]) for p,y in right])
 for p,y in left[:8]:netport('H_STM32',p,(165,y),display=pnet('H_STM32',p)+' (F3)')
 for p,y in right[2:]:netport('H_STM32',p,side='right')
 device('J4',(70,370,55,65),[('1','R',145,390,'5V IN'),('2','R',145,420,'GND')]);link(('J4','1'),('H_STM32','P1.2'));ground('J4','2',(165,420));netport('J4','1',(190,390),power=True)
 txt(97,452,'5 V da F1 · sem USB',7,BLACK,align='center')
 netport('H_STM32','P2.2',(220,415),power=True);testpoint('TP3',245,415);ground('H_STM32','P1.1',(220,445))
 block(565,65,235,195,'4B  Comunicação ESP32','UART: full-duplex · 115200, 8N1')
 device('H_ESP32',(660,115,110,105),[('RX2','L',630,130,'GPIO16 RX2'),('TX2','L',630,155,'GPIO17 TX2'),('VIN','L',630,180,'VIN / 5V'),('GND','L',630,205,'GND')])
 link(('H_STM32','P1.40'),('H_ESP32','RX2'));link(('H_STM32','P1.39'),('H_ESP32','TX2'))
 txt(555,122,'TX',6,BLACK);txt(555,148,'RX',6,BLACK)
 netport('H_ESP32','VIN',(595,180),power=True);ground('H_ESP32','GND',(605,205))
 block(565,280,235,195,'4C  Polarização das interfaces')
 element('R11',(625,325),(625,370));element('R12',(735,325),(735,370));link(('R11','1'),('R12','1'));netport('R11','1',(680,325),power=True)
 netport('R11','2',side='right',display='I2C_SCL');netport('R12','2',side='right',display='I2C_SDA')
 element('R13',(625,415),(625,450));element('R14',(735,415),(735,450));netport('R13','1',display='CODEC_RST');netport('R14','1',display='ADC_DATA');ground('R13','2');ground('R14','2')


def page6():
 block(40,65,350,410,'5A  Chaves com retenção','Controles para o STM32 (F5) · fechado = LOW')
 block(420,65,380,410,'5B  Indicadores','Saídas do STM32 (F5) · resistor → LED → GND')
 for i,(sw,d,net,gpio) in enumerate([('SW1','D2','LED_OD','PE7'),('SW2','D3','LED_EQ','PE8'),('SW3','D4','LED_DLY','PE9'),('SW4','D5','LED_STAT','PE15')]):
  y=145+i*85;switch(sw,220,y);netport(sw,'C',(95,y),display=pnet(sw,'C')+' (F4)');ground(sw,'1',(325,y))
  txt(65,y+25,['PC0','PC1','PC2_C','PC3_C'][i],7,BLACK)
  txt(52,y-27,byref[d]['function'],8,BLACK)
  element('R_'+d,(495,y),(555,y));netport('R_'+d,'1',(470,y),display=net+' (F4)')
  element(d,(625,y),(685,y));link(('R_'+d,'2'),(d,'1'));ground(d,'2',(750,y))
  txt(465,y+25,gpio,7,BLACK)


def page7():
 block(40,65,760,200,'7A  Desacoplamento local do CS4272','Um par junto de cada domínio; não colocar no extremo oposto da perfboard')
 for r1,r2,x,caption in [('C23','C24',125,'VA · U2 pino 20'),('C25','C26',355,'VD · U2 pino 9'),('C27','C28',585,'VL · U2 pino 10')]:
  element(r1,(x,145),(x,220));element(r2,(x+65,145),(x+65,220));link((r1,'1'),(r2,'1'));netport(r1,'1',(x+30,145),power=True)
  link((r1,'2'),(r2,'2'));ground(r2,'2',(x+30,220));txt(x+30,260,caption,7,BLACK,align='center')
 block(40,290,460,180,'7B  Desacoplamento dos dois TL072','470 µF em VREF_OP na F1; não confundir com alimentação')
 for ra,rb,x,caption in [('C29','C30',100,'U1: próximo aos pinos 8/4'),('C31','C32',320,'U3: próximo aos pinos 8/4')]:
  element(ra,(x,365),(x,430));element(rb,(x+70,365),(x+70,430));link((ra,'1'),(rb,'1'));netport(ra,'1',(x+35,365),power=True)
  link((ra,'2'),(rb,'2'));ground(rb,'2',(x+35,430));txt(x+35,472,caption,7,BLACK,align='center')
 block(520,290,275,180,'7C  Unidades de alimentação')
 powerunit('U1',640,335);powerunit('U3',755,335)

def mark_all_junctions():
 # Dots follow actual graph branches, including a component pin on a rail.
 seg=[];points=set();pins=set()
 for a in INSTANCES:
  if a['sheet']==CURRENT_SHEET:pins.update(tuple(v) for v in a['pins'].values())
 points.update(pins)
 for r in ROUTES:
  if r['sheet']!=CURRENT_SHEET:continue
  for a,b in zip(r['points'],r['points'][1:]):
   a=tuple(a);b=tuple(b)
   if a!=b:seg.append((a,b));points.update([a,b])
 adj=defaultdict(set)
 for a,b in seg:
  pts=sorted(p for p in points if min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1]))
  for c,d in zip(pts,pts[1:]):adj[c].add(d);adj[d].add(c)
 for pt,neighbors in adj.items():
  if len(neighbors)+(pt in pins)>=3:dotat(*pt)

def draw_sheet(n):
 global CURRENT_SHEET,IN_DRAW
 CURRENT_SHEET=n;IN_DRAW=True
 globals()['page'+str(n)]()
 mark_all_junctions()
 IN_DRAW=False

# Serialize a fully routed drawing, independently reusable by the CAD exporter.
def save_connected_layout():
 (OUT/'diagram_layout.json').write_text(json.dumps({'version':1,'pages':PAGES,'instances':INSTANCES,'routes':ROUTES,'ports':PORTS,'decorations':DECOR},ensure_ascii=False,indent=2))
