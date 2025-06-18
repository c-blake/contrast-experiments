#!/usr/bin/python3
#stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color
# Mynex answer, in particular.
import sys, termios as tio, tty, time, re, os

def color(ints):    # 3-channel integer -> 3-channel float
  result = ints; s = 1.0/255
  for i, c in enumerate(result): result[i] = s*c
  return result

def _sRGB2Lin(v: float) -> float:
  return v/12.92 if v <= 0.04045 else ((v + 0.055)/1.055)**2.4

def Y(c) -> float:
  "Luminance Y of the color"; (r, g, b) = c
  return 0.2126*_sRGB2Lin(r) + 0.7152*_sRGB2Lin(g) + 0.0722*_sRGB2Lin(b)

def L(c) -> float:        # L* ~ "perceptual lightness"
  "So-called L* of the color; Re-normalized from [0,100] -> [0,1]"
  # CIE std sez 0.008856 & 903.3 but its intent is 216/24389 24389/27.
  y = Y(c); return (y*(24389/27) if y <= 216/24389 else 116*pow(y,1/3) - 16)/100

minL = float(os.environ.get("minL", "0.05"))
wait = float(os.environ.get("wait", "0.025")) # delay between req-reply read
def contrast(p, q, m=Y, cmp='R') -> float:
  """Return some kind of (contrast float, its width3 format for a table
  based on measurement function `m()` & comparison code `cmp`."""
  if cmp == 'R':
    (p, q) = (m(p), m(q))
    lighter = max(p, q) + minL  # minL==0.05263 => Max Ratio 20.00
    darker  = min(p, q) + minL  # 0.0102 => Max Ratio=99
    ratio = lighter/darker
    fmt3 = f"{ratio:.0f}."
    return ratio, f"{ratio:.1f}" if len(fmt3) < 3 else fmt3
  elif cmp == 'D':
    con = abs(m(p) - m(q))
    return con, "1.0" if con == 1 else f"{con:.2f}"[1:]

def getTtyColors(colorIxes):
  i = sys.stdin; o = sys.stdout
  if not i.isatty(): return None
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
      o.write(f"\033]4;{colorIndex};?\033\\"); o.flush()
      time.sleep(wait)    # Give term time to answer
      a = ""              # Read answer into `a`
      while ch := i.read(1): a += ch
      if m := re.search(pat, a):
        result.append(color(list(map(lambda s: int(s[:2], 16),
                                 m.groups()))))
  finally: tio.tcsetattr(i, tio.TCSADRAIN, ta0)
  return result

def limitFor(cs, nHi, m=Y, cmp='R'):
  all = [ contrast(cs[i], cs[j], m, cmp)[0]
          for i in range(len(cs)) for j in range(len(cs)) ]
  all.sort()
  return all[-nHi]

def dumpTable(cs, lim, m=Y, cmp='R'):
  cnt = 0; E = "\033"; o = sys.stdout.write
  o("B/F")
  for b,fbank in enumerate([3,9]):
    for fc in range(8):
      if 8*b + fc > 0: o(" ")
      o(f"{8*b + fc:3}")
  o('\n')
  for B, bbank in enumerate([4,10]):    # dark|light BG banks
    for bc in  range(8):                # All BackGrounds
      i = 8*B + bc
      s = str(bbank) + str(bc)
      o(f"{E}[{s}m{i:2}")
      for b, fbank in enumerate([3,9]): # dark|light FG banks
        for fc in range(8):             # All ForeGrounds
          j = 8*b + fc
          s = str(fbank) + str(fc)
          con, fmt3 = contrast(cs[i], cs[j], m=m, cmp=cmp)
          if con > lim: cnt += 1; o(f"{E}[{s}m {fmt3}")
          else: o(f"{E}[{s}m    ")
      o(f"{E}[m\n")

use="""This script emits tables to assess various metrics/scores of contrast as
proxies for "legibility" scores.  Use emitted tables by just reading numbers &
evaluating if "scoreA>scoreB" even always implies "A is more readable than B"
(according to YOUR OWN PERSONAL PERCEPTION on various display devices, OLED,
LCD, DLP/LCD/etc.  projector images, etc.).  Command-line syntax is just:
  [wait=.025] [minL=0.05] contrast.py [numPairsToKeep(120)] [{RD|YL} pairs(all)]
E.g., `contrast.py 160 RY DL` emits two tables w/"worst" 1/3 (80+16/256) pairs
BLANKED where "worst" is defined by either ratio of CIE_Y or |diff| of L*.  Over
network connections (either via remote X or just ssh) you may need wait=0.1.
Tested only on xterm-400 & st-0.9.2."""
if __name__== '__main__':       # Should maybe take 
  if len(sys.argv)>1 and sys.argv[1] in ("-h","--help"): print(use); sys.exit(0)
  R, G, B, Z = '\033[91m', '\033[32m', '\033[94m', '\033[m'
  nHi = int(sys.argv[1]) if len(sys.argv) > 1 else 240  # Do all by default
  tabs = sys.argv[2:] if len(sys.argv) > 2 else ["RY", "RL", "DY", "DL"]
  cs = getTtyColors(range(16))  # Since lim depends on L v.Y, drive w/"best nHi"
  print("%6s %6s %2s %14s %14s %14s" %
        ("CIE_Y", "L*", "cX", f"{R}R{Z}", f"{G}G{Z}", f"{B}B{Z}"))
  for i, c in enumerate(cs):    # Lightness |difference| rather than ratio..
    (r, g, b) = c               #..may be more useful as a legibility score.
    print(f"{Y(c):.4f} {L(c):.4f} {i:2} {R}{r:.4f} {G}{g:.4f} {B}{b:.4f}{Z}")
  for tab in tabs:
    cmp, metric = tab[0], eval(tab[1])
    dumpTable(cs, limitFor(cs, nHi, metric, cmp), metric, cmp)
