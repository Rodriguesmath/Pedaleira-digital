#!/usr/bin/env python3
"""PDF vetorial A4 paisagem, sem alterar a BOM ou o circuito EasyEDA existente.
Usa o gerador existente como contrato de referencias, valores e conectividade.
"""
from pathlib import Path
import importlib.util
import json
import io
import re
from matplotlib import mathtext, rc_context
from matplotlib.font_manager import FontProperties
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'output/pdf/pedaleira_digital_esquematica.pdf'
FONT_DIR = Path('/home/rodrigues/.local/share/fonts/msttcorefonts')
for name, font in {
    'Sans': FONT_DIR / 'Times.TTF',
    'Bold': FONT_DIR / 'Timesbd.TTF',
    'Reference': FONT_DIR / 'Times.TTF',
    'Net': FONT_DIR / 'Times.TTF',
    'Heading': Path('/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf'),
    'HeadingBold': Path('/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf'),
}.items():
    pdfmetrics.registerFont(TTFont(name, str(font)))
OUT.parent.mkdir(parents=True, exist_ok=True)
PAGE_WIDTH_PT, PAGE_HEIGHT_PT = 842, 595  # Exact MediaBox of the supplied WeAct PDF.
FONT_FACTOR = 1.18
c = canvas.Canvas(str(OUT), pagesize=(PAGE_WIDTH_PT,PAGE_HEIGHT_PT), pageCompression=1)
c.setTitle('Pedaleira Digital - Esquemática de interligação - Revisão documental 4.7')
c.setAuthor('Projeto Pedaleira Digital / Rodriguesmath')
c.setSubject('Circuito existente preservado; folhas A4 e pendências técnicas identificadas')
INK = '#000000'; BLUE = '#000080'; GREY = '#404040'
SYMBOL = '#0000FF'; WIRE = '#000080'
NET_COLOR = '#800000'; REF_COLOR = BLUE
PIN_COLOR = '#000000'; BODY_COLOR = '#800000'; CREAM = '#FFFFB0'; PAPER = '#FFFCF8'
SYMBOL_CONTEXT = False

def ref_color(ref):
    return REF_COLOR


def symbol_style(fn):
    def styled(*args, **kwargs):
        global SYMBOL_CONTEXT
        previous=SYMBOL_CONTEXT
        SYMBOL_CONTEXT=True
        try:
            return fn(*args, **kwargs)
        finally:
            SYMBOL_CONTEXT=previous
    return styled


def fillbox(x,y,w,h,color):
    # Decorative fills only: never change electrical geometry.
    c.setFillColor(color)
    c.rect(x*mm,(297-y-h)*mm,w*mm,h*mm,fill=1,stroke=0)

refs = {}; connections = {}; text_boxes = []
page_no = 0

def text(x,y,s,size=3,bold=False,color=INK,align='left',font=None):
    # Distinct roles: body, section heading, component reference and net name.
    s = str(s)
    size *= FONT_FACTOR
    value_display = {'100k':'100 kΩ', '1M':'1 MΩ', '1k':'1 kΩ', '330R':'330 Ω'}
    s = value_display.get(s, s)
    if re.fullmatch(r'[0-9][0-9,.]* (?:kΩ|MΩ|Ω|nF|µF)(?: · cerâmico)?',s) or s in ('TL072','1N4007'):
        color = BLUE
    is_ref = bool(re.fullmatch(r'(?:[RCDJU]\d+[AB]?|R_D[2-5]|C_IN|H_(?:CODEC|STM32|ESP32))',s))
    mixed = re.fullmatch(r'(SW[1-4]|D[2-5]) · (.+)',s)
    if is_ref and font is None:
        font = 'Reference'; color = ref_color(s); size = max(size,3.25)
    font = font or ('Bold' if bold else 'Sans')
    if mixed:
        mixed_color = INK if mixed[1].startswith('SW') else BLUE
        fragments = [(mixed[1], 'Reference', mixed_color),('  '+mixed[2], 'Sans', mixed_color)]
    else:
        fragments = [(s,font,color)]
    width = sum(pdfmetrics.stringWidth(t,f,size) for t,f,col in fragments)
    start = x if align=='left' else x-width if align=='right' else x-width/2
    assert start >= 19.9 and start+width <= 410.1, (page_no,s,start,width)
    assert 10 <= y <= 286, (page_no,s,y)
    text_boxes.append((page_no,start,y-size,width,size,s))
    cursor = start
    for t,f,col in fragments:
        c.setFillColor(col); c.setFont(f,size*mm)
        c.drawString(cursor*mm,(297-y)*mm,t)
        cursor += pdfmetrics.stringWidth(t,f,size)


def formula(x, y, expression, size=10.5, max_width=180, color=INK):
    """LaTeX math syntax rendered as vector paths, never a bitmap or raw markup.
    x/y locate the top-left; size is in points, independent of body mm sizing.
    """
    buffer = io.BytesIO()
    with rc_context({'mathtext.fontset':'stix', 'svg.fonttype':'path'}):
        mathtext.math_to_image('$'+expression+'$', buffer,
                              prop=FontProperties(size=size*FONT_FACTOR), format='svg', color=color)
    drawing = svg2rlg(io.BytesIO(buffer.getvalue()))
    assert drawing is not None, expression
    assert drawing.width <= max_width*mm, (expression, drawing.width/mm, max_width)
    renderPDF.draw(drawing, c, x*mm, (297-y)*mm-drawing.height)


