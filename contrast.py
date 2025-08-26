#!/usr/bin/py
#stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color
def softClamp(y): return y + (0.022 - y)**1.414 if y <= 0.022 else y
def APCAcontrast(t, b):                 # APCA/SAPC from Y(Luminance) of txt,bg
  thresh = 0.035991; offset = 0.027     # APCA G-4g Constants for 2.4 _sRGB2Lin
  t = softClamp(t); b = softClamp(b)    # Move y to interval [0.00453..1]
  if abs(b - t) < 0.0005: return 0.     # Return 0 Early for tiny ∆Y
  C = (b**0.56 - t**0.57 if b > t else b**0.65 - t**0.62)*1.14
  if abs(C) < 0.001: return 0.0         # Clip for very low contrasts
  if b > t: return C - C*offset/thresh if C < +thresh else C - offset
  else    : return C - C*offset/thresh if C > -thresh else C + offset
# Exponent non-equality makes b>t !=> C>0 5% of time & b<t !=> C>0 12% of time.
# So, |C|<thresh !=> b<t and we must use logic based on b>t not just |C| to
# smooth/block polarity reversal.  The idea here seems to have metastasized from
# a L_goldenRatio norm |b^phi - t^phi|^(1/phi) which itself was unjustified.
# Lightness comparison corrections seem less important to me than "actual color
# ALSO matters" effects.  Switching off polarity is conceptually stronger, but
# only a PROXY for <pixel area>, itself only proxy for per glyph pixel patterns.
# Anyway, the implementation here exactly matches { given same (t,b)s }:
#  stackoverflow.com/questions/66567403/how-do-you-find-the-color-contrast-using-apca-advanced-perpetual-contrast-algor
# Given oft constant fiddling, A.Somers likely has weird new tweaks.  What this
# prog calls "AL" gives dark blue/black a high .35 score.  So, AL is likely bad,
# but dunno since even "AY" has some pretty bad scores in there.  This effort
# all feels..off track - a contrast distance metric between 2 colors should come
# from a full color triple even if dominant dimension is lightness.

from sys import argv, exit, stdin, stdout, stderr
import termios as tio, tty, time, re, os

def color(ints):    # 3-channel integer -> 3-channel float
  result = ints; s = 1.0/255
  for i, c in enumerate(result): result[i] = s*c
  return result

def _sRGB2Lin(v: float) -> float:
  return v/12.92 if v <= 0.04045 else ((v + 0.055)/1.055)**2.4

def Y(c) -> float:
  "Luminance Y of the color"; (r, g, b) = c
  return 0.2126729*_sRGB2Lin(r) + 0.7151522*_sRGB2Lin(g) + 0.072175*_sRGB2Lin(b)

def L(c) -> float:        # L* ~ "perceptual lightness"
  "So-called L* of the color; Re-normalized from [0,100] -> [0,1]"
  # CIE std sez 903.3 & 0.008856 but its intent is 24389/27 & 216/24389.
  y = Y(c); return (y*(24389/27) if y <= 216/24389 else 116*pow(y,1/3) - 16)/100

minL = float(os.environ.get("minL", "0.05"))
wait = float(os.environ.get("wait", "0.025")) # delay between req-reply read
axes = os.environ.get("axes", "B/F")          # B/F | F/B
def contrast(p, q, m=Y, cmp='R') -> float:
  """Return some kind of (contrast float, its width3 format for a table
  based on measurement function `m()` & comparison code `cmp`."""
  if cmp == 'R':
    (p, q) = (m(p), m(q))
    lighter = max(p, q) + minL  # MaxRatio=(1+minL)/minL => minL=1/(MaxRatio-1)
    darker  = min(p, q) + minL  # 1/(20-1)=0.0526316; 1/(100-1)=0.010101
    ratio = lighter/darker
    fmt3 = f"{ratio:.0f}."
    return ratio, f"{ratio:.1f}" if len(fmt3) < 3 else fmt3
  elif cmp == 'D':
    con = abs(m(p) - m(q))
    return con, "1.0" if con == 1 else f"{con:.2f}"[1:]
  elif cmp == 'A':              # Andy Somers' ideas circa 2021
    con = abs(APCAcontrast(m(p), m(q)))
    return con, "1.0" if con >= 1 else f"{con:.2f}"[1:]

def getTtyColors(colorIxes):
  i = stdin; e = stderr # Using stderr for this protocol allows saving..
  if not i.isatty():return None #..stdout via prog>out (to 'diff' matrices).
  hx = '([0-9a-fA-F]+)'; pat = f'rgb:{hx}/{hx}/{hx}'
  fd = i.fileno(); result = []
  try:
    ta0 = tty.setraw(fd)
    while True:                 # Hard to understand..
      ta = tio.tcgetattr(fd)    #..need for this loop.
      ta[6][tio.VMIN] = ta[6][tio.VTIME] = 0
      tio.tcsetattr(fd, tio.TCSANOW, ta)
      if not i.read(1): break
    for colorIndex in colorIxes:
      e.write(f"\033]4;{colorIndex};?\033\\"); e.flush()
      time.sleep(wait)    # Give term time to answer
      a = ""              # Read answer into `a`
      while ch := i.read(1): a += ch
      if m := re.search(pat, a):
        result.append(color(list(map(lambda s: int(s[:2], 16),
                                 m.groups()))))
  finally: tio.tcsetattr(i, tio.TCSADRAIN, ta0)
  return result

