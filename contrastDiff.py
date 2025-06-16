#!/usr/bin/py
#stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color
# Mynex answer, in particular.
import sys, termios as tio, tty, time, re

def color(ints):    # 3-channel integer -> 3-channel float
  result = ints; s = 1.0/255
  for i, c in enumerate(result): result[i] = s*c
  return result

def _sRGB2Lin(v: float) -> float:
  return v/12.92 if v <= 0.04045 else ((v + 0.055)/1.055)**2.4

def Y(c) -> float:
  "Luminance Y of the color"; (r, g, b) = c
  return 0.2126*_sRGB2Lin(r) + 0.7152*_sRGB2Lin(g) + 0.0722*_sRGB2Lin(b)

def Ls(c) -> float:        # L* ~ "perceptual lightness"
  "So-called L* of the color; Re-normalized from [0,100] -> [0,1]"
  # CIE std sez 0.008856 & 903.3 but its intent is 216/24389 24389/27.
  y = Y(c); return (y*(24389/27) if y <= 216/24389 else 116*pow(y,1/3) - 16)/100

def contrast(p, q, minL=0.0102, L=Y) -> float: return abs(L(p) - L(q))

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
      time.sleep(0.003)   # Give term 3ms to answer
      a = ""              # Read answer into `a`
      while ch := i.read(1): a += ch
      if m := re.search(pat, a):
        result.append(color(list(map(lambda s: int(s[:2], 16),
                                 m.groups()))))
  finally: tio.tcsetattr(i, tio.TCSADRAIN, ta0)
  return result

def fmtCon(r): return f"{r:.2f}"[1:]

if __name__== '__main__':
  lim = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
  L = Ls if len(sys.argv) > 2 else Y
  cs = getTtyColors(range(16))  # Lim surely depends on Ls v.Y
  for i, c in enumerate(cs):    # Lightness |difference| rather than ratio..
    (r, g, b) = c               #..may be more useful as a legibility score.
    print(f"Y: {Y(c):.4f} L*: {Ls(c):.4f} {i:2}: {r:.4f} {g:.4f} {b:.4f}")
  E = "\033"
  o = sys.stdout.write
  o("  ")
  for fbank in [3,9]:
    for fc in range(8): o(f"  {fbank}{fc}")
  o('\n')
  for B, bbank in enumerate([4,10]):    # dark|light BG banks
    for bc in  range(8):                # All BackGrounds
      i = 8*B + bc
      s = str(bbank) + str(bc)
      o(f"{E}[{s}m{s:3}")
      for b, fbank in enumerate([3,9]): # dark|light FG banks
        for fc in range(8):             # All ForeGrounds
          j = 8*b + fc
          s = str(fbank) + str(fc)
          con = contrast(cs[i], cs[j], L=L)
          o(f"{E}[{s}m {fmtCon(con)}" if con > lim else f"{E}[{s}m    ")
      o(f"{E}[m\n")