def line(x,y,X,Y,width=.25,color=None):
    color=color or (SYMBOL if SYMBOL_CONTEXT else WIRE)
    c.setStrokeColor(color); c.setLineWidth(width*mm)
    c.line(x*mm,(297-y)*mm,X*mm,(297-Y)*mm)

def path(points,width=.25,color=None):
    color=color or (SYMBOL if SYMBOL_CONTEXT or points[0]==points[-1] else WIRE)
    if len(points)==4 and points[0]==points[-1] and not SYMBOL_CONTEXT:
        # Discrete diode/LED symbol fill, matching the source; port triangles stay hollow.
        shape=c.beginPath()
        shape.moveTo(points[0][0]*mm,(297-points[0][1])*mm)
        for px,py in points[1:]:shape.lineTo(px*mm,(297-py)*mm)
        shape.close();c.setFillColor(SYMBOL);c.drawPath(shape,fill=1,stroke=0)
    for a,b in zip(points,points[1:]): line(*a,*b,width,color=color)

def rect(x,y,w,h,fill=None,width=.25):
    stroke = SYMBOL if w<=10 and h<=10 else BODY_COLOR if SYMBOL_CONTEXT or fill==CREAM else INK
    c.setStrokeColor(stroke); c.setLineWidth(width*mm)
    if fill: c.setFillColor(fill)
    c.rect(x*mm,(297-y-h)*mm,w*mm,h*mm,fill=bool(fill),stroke=1)

def dot(x,y):
    c.setFillColor(WIRE); c.circle(x*mm,(297-y)*mm,.7*mm,fill=1,stroke=0)

@symbol_style
def gnd(x,y):
    line(x,y,x,y+3,color=NET_COLOR)
    for yy,ww in [(3,3),(4.5,2),(6,1)]: line(x-ww,y+yy,x+ww,y+yy,color=NET_COLOR)
    text(x,y+11,'GND',2.45,color=NET_COLOR,align='center',font='Net')

port_markers = []

def port_marker(x,y,kind):
    """WeAct power symbols; signal terminals use net labels without markers."""
    if kind in ('in_left','in_right','left','right'):
        return
    port_markers.append((page_no,x,y,kind))
    c.setStrokeColor(NET_COLOR);c.setLineWidth(.25*mm)
    if kind == 'power':
        segments=[((x,y),(x,y-4)),((x-2.5,y-4),(x+2.5,y-4))]
    elif kind == 'power_top':
        segments=[((x-2.5,y),(x+2.5,y))]
    elif kind == 'ground':
        segments=[((x,y),(x,y+2))]+[((x-w,y+dy),(x+w,y+dy)) for dy,w in [(2,2.5),(3.3,1.6),(4.6,.7)]]
    else:
        raise ValueError('Unknown power symbol: '+kind)
    for (x1,y1),(x2,y2) in segments:
        c.line(x1*mm,(297-y1)*mm,x2*mm,(297-y2)*mm)


def label(x,y,s,side='left',port=None,terminal=None):
    # The terminal is explicit: marker and existing conductor meet exactly.
    shift=2
    if port:
        px,py=terminal or (x,y)
        port_marker(px,py,port)
        shift=6.5 if port=='power' else 2
    text(x,y-shift,s,2.8,color=NET_COLOR,align=side,font='Net')
    if port not in ('power','power_top','ground') and s!='GND':
        width=pdfmetrics.stringWidth(s,'Net',2.8*FONT_FACTOR)
        start=x if side=='left' else x-width if side=='right' else x-width/2
        c.setStrokeColor(NET_COLOR);c.setLineWidth(.12*mm)
        c.line(start*mm,(297-y+shift-.35)*mm,(start+width)*mm,(297-y+shift-.35)*mm)


def reg(ref,value,pins):
    assert ref not in refs,ref
    refs[ref]=value; connections[ref]=pins

@symbol_style
def r(x,y,ref,val,n1,n2,vertical=False):
    reg(ref,val,{'1':n1,'2':n2})
    if vertical:
        line(x,y,x,y+7); path([(x,y+7),(x-1.2,y+7.5),(x+1.2,y+8.5),(x-1.2,y+9.5),(x+1.2,y+10.5),(x-1.2,y+11.5),(x+1.2,y+12.5),(x,y+13)]); line(x,y+13,x,y+20)
        text(x+5,y+8,ref,3,True);text(x+5,y+14,val,3)
        return (x,y),(x,y+20)
    line(x,y,x+7,y); path([(x+7,y),(x+7.5,y-1.2),(x+8.5,y+1.2),(x+9.5,y-1.2),(x+10.5,y+1.2),(x+11.5,y-1.2),(x+12.5,y+1.2),(x+13,y)]);line(x+13,y,x+20,y)
    text(x+10,y-5,ref,3,True,align='center');text(x+10,y+7,val,3,align='center')
    return (x,y),(x+20,y)