def limitFor(cs, nHi, m=Y, cmp='R'):
  if "." in nHi: return float(nHi)
  all = [ contrast(cs[i], cs[j], m, cmp)[0]
            for i in range(len(cs)) for j in range(len(cs)) ]
  all.sort()
  return all[-int(nHi)] if int(nHi) > 0 else -all[-int(nHi)]

def dumpTable(cs, lim, m=Y, cmp='R'):
  cnt = 0; E = "\033"; o = stdout.write
  o(axes)
  if axes=="B/F": ax0 = [3, 9] ; ax1 = [4, 10]
  else          : ax0 = [4, 10]; ax1 = [3, 9]
  for b,fbank in enumerate(ax0):
    for fc in range(8):
      if 8*b + fc > 0: o(" ")
      o(f"{8*b + fc:3}")
  o(' N^\n')
  for B, bbank in enumerate(ax1):       # dark|light BG banks
    for bc in  range(8):                # All Dark,Light Axis 1 (Background)
      i = 8*B + bc
      s = str(bbank) + str(bc)
      o(f"{E}[{s}m{i:2}")
      rowCnt = 0
      for b, fbank in enumerate(ax0):   # dark|light FG banks
        for fc in range(8):             # All Dark,Light Axis 0 (Foreground)
          j = 8*b + fc
          s = str(fbank) + str(fc)
          con, fmt3 = contrast(cs[j], cs[i], m=m, cmp=cmp) # takes t)ext on b)g
          if (lim >= 0 and con >= lim) or (lim < 0 and con < -lim):
              o(f"{E}[{s}m {fmt3}"); cnt += 1
              if j > i: rowCnt += 1
          else: o(f"{E}[{s}m    ")
      o(f"{E}[m {rowCnt}\n")
  limTag = f"{'FAIL' if lim<0 else 'PASS'}"
  print(f"{cnt} ={cnt/2.4:.1f}% {limTag} {cmp+str(m)[10:11] } Thresh {lim:.4f}")

use="""This script emits tables to assess various metrics/scores of contrast as
proxies for "legibility" scores.  Use emitted tables by just reading numbers &
evaluating if "scoreA > scoreB" even always implies "A is more readable than B"
(according to YOUR OWN PERSONAL PERCEPTION on various display devices, OLED,
LCD, DLP/LCD/etc.  projector images, etc.).  Command-line syntax is just:\n
  [axes=B/F] [palette=(unset)] [minL=0.05] [wait=.025] \\
    contrast.py [+-FP|int ToKeep(120)] [{DRA|YL}pairs(AllDRYL)]\n
Over a network (either via remote X or just ssh) you may need longer wait=0.1.
Tested on: xterm400,st0.9.2. 'axes' transposes, 'palette=' dumps, 'minL' tweaks.
FP ToKeep are value thresholds; int are rank; +:pass greater, -:fail lesser.
Kinds of comparison are D=diff, R=ratio, A=APCA curve.\n
Eg.1: `contrast.py 160 RY DL` emits two tables w/"worst" 1/3 (80+16/256) pairs
BLANKED where "worst" is defined by either ratio of CIE_Y or |diff| of L*.\n
Eg.2: Find numbers EASY to read in `contrast.py -0.1 DL`; Maybe shrink thresh.\n
Eg.3: Use X WM to set up 2 terminals for pixel-aligned page flipping; On 1, do
`contrast.py 3.0 RY` (prints count N); On other, `contrast.py N DL`.  Rapidly &
repeatedly flip.  AboveDiagTots N^ help for where to look for toggling diffs."""

if __name__== '__main__':
  if len(argv)>1 and argv[1] in ("-h","--help"): print(use); exit(0)
  nHi = argv[1] if len(argv) > 1 else "240"  # Do all by default
  tabs = argv[2:] if len(argv) > 2 else ["RY", "RL", "DY", "DL"]
  cs = getTtyColors(range(16))  # Since lim depends on L v.Y, drive w/"best nHi"
  if "palette" in os.environ:   # Optional "documentation".  For portability.
    R, G, B, Z = '\033[91m', '\033[32m', '\033[94m', '\033[m'
    print("%6s %6s %2s %14s %14s %14s" %
          ("CIE_Y", "L*", "cX", f"{R}R{Z}", f"{G}G{Z}", f"{B}B{Z}"))
    for i, c in enumerate(cs):  # Lightness |difference| rather than ratio..
      (r, g, b) = c             #..may be more useful as a legibility score.
      print(f"{Y(c):.4f} {L(c):.4f} {i:2} {R}{r:.4f} {G}{g:.4f} {B}{b:.4f}{Z}")
  for tab in tabs:
    cmp, metric = tab[0], eval(tab[1])
    dumpTable(cs, limitFor(cs, nHi, metric, cmp), metric, cmp)