@symbol_style
def cap(x,y,ref,val,n1,n2,vertical=False,positive=False):
    reg(ref,val,{'1':n1,'2':n2})
    display_value=val if positive else val+' · cerâmico'
    c.setStrokeColor(SYMBOL);c.setLineWidth(.45*mm)
    if vertical:
        line(x,y,x,y+8)
        line(x-4,y+8,x+4,y+8,.45,color=SYMBOL)
        if positive:
            arc=c.beginPath()
            arc.moveTo((x-4)*mm,(297-y-11)*mm)
            arc.curveTo((x-2)*mm,(297-y-9)*mm,(x+2)*mm,(297-y-9)*mm,(x+4)*mm,(297-y-11)*mm)
            c.drawPath(arc,fill=0,stroke=1)
            line(x,y+9.5,x,y+20)
        else:
            line(x-4,y+11,x+4,y+11,.45,color=SYMBOL)
            line(x,y+11,x,y+20)
        text(x+6,y+8,ref,3,True)
        text(x+6,y+14,display_value,2.8)
        if positive:
            text(x-7,y+6,'+',3.5,True,color=SYMBOL)
            text(x-7,y+15,'−',3.5,True,color=SYMBOL)
        return (x,y),(x,y+20)
    line(x,y,x+8,y)
    line(x+8,y-4,x+8,y+4,.45,color=SYMBOL)
    if positive:
        arc=c.beginPath()
        arc.moveTo((x+11)*mm,(297-y+4)*mm)
        arc.curveTo((x+9)*mm,(297-y+2)*mm,(x+9)*mm,(297-y-2)*mm,(x+11)*mm,(297-y-4)*mm)
        c.drawPath(arc,fill=0,stroke=1)
        line(x+9.5,y,x+20,y)
    else:
        line(x+11,y-4,x+11,y+4,.45,color=SYMBOL)
        line(x+11,y,x+20,y)
    text(x+10,y-7,ref,3,True,align='center')
    text(x+10,y+9,display_value,2.8,align='center')
    if positive:
        text(x+2,y-4,'+',3.5,True,color=SYMBOL)
        text(x+14,y-4,'−',3.5,True,color=SYMBOL)
    return (x,y),(x+20,y)

@symbol_style
def op(x,y,ref,pins):
    # x,y = left input at upper (-); lower (+) 12 mm below.
    reg(ref,'TL072',pins)
    triangle=c.beginPath()
    triangle.moveTo((x+8)*mm,(297-y+7)*mm)
    triangle.lineTo((x+8)*mm,(297-y-19)*mm)
    triangle.lineTo((x+32)*mm,(297-y-6)*mm)
    triangle.close()
    c.setFillColor(CREAM);c.drawPath(triangle,fill=1,stroke=0)
    path([(x+8,y-7),(x+8,y+19),(x+32,y+6),(x+8,y-7)],.35)
    line(x,y,x+8,y,color=PIN_COLOR);line(x,y+12,x+8,y+12,color=PIN_COLOR);line(x+32,y+6,x+40,y+6,color=PIN_COLOR)
    text(x+10,y+1,'−',3.4);text(x+10,y+13,'+',3.4)
    nums=('2','3','1') if ref=='U1A' else ('6','5','7')
    text(x+3,y-2,nums[0],2.6);text(x+3,y+10,nums[1],2.6);text(x+34,y+4,nums[2],2.6)
    text(x+18,y-12,ref,3.4,True,align='center');text(x+18,y+25,'TL072',3,align='center')
    return (x,y),(x,y+12),(x+40,y+6)

def signal_direction(ref,name,net):
    if net=='GND' or net.startswith('+'):return None
    if ref=='H_CODEC':
        if name=='SDA':return 'E/S'
        return 'S' if name in ('AOUTL','SDOUT') else 'E'
    if ref=='H_ESP32':return 'E' if 'RX2' in name else 'S'
    if 'SDA' in name:return 'E/S'
    return 'E' if name.startswith(('PA0','PD9','PC0','PC1','PC2','PC3')) else 'S'


@symbol_style
def module(x,y,w,h,ref,title,rows,suppress=()):
    reg(ref,title,{name:net for side,off,name,net in rows})
    rect(x,y,w,h,fill=CREAM)
    text(x+w/2,y+7,ref,3.4,True,align='center')
    text(x+w/2,y+13,title,3,align='center')
    for side,off,name,net in rows:
        yy=y+off
        direction=signal_direction(ref,name,net)
        display_name=name+(' ['+direction+']' if direction else '')
        if side=='L':
            line(x-10,yy,x,yy,color=PIN_COLOR);text(x+3,yy+1,display_name,2.7)
            if name not in suppress:
                kind='ground' if net=='GND' else 'power' if net.startswith('+') else 'in_left' if direction=='E' else 'left'
                label(x-11,yy,net,'right',port=kind,terminal=(x-10,yy))
        else:
            line(x+w,yy,x+w+10,yy,color=PIN_COLOR);text(x+w-3,yy+1,display_name,2.7,align='right')
            if name not in suppress:
                kind=('in_right' if direction=='E' else 'right') if ref=='H_STM32' and not name.startswith(('PD8','PD9')) else None
                label(x+w+11,yy,net,port=kind,terminal=(x+w+10,yy))


def section(x,y,title,subtitle=None):
    text(x,y,title,3.8,True,color=BLUE,font='HeadingBold')
    if subtitle:text(x,y+6,subtitle,2.8,color=GREY)

def notes(x,y,title,items,w=365):
    section(x,y,title)
    for i,s in enumerate(items):text(x,y+8+6*i,s,2.8)

def drawing_frame():
    rect(3,12,414,273,width=.24)
    rect(10,19,400,259,width=.24)
    c.setStrokeColor(INK);c.setLineWidth(.2*mm)
    def grid_text(x,y,value):
        c.setFillColor(INK);c.setFont('Sans',2.7*mm)
        c.drawCentredString(x*mm,(297-y)*mm,value)
    for i in range(4):
        x=3+414*(i+.5)/4
        grid_text(x,16.7,str(i+1));grid_text(x,282.7,str(i+1))
        y=12+273*(i+.5)/4
        grid_text(6.5,y+.9,'ABCD'[i]);grid_text(413.5,y+.9,'ABCD'[i])
    for i in range(1,4):
        x=3+414*i/4
        for y1,y2 in [(12,19),(278,285)]:
            c.line(x*mm,(297-y1)*mm,x*mm,(297-y2)*mm)
        y=12+273*i/4
        for x1,x2 in [(3,10),(410,417)]:
            c.line(x1*mm,(297-y)*mm,x2*mm,(297-y)*mm)


def page(title,sub):
    global page_no
    page_no+=1
    c.bookmarkPage(f'page{page_no}');c.addOutlineEntry(f'{page_no:02d} · {title}',f'page{page_no}')
    # Keep the existing relative placement on a virtual sheet and map it to A4.
    c.saveState()
    c.scale(PAGE_WIDTH_PT/(420*mm),PAGE_HEIGHT_PT/(297*mm))
    fillbox(0,0,420,297,PAPER)
    drawing_frame()
    # Raise only the fixed lower band to meet the reference's inner frame.
    c.saveState()
    c.translate(0,9*mm)
    # Lower-left annotation block removed; identification remains on the right.
    rect(230,259,180,28,width=.35)
    for yy in (268,277):line(230,yy,410,yy,.25,color=INK)
    for xx in (300,319,352,374):line(xx,268,xx,277,.25,color=INK)
    for xx in (310,365):line(xx,277,xx,287,.25,color=INK)
    text(233,262.4,'TÍTULO DA FOLHA',2.5,color=GREY)
    text(233,266.8,title,3.1,False,color=BLUE)
    for xx,caption,value in [
        (233,'NÚMERO DO DOCUMENTO','PD-EA-001'),
        (303,'REVISÃO','4.7'),
        (322,'DATA','2026-11-06'),
        (355,'FOLHA',f'{page_no} / 5'),
        (377,'FORMATO','A4 / 297 × 210')]:
        text(xx,271.3,caption,2.5,color=GREY)
        text(xx,275.8,value,2.8,True)
    text(233,280.8,'AUTORIA / PROJETO',2.5,color=GREY)
    text(233,285.2,'Rodrigues M. Lima',2.8)
    text(313,280.8,'STATUS DO DOCUMENTO',2.5,color=GREY)
    text(313,285.2,'Revisão documental',2.8)
    text(368,280.8,'ESCALA',2.5,color=GREY)
    text(368,285.2,'Sem escala',2.8)
    c.restoreState()  # Fixed legend and title block.
    # Move the contents uniformly, retaining the approved relative arrangement.
    c.saveState()
    c.translate(0,18*mm)


def begin_group(dx=0,dy=0):
    c.saveState()
    c.translate(dx*mm,-dy*mm)


def end_group():
    c.restoreState()


def end():
    c.restoreState()  # Contents translation.
    c.restoreState()  # A4 mapping.
    c.showPage()

# 1. Existing analog input and supply, with spacious feedback routing.
page('Alimentação analógica e entrada Hi-Z','9 V analógico · módulos alimentados por USB')
section(30,51,'1A  Fonte analógica e referência','A rede +9V_RAW está após D1; sua tensão é menor que a tensão do jack.')
rect(32,75,27,28,fill=CREAM);text(45.5,83,'J1',3.4,True,align='center');text(45.5,90,'DC 9 V',3,align='center')
text(61,79,'1',2.5);text(61,99,'2',2.5)
reg('J1','DC 9V',{'+9V':'9V_IN','GND':'GND'})
line(59,80,87,80);line(59,100,65,100);gnd(65,100)
reg('D1','1N4007',{'A':'9V_IN','K':'+9V_RAW'})
path([(87,77.8),(87,82.2),(91.5,80),(87,77.8)],.25);line(92,77.3,92,82.7,.3,color=SYMBOL);line(92,80,125,80)
text(89,68,'D1',3,True,align='center');text(89,95,'1N4007',3,align='center');label(118,80,'+9V_RAW (F1/F2)')
line(125,80,170,80);dot(125,80)
cap(125,95,'C_IN','100 µF','+9V_RAW','GND',True,True);line(125,80,125,95);gnd(125,115)
r(170,91,'R1','100k','+9V_RAW','VREF',True);line(170,80,170,91);line(170,111,170,125);dot(170,125)
r(170,135,'R2','100k','VREF','GND',True);line(170,125,170,135);gnd(170,155)
line(170,125,225,125);dot(210,125);label(225,125,'VREF (1B)',port='right')
cap(210,135,'C3','47 µF','VREF','GND',True,True);line(210,125,210,135);gnd(210,155)
begin_group(dy=-14)
section(275,65,'Alimentação de U1 (DIP-8)')
text(275,73,'Pino 8: +9V_RAW   ·   Pino 4: GND',2.8)
text(275,79,'U1A e U1B pertencem ao mesmo CI.',2.8)
formula(275,84,r'V_{\mathrm{REF}}=\frac{V_{\mathrm{RAW}}}{2}',11.5,max_width=112)
text(275,99,'Após D1: referência de aproximadamente 4,1 a 4,3 V.',2.65)
formula(275,103,r'R_{\mathrm{th}}=R_1\parallel R_2=50\,\mathrm{k}\Omega',10.5,max_width=112)
formula(275,111,r'\tau=R_{\mathrm{th}}C_3\approx2{,}35\,\mathrm{s}',10.5,max_width=112)
text(275,119,'Aguardar estabilização da referência.',2.65)
rect(305,132,44,20,fill=CREAM)
text(327,140,'U1 · alimentação',2.8,True,align='center')
text(327,147,'TL072 / DIP-8',2.7,align='center')
line(327,124,327,132);label(327,124,'+9V_RAW',side='center',port='power_top');text(330,130,'8',2.5)
line(327,152,327,157);text(330,155,'4',2.5);gnd(327,157)
end_group()
begin_group(dy=3)
section(30,175,'1B  Buffer de instrumento','C1 desacopla a entrada; R3 fixa o ponto DC em VREF. Ganho do seguidor = 1.')
# compressed lower row, within y250
reg('J2','IN P10',{'TIP':'JACK_IN','GND':'GND'})
rect(32,209,24,27,fill=CREAM);text(44,217,'J2',3,True,align='center');text(44,224,'ENTRADA',2.7,align='center')
line(56,215,75,215);line(56,233,62,233);gnd(62,233)
cap(75,215,'C1','100 nF','JACK_IN','HI_Z');line(95,215,145,215);dot(115,215)
r(115,225,'R3','1M','HI_Z','VREF',True);line(115,215,115,225);line(115,245,130,245);label(130,245,'VREF',port='in_right')
a,b,o=op(145,203,'U1A',{'IN-':'BUF_OUT','IN+':'HI_Z','OUT':'BUF_OUT','VCC':'+9V_RAW','GND':'GND'})
path([o,(200,209),(200,184),(138,184),(138,203),a]);dot(200,209)
line(200,209,235,209);cap(235,209,'C2','10 µF','BUF_OUT','ADC_IN_L',positive=True)
line(255,209,280,209);label(280,209,'ADC_IN_L (F3)',port='right')
formula(315,205,r'Z_{\mathrm{in}}\approx1\,\mathrm{M}\Omega',12,max_width=80,color=INK)
formula(315,215,r'f_{\mathrm{c}}=\frac{1}{2\pi R_3 C_1}\approx1{,}59\,\mathrm{Hz}',10.5,max_width=80)
text(300,230,'C2 (+) voltado para U1A.',2.8);text(300,238,'Interface ADC: condição P1, folha 5.',2.8)
end_group()
end()

# 2. Preserve original RC ladder; correct its description, not its values.
page('Filtro passivo e saída de áudio','Dois polos RC · seguidor TL072 · acoplamento AC')
section(30,51,'2A  Rede de saída existente','O circuito é uma cascata RC carregada seguida de buffer. Não é um filtro Sallen-Key.')
begin_group(dy=3)
label(35,110,'DAC_OUT_L (F3)',port='in_left');line(35,110,80,110)
r(80,110,'R4','1k','DAC_OUT_L','LP_NODE1');line(100,110,135,110);dot(135,110)
cap(135,125,'C4','4,7 nF','LP_NODE1','GND',True);line(135,110,135,125);gnd(135,145)
line(135,110,165,110);r(165,110,'R5','1k','LP_NODE1','LP_NODE2');line(185,110,225,110);dot(200,110)
cap(200,125,'C6','1,5 nF','LP_NODE2','GND',True);line(200,110,200,125);gnd(200,145)
a,b,o=op(225,98,'U1B',{'IN-':'OUT_BUF','IN+':'LP_NODE2','OUT':'OUT_BUF'})
path([o,(275,104),(275,77),(218,77),(218,98),a]);dot(275,104)
line(275,104,295,104);cap(295,104,'C5','10 µF','OUT_BUF','JACK_OUT',positive=True)
line(315,104,365,104);dot(335,104)
r(335,125,'R6','100k','JACK_OUT','GND',True);line(335,104,335,125);gnd(335,145)
reg('J3','OUT P10',{'TIP':'JACK_OUT','GND':'GND'})
rect(365,96,29,30,fill=CREAM);text(379.5,105,'J3',3.4,True,align='center');text(379.5,113,'SAÍDA',2.8,align='center')
line(365,120,358,120);gnd(358,120)
end_group()
begin_group(dy=5)
section(30,179,'2B  Resposta do filtro e condições de uso')
text(30,187,'A interação entre as duas redes RC está incluída na função de transferência abaixo.',2.9)
formula(30,193,r'H(s)=\frac{1}{R_4R_5C_4C_6s^2+(R_4C_4+R_4C_6+R_5C_6)s+1}',12,max_width=205)
formula(238,193,r'f_{-3\,\mathrm{dB}}\approx23{,}4\,\mathrm{kHz}',12,max_width=155,color=INK)
text(30,210,'Modelo: fonte ideal, entrada de U1B de alta impedância; s representa a variável de Laplace.',2.8)
for i, note in enumerate([
    'Valores preservados. O filtro digital de reconstrução permanece no codec.',
    'C5 bloqueia o nível DC de U1B: terminal positivo para o amplificador. R6 define o DC do jack.',
    'Saída de linha para carga de pelo menos 10 kΩ; não dimensionada para fones de baixa impedância.',
    'O nível DC de DAC_OUT_L deve respeitar a faixa de modo comum do TL072 (P2, folha 5).',
    'U1B compartilha a alimentação de U1A: pino 8 em +9V_RAW e pino 4 em GND (folha 1).'
]):
    text(30,219+i*7,note,2.85)
end_group()
end()

# 3. Modules: preserve logical endpoints, do not invent physical breakout pinout.
page('Codec, processamento e comunicação','Interfaces funcionais dos módulos · sinais de 3,3 V')
section(30,51,'3A  Interligação por nomes de rede','I²S: áudio full-duplex (SDIN/SDOUT). UART: full-duplex (TX/RX). I²C: controle half-duplex.')
begin_group(dy=4)
codec=[('L',28,'VA / +5V','+5V_USB'),('L',42,'AGND','GND'),('L',56,'VD / +3V3','+3.3V'),('L',70,'DGND','GND'),('L',98,'AINL+','ADC_IN_L'),('L',126,'AOUTL','DAC_OUT_L')]
for off,name,net in [(28,'MCLK','SAI4_MCLK'),(42,'LRCK / FS','SAI4_FS'),(56,'SCLK','SAI4_SCK'),(70,'SDIN','SAI4_SD_OUT'),(84,'SDOUT','SAI4_SD_IN'),(98,'SCL','I2C1_SCL'),(112,'SDA','I2C1_SDA'),(126,'/RESET','CODEC_RST')]:codec.append(('R',off,name,net))
module(78,68,65,143,'H_CODEC','CS4272 Breakout',codec)
stm=[('L',28,'PE0 / MCLK','SAI4_MCLK'),('L',42,'PE4 / FS','SAI4_FS'),('L',56,'PE5 / SCK','SAI4_SCK'),('L',70,'PE6 / SD_A','SAI4_SD_OUT'),('L',84,'PA0 / SD_B','SAI4_SD_IN'),('L',98,'PB8 / SCL','I2C1_SCL'),('L',112,'PB9 / SDA','I2C1_SDA'),('L',126,'PD10 / RESET','CODEC_RST')]
for off,name,net in [(147,'5V_USB','+5V_USB'),(161,'GND','GND'),(175,'3V3_OUT','+3.3V')]:stm.append(('L',off,name,net))
for off,name,net in [(28,'PD8 / TX3','UART_TX_STM'),(42,'PD9 / RX3','UART_RX_STM'),(70,'PC0 / SW1','SW_OVERDRIVE'),(84,'PC1 / SW2','SW_EQ'),(98,'PC2 / SW3','SW_DELAY'),(112,'PC3 / SW4','SW_MUTE'),(133,'PE7 / LED1','LED_OD_DRV'),(147,'PE8 / LED2','LED_EQ_DRV'),(161,'PE9 / LED3','LED_DLY_DRV'),(175,'PE15 / LED4','LED_STAT_DRV')]:stm.append(('R',off,name,net))
module(230,68,65,182,'H_STM32','WeAct STM32H723',stm,suppress=tuple(row[2] for row in stm[:8]))
# Explicit physical wires between codec and DSP, with no crossings.
for off in [28,42,56,70,84,98,112,126]:
    # Put name only once in this narrow corridor; erase neither text nor conductors.
    line(153,68+off,220,68+off)
# ESP on separate logical net ports, so no visual crossing with GPIO.
module(350,68,49,80,'H_ESP32','ESP32 DevKit',[
('L',28,'GPIO16 / RX2','UART_TX_STM'),('L',42,'GPIO17 / TX2','UART_RX_STM'),('L',56,'VIN / 5V','+5V_USB'),('L',67,'GND','GND')],suppress=('GPIO16 / RX2','GPIO17 / TX2'))
line(305,96,340,96)
line(305,110,340,110)
text(350,164,'UART: 115200, 8N1',2.7)
text(350,173,'FULL-DUPLEX: TX + RX',2.7)
text(350,187,'USB: fonte única.',2.7)
text(350,196,'Ver P3 na folha 5.',2.7)
end_group()
text(30,234,'I²C: SDA bidirecional, half-duplex. AD0 em GND: 0x10 (7 bits); escrita 0x20.',2.8)
text(30,242,'As ligações internas de VL, AIN−, VCOM, FILT+ e AD0 pertencem ao breakout (P1/P4, folha 5).',2.8)
text(30,250,'SAI4: MCLK = 12,288 MHz; FS = 48 kHz; SCK = 3,072 MHz; 2 slots de 32 bits, áudio de 24 bits.',2.8)
end()

# 4. Controls.
page('Chaves e indicadores','Quatro entradas ativas em nível baixo · quatro LEDs')
section(30,51,'4A  Chaves com retenção','Configurar PC0…PC3 com GPIO_PULLUP e debounce no firmware.')
section(227,51,'4B  Indicadores','Saídas push-pull; resistor individual de 330 Ω.')
for i,(sw,name,net,pin) in enumerate([('SW1','Overdrive','SW_OVERDRIVE','PC0'),('SW2','Equalizador','SW_EQ','PC1'),('SW3','Delay','SW_DELAY','PC2'),('SW4','Master Mute','SW_MUTE','PC3')]):
    yy=92+i*42
    label(35,yy,f'{net} (F3)',port='left');line(35,yy,118,yy)
    c.setStrokeColor(SYMBOL);c.setLineWidth(.25*mm)
    for xx in (118,126):c.circle(xx*mm,(297-yy)*mm,.55*mm,stroke=1,fill=0)
    line(118.45,yy-.4,125.5,yy-4,.25,color=SYMBOL);line(126.55,yy,160,yy);gnd(160,yy)
    text(122,yy-14,f'{sw} · {name}',3.2,True,align='center');text(35,yy+12,f'{pin} · fechado = LOW',2.8)
    text(112,yy+20,'COM + contato; terceiro livre.',2.6)
    reg(sw,name,{'IN':net,'GND':'GND'})
for i,(ref,name,net,pin) in enumerate([('D2','LED Overdrive','LED_OD_DRV','PE7'),('D3','LED Equalizador','LED_EQ_DRV','PE8'),('D4','LED Delay','LED_DLY_DRV','PE9'),('D5','LED Status','LED_STAT_DRV','PE15')]):
    yy=92+i*42
    label(227,yy,f'{net} (F3)',port='in_left');line(227,yy,285,yy)
    r(285,yy,'R_'+ref,'330R',net,'LED_'+ref+'_A');line(305,yy,330,yy)
    path([(330,yy-2.2),(330,yy+2.2),(334.5,yy),(330,yy-2.2)],.25);line(335,yy-2.7,335,yy+2.7,.3,color=SYMBOL)
    # LED emission arrows, distinct from ordinary diode.
    for xx,dy in [(332,-4.5),(335,-3)]:
        line(xx,yy+dy,xx+2.8,yy+dy-2.8,.22,color=SYMBOL);path([(xx+1.7,yy+dy-2.8),(xx+2.8,yy+dy-2.8),(xx+2.8,yy+dy-1.7)],.22,color=SYMBOL)
    line(335,yy,365,yy);gnd(365,yy)
    text(331,yy+13,f'{ref} · {name[4:]}',3,True,align='center');text(375,yy+1,pin,2.8)
    reg(ref,name,{'A':'LED_'+ref+'_A','K':'GND'})
text(30,257,'MTS-102 é SPDT: o terceiro contato fica sem conexão. LEDs: ânodo à esquerda; cátodo voltado ao GND.',2.8)
end()

# 5. Audit status, preserved BOM and actual documentation scope.
page('Condições de interface e rastreabilidade','Revisão documental · sem substituição de componentes')
begin_group(dy=18)
section(30,51,'5A  Condições para funcionamento e montagem')
rows=[
('P1 · ADC do breakout','O CS4272 tem entradas diferenciais. Confirmar bias, AIN− e condicionamento no módulo.',
 'C2 não fornece sozinho o retorno DC do ADC. O conector lógico não substitui o esquema interno.'),
('P2 · TL072 e saída DAC','Confirmar o nível DC de AOUTL no módulo e a faixa de modo comum do TL072 a 9 V.',
 'Uma saída crua em cerca de 2,5 V pode ficar fora da faixa. Sem mudar a BOM, isto permanece pendente.'),
('P3 · Alimentação USB','Usar uma única fonte de 5 V no conjunto; GND comum entre as placas e os jacks.',
 'Verificar corrente do regulador 3V3, consumo total e isolamento de VBUS antes de ligar outro USB.'),
('P4 · Suporte do codec','Conferir no breakout: VL, AD0, VCOM, FILT+, desacoplamento e entradas do canal não usado.',
 'AD0 deve ficar em GND para 0x10. Não presumir que todo módulo CS4272 inclui esses circuitos.'),
('P5 · Layout e partida','Desacoplamento local do TL072 não aparece na BOM externa. Conferir se existe na montagem.',
 'Firmware: clocks estáveis antes de /RESET; CPEN+PDN deve ser escrito dentro de 10 ms após liberar reset.')]
for i,(head,l1,l2) in enumerate(rows):
    y=64+i*34
    text(30,y,head,3,True);text(30,y+8,l1,2.8);text(30,y+15,l2,2.8)
section(225,51,'5B  Componentes preservados')
for i,s in enumerate([
'R1, R2, R6: 100 kΩ; R3: 1 MΩ; R4, R5: 1 kΩ; R_D2 a R_D5: 330 Ω.',
'C1: 100 nF; C2, C5: 10 µF; C3: 47 µF; C4: 4,7 nF; C6: 1,5 nF; C_IN: 100 µF.',
'D1: 1N4007; D2…D5: LEDs; U1: TL072 DIP-8 (unidades A/B); SW1…SW4: MTS-102.',
'J1: DC 9 V; J2/J3: P10; módulos: WeAct STM32H723, CS4272 Breakout, ESP32 DevKit.'
]):text(225,66+i*10,s,2.7)
text(225,110,'C1, C4 e C6: cerâmicos. C_IN, C2, C3 e C5: eletrolíticos polarizados.',2.7)
section(225,149,'5C  Referências e alcance da revisão')
text(225,161,'Apresentação baseada em ISO 5457 e ISO 7200; convenções de desenho IEC 61082-1 / IEC 60617.',2.65)
text(225,178,'Sem auditoria integral das normas ou ensaio de bancada. P1…P5 impedem declarar liberação para fabricação.',2.65)
text(225,195,'Fontes: Cirrus CS4272 DS593F2 §§ 5–6; TI TL072; ST STM32H723 DS13313 Rev. 5; gerador EasyEDA local.',2.65)
text(225,212,'Consultar datasheets: CS4272  |  TL072  |  STM32H723  ·  Continuidade visual preservada; sem ERC de CAD.',2.65)
# Link rectangles follow the relocated reference row, including its local translation.
link_prefix='Consultar datasheets: '
link_x=225+pdfmetrics.stringWidth(link_prefix,'Sans',2.65*FONT_FACTOR)
for name,url in [('CS4272','https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf'),
                 ('TL072','https://www.ti.com/product/TL072'),
                 ('STM32H723','https://www.st.com/resource/en/datasheet/stm32h723vg.pdf')]:
    w=pdfmetrics.stringWidth(name,'Sans',2.65*FONT_FACTOR)
    c.linkURL(url,(link_x*mm,(297-212-1)*mm,(link_x+w)*mm,(297-212+3)*mm),relative=1)
    link_x+=pdfmetrics.stringWidth(name+'  |  ','Sans',2.65*FONT_FACTOR)
end_group()
end()

# Contract check: references and values extracted from the user's existing generator.
spec=importlib.util.spec_from_file_location('existing',Path(__file__).with_name('gen_schematic.py'))
existing=importlib.util.module_from_spec(spec);spec.loader.exec_module(existing)
b=existing.build_pedaleira_schematic()
original={}
for shape in b.shapes:
    if not shape.startswith('LIB~'):continue
    params=shape.split('~')[3].split('`')
    value=params[params.index('name')+1]
    for part in shape.split('#@$'):
        if part.startswith('T~P~'):
            original[part.split('~')[12]]=value;break
# PDF uses locale formatting for only these display values; semantic values are unchanged.
aliases={'100 µF':'100uF','47 µF':'47uF','10 µF':'10uF','100 nF':'100nF','4,7 nF':'4.7nF','1,5 nF':'1.5nF'}
assert set(refs)==set(original),(set(refs)-set(original),set(original)-set(refs))
for ref,v in refs.items():assert aliases.get(v,v)==original[ref],(ref,v,original[ref])
# Compare net pin membership against the input builder, independent of names of anonymous nodes.
parent={}
def find(p):
    parent.setdefault(p,p)
    if parent[p]!=p:parent[p]=find(parent[p])
    return parent[p]
def union(a,b):parent[find(a)]=find(b)
points={(x,y) for x,y,_,_ in b.pins}|{(x,y) for x,y,_ in b.netlabels}
for x,y,X,Y in b.wires:
    union((x,y),(X,Y))
    for p in points:
        if (x==X==p[0] and min(y,Y)<=p[1]<=max(y,Y)) or (y==Y==p[1] and min(x,X)<=p[0]<=max(x,X)):
            union(p,(x,y))
labels={}
for x,y,n in b.netlabels:
    if n in labels:union((x,y),labels[n])
    else:labels[n]=(x,y)
old_nets=defaultdict(set)
for x,y,pin,ref in b.pins:old_nets[find((x,y))].add((ref,pin))
new_nets=defaultdict(set)
for ref,pins in connections.items():
    for pin,net in pins.items():new_nets[net].add((ref,pin))
# Existing SPDT symbol pin names and module terminal names are mapped explicitly.
remap={
'J1':{'+9V':'VCC'},
**{ref:{'IN':'1','GND':'2'} for ref in ['SW1','SW2','SW3','SW4']},
'H_CODEC':{'VA / +5V':'VA (+5V)','VD / +3V3':'VD (+3.3V)','LRCK / FS':'LRCK/FS'},
'H_STM32':{'PD8 / TX3':'PD8 (TX3)','PD9 / RX3':'PD9 (RX3)','PE0 / MCLK':'PE0 (MCLK)','PE4 / FS':'PE4 (FS)','PE5 / SCK':'PE5 (SCK)','PE6 / SD_A':'PE6 (SD_OUT)','PA0 / SD_B':'PA0 (SD_IN)','PB8 / SCL':'PB8 (SCL)','PB9 / SDA':'PB9 (SDA)','PD10 / RESET':'PD10 (RST)','PC0 / SW1':'PC0 (SW1)','PC1 / SW2':'PC1 (SW2)','PC2 / SW3':'PC2 (SW3)','PC3 / SW4':'PC3 (SW4)','PE7 / LED1':'PE7 (LED1)','PE8 / LED2':'PE8 (LED2)','PE9 / LED3':'PE9 (LED3)','PE15 / LED4':'PE15 (LED4)'},
'H_ESP32':{'GPIO16 / RX2':'GPIO16 (RX2)','GPIO17 / TX2':'GPIO17 (TX2)','VIN / 5V':'5V_IN'}}
normalized={frozenset((ref,remap.get(ref,{}).get(pin,pin)) for ref,pin in pins) for pins in new_nets.values()}
expected={frozenset(v) for v in old_nets.values()}
assert normalized==expected, ('PDF only', normalized-expected, 'Original only',expected-normalized)
c.save()
report={'pages':page_no,'symbol_references':len(refs),'physical_TL072_count':1,'bom_preserved':True,'connectivity_preserved':True,'nets':len(normalized),'status':'documentary review; P1-P5 open','revision':'4.7','math_rendering':'vector LaTeX mathtext','typography':'embedded Times New Roman; Liberation Sans headings (Arial-compatible)','color_revision':'supplied WeAct Altium PDF: blue symbols, navy wires, maroon net labels/power, cream modules, black frame','terminal_markers':len(port_markers),'direction_annotations':'WeAct underlined net labels without triangles; E/S pin tags; UART and I2S full-duplex; I2C half-duplex','capacitor_symbols':'electrolytic: curved negative plate, + and minus polarity marks, capacitance only; ceramic: two straight plates and type label','page_format':'A4 landscape','media_box_pt':[842,595],'net_terminal_triangles':False,'content_shift_up_mm':18,'style_reference':'/home/rodrigues/Downloads/STM32H7xx SchDoc V12.pdf','layout_revision':'aligned section titles, balanced analog groups, parallel controls, two-column technical notes','components':refs}
(ROOT/'output/pdf/verificacao_esquematica.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
print(OUT)
