#!/usr/bin/env python3
"""
CAT'S SPACE INVADERS 1.X
A.C Holdings / Team Flames - (C) 2026

A fixed-screen alien shooter engine in pygame-ce, styled like a Famicom game:
  * 256x240 logical screen, 2C02-style palette, 8-row tile sprites
  * 2x pulse + triangle + 15-bit LFSR noise synth (NES-APU style), 4-bit volume
  * locked 60 FPS game loop (F1 shows the FPS counter)

All sprites, sound effects and music in this file are ORIGINAL works made
for this game (space mice, space fish, space bats, mouse mothership, paw
shields). No Taito or Nintendo graphics, audio or code are used.

Requires: pip install pygame-ce
Controls: arrows / A-D move, Z / X / SPACE fire, P / ESC pause, F11 fullscreen
"""
import array
import math
import os
import random
import sys

import pygame

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
TITLE_TOP = "CAT'S"
TITLE_MID = "SPACE INVADERS"
TITLE_VER = "1.X"
VERSION = "1.0"
W, H = 256, 240
FPS = 60
RATE = 22050
HI_FILE = os.path.join(os.path.expanduser("~"), ".cats_space_invaders_hi")

COLS, ROWS = 11, 5
CELL_W, CELL_H = 16, 16
ROW_TYPE = [0, 1, 1, 2, 2]
POINTS = [30, 20, 10]
PLAYER_Y = 208
SHIELD_Y = 176
GROUND_Y = 222
EXTRA_LIFE_AT = 1500

# ----------------------------------------------------------------------------
# 2C02-style palette (common emulator RGB values)
# ----------------------------------------------------------------------------
NES = {
    0x00: (124, 124, 124), 0x01: (0, 0, 252), 0x02: (0, 0, 188), 0x03: (68, 40, 188),
    0x04: (148, 0, 132), 0x05: (168, 0, 32), 0x06: (168, 16, 0), 0x07: (136, 20, 0),
    0x08: (80, 48, 0), 0x09: (0, 120, 0), 0x0A: (0, 104, 0), 0x0B: (0, 88, 0),
    0x0C: (0, 64, 88), 0x0F: (0, 0, 0),
    0x10: (188, 188, 188), 0x11: (0, 120, 248), 0x12: (0, 88, 248), 0x13: (104, 68, 252),
    0x14: (216, 0, 204), 0x15: (228, 0, 88), 0x16: (248, 56, 0), 0x17: (228, 92, 16),
    0x18: (172, 124, 0), 0x19: (0, 184, 0), 0x1A: (0, 168, 0), 0x1B: (0, 168, 68),
    0x1C: (0, 136, 136),
    0x20: (248, 248, 248), 0x21: (60, 188, 252), 0x22: (104, 136, 252), 0x23: (152, 120, 248),
    0x24: (248, 120, 248), 0x25: (248, 88, 152), 0x26: (248, 120, 88), 0x27: (252, 160, 68),
    0x28: (248, 184, 0), 0x29: (184, 248, 24), 0x2A: (88, 216, 84), 0x2B: (88, 248, 152),
    0x2C: (0, 232, 216),
    0x30: (252, 252, 252), 0x31: (164, 228, 252), 0x32: (184, 184, 248), 0x33: (216, 184, 248),
    0x34: (248, 184, 248), 0x35: (248, 164, 192), 0x36: (240, 208, 176), 0x37: (252, 224, 168),
    0x38: (248, 216, 120), 0x39: (216, 248, 120), 0x3A: (184, 248, 184), 0x3B: (184, 248, 216),
    0x3C: (0, 252, 252),
}


def P(i):
    return NES[i]


BLACK, WHITE = P(0x0F), P(0x30)

# ----------------------------------------------------------------------------
# Original sprite art ('.' = transparent)
# ----------------------------------------------------------------------------
MOUSE = [[  # space mouse, 30 pts
    "XX........XX",
    "XpX......XpX",
    ".XXXXXXXXXX.",
    ".XrrXXXXrrX.",
    ".XXXXXXXXXX.",
    "..XXXppXXX..",
    "...XXXXXX...",
    "..X..XX..X..",
], [
    "XX........XX",
    "XpX......XpX",
    ".XXXXXXXXXX.",
    ".XrrXXXXrrX.",
    ".XXXXXXXXXX.",
    "..XXXppXXX..",
    "...XXXXXX...",
    ".X...XX...X.",
]]

FISH = [[  # space fish, 20 pts
    "............",
    "X.....XXXX..",
    "XX..XXXXXXX.",
    "XXXXXXXXwkXX",
    "XXXXoXoXXXXX",
    "XX..XXXXXXX.",
    "X.....XXXX..",
    "............",
], [
    "............",
    ".X....XXXX..",
    ".XX.XXXXXXX.",
    "XXXXXXXXwkXX",
    "XXXXXoXoXXXX",
    ".XX.XXXXXXX.",
    ".X....XXXX..",
    "............",
]]

BAT = [[  # space bat, 10 pts
    "X..........X",
    "XX..X..X..XX",
    "XXX.XXXX.XXX",
    "XXXXyXXyXXXX",
    ".XXXXXXXXXX.",
    "..XX.XX.XX..",
    "...X....X...",
    "............",
], [
    "............",
    "....X..X....",
    "...XXXXXX...",
    ".XXXyXXyXXX.",
    "XXXXXXXXXXXX",
    "XX.XXXXXX.XX",
    "X..X....X..X",
    "X..........X",
]]

SHIP = [  # cat-ear cannon
    "......w......",
    ".....XXX.....",
    ".p...XXX...p.",
    ".pp.XXXXX.pp.",
    ".XXXXXXXXXXX.",
    "XXXXX.X.XXXXX",
    "XXXXXXXXXXXXX",
    "XX.XXXXXXX.XX",
]

MOTHER = [[  # mouse mothership
    "..XX........XX..",
    ".XppX.XXXX.XppX.",
    ".XXXXXXXXXXXXXX.",
    "..XXwXXXXXXwXX..",
    "...XXXXXXXXXX...",
    "XXXXXXXXXXXXXXXX",
    ".y.y.y.y.y.y.y.y",
], [
    "..XX........XX..",
    ".XppX.XXXX.XppX.",
    ".XXXXXXXXXXXXXX.",
    "..XXwXXXXXXwXX..",
    "...XXXXXXXXXX...",
    "XXXXXXXXXXXXXXXX",
    "y.y.y.y.y.y.y.y.",
]]

CAT_FACE = [
    "X..........X",
    "XX........XX",
    "XpX......XpX",
    "XXXXXXXXXXXX",
    "XXwkXXXXwkXX",
    "XXwwXXXXwwXX",
    "XXXXXppXXXXX",
    "wXXXXXXXXXXw",
    ".XXXX..XXXX.",
    "..XXXXXXXX..",
]

BOOM_INV = [
    "..X...X...X.",
    "X..X..X..X..",
    ".X........X.",
    "...X....X...",
    "XX........XX",
    "...X....X...",
    ".X..X..X..X.",
    "X...X..X...X",
]

BOOM_SHIP = [[
    "..X......X...",
    "....X..X.....",
    "X..X.XX..X..X",
    "..XXXXXXXX...",
    ".XXX.XXXX.XX.",
    "XXXXXXXXXXXXX",
    "..X.XX.XX.X..",
    ".X..X...X..X.",
], [
    "X.....X.....X",
    "..X.X...X.X..",
    ".....X.X.....",
    "X.XXX.X.XXX.X",
    "..XX.XXX.XX..",
    ".XXXXX.XXXXX.",
    "XXX.XXXXX.XXX",
    "X.X.X.X.X.X.X",
]]

BURST = [
    "X...X.",
    "..X...",
    ".XXXX.",
    "XXXXXX",
    ".XXXX.",
    "..X..X",
    "X...X.",
]

EB_ART = [
    [[".X.", "X..", ".X.", "..X", ".X.", "X..", ".X."],
     [".X.", "..X", ".X.", "X..", ".X.", "..X", ".X."]],
    [[".X.", ".X.", "X.X", ".X.", ".X.", "X.X", ".X."],
     ["X.X", ".X.", ".X.", "X.X", ".X.", ".X.", "X.X"]],
    [[".X.", "XXX", ".X.", ".X.", "XXX", ".X.", ".X."],
     [".X.", ".X.", "XXX", ".X.", ".X.", "XXX", ".X."]],
]

# ----------------------------------------------------------------------------
# 5x7 bitmap font
# ----------------------------------------------------------------------------
FONT_SRC = {
    'A': ".###. #...# #...# ##### #...# #...# #...#",
    'B': "####. #...# #...# ####. #...# #...# ####.",
    'C': ".###. #...# #.... #.... #.... #...# .###.",
    'D': "####. #...# #...# #...# #...# #...# ####.",
    'E': "##### #.... #.... ####. #.... #.... #####",
    'F': "##### #.... #.... ####. #.... #.... #....",
    'G': ".###. #...# #.... #.### #...# #...# .####",
    'H': "#...# #...# #...# ##### #...# #...# #...#",
    'I': ".###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
    'J': "..### ...#. ...#. ...#. ...#. #..#. .##..",
    'K': "#...# #..#. #.#.. ##... #.#.. #..#. #...#",
    'L': "#.... #.... #.... #.... #.... #.... #####",
    'M': "#...# ##.## #.#.# #.#.# #...# #...# #...#",
    'N': "#...# ##..# #.#.# #..## #...# #...# #...#",
    'O': ".###. #...# #...# #...# #...# #...# .###.",
    'P': "####. #...# #...# ####. #.... #.... #....",
    'Q': ".###. #...# #...# #...# #.#.# #..#. .##.#",
    'R': "####. #...# #...# ####. #.#.. #..#. #...#",
    'S': ".#### #.... #.... .###. ....# ....# ####.",
    'T': "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    'U': "#...# #...# #...# #...# #...# #...# .###.",
    'V': "#...# #...# #...# #...# #...# .#.#. ..#..",
    'W': "#...# #...# #...# #.#.# #.#.# ##.## #...#",
    'X': "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    'Y': "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..",
    'Z': "##### ....# ...#. ..#.. .#... #.... #####",
    '0': ".###. #...# #..## #.#.# ##..# #...# .###.",
    '1': "..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.",
    '2': ".###. #...# ....# ...#. ..#.. .#... #####",
    '3': "####. ....# ....# .###. ....# ....# ####.",
    '4': "...#. ..##. .#.#. #..#. ##### ...#. ...#.",
    '5': "##### #.... ####. ....# ....# #...# .###.",
    '6': ".###. #.... #.... ####. #...# #...# .###.",
    '7': "##### ....# ...#. ..#.. .#... .#... .#...",
    '8': ".###. #...# #...# .###. #...# #...# .###.",
    '9': ".###. #...# #...# .#### ....# ....# .###.",
    '.': "..... ..... ..... ..... ..... .##.. .##..",
    ',': "..... ..... ..... ..... .##.. ..#.. .#...",
    '!': "..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..",
    '?': ".###. #...# ....# ...#. ..#.. ..... ..#..",
    '-': "..... ..... ..... ##### ..... ..... .....",
    ':': "..... .##.. .##.. ..... .##.. .##.. .....",
    "'": "..#.. ..#.. .#... ..... ..... ..... .....",
    '/': "....# ....# ...#. ..#.. .#... #.... #....",
    '(': "...#. ..#.. .#... .#... .#... ..#.. ...#.",
    ')': ".#... ..#.. ...#. ...#. ...#. ..#.. .#...",
    '>': ".#... ..#.. ...#. ....# ...#. ..#.. .#...",
    '<': "...#. ..#.. .#... #.... .#... ..#.. ...#.",
    '=': "..... ..... ##### ..... ##### ..... .....",
    '+': "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
    '*': "..... #.#.# .###. ##### .###. #.#.# .....",
    '_': "..... ..... ..... ..... ..... ..... #####",
    '@': ".###. #...# #.### #.#.# #.### #.... .###.",
    '&': ".##.. #..#. #.#.. .#... #.#.# #..#. .##.#",
    ' ': "..... ..... ..... ..... ..... ..... .....",
}


def make_sprite(rows, cmap):
    h = len(rows)
    w = max(len(r) for r in rows)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in cmap:
                s.set_at((x, y), cmap[ch])
    return s


class Font:
    def __init__(self):
        self.cache = {}

    def glyph(self, ch, color, scale):
        key = (ch, color, scale)
        g = self.cache.get(key)
        if g is None:
            rows = FONT_SRC.get(ch, FONT_SRC['?']).split()
            g = make_sprite(rows, {'#': color})
            if scale != 1:
                g = pygame.transform.scale(g, (5 * scale, 7 * scale))
            self.cache[key] = g
        return g

    def width(self, text, scale=1):
        return len(text) * 6 * scale - scale

    def draw(self, surf, text, x, y, color=WHITE, scale=1, align='left',
             shadow=None, colors=None):
        text = str(text).upper()
        adv = 6 * scale
        w = self.width(text, scale)
        if align == 'center':
            x -= w // 2
        elif align == 'right':
            x -= w
        for i, ch in enumerate(text):
            if ch == ' ':
                continue
            cx = x + i * adv
            if shadow is not None:
                surf.blit(self.glyph(ch, shadow, scale), (cx + scale, y + scale))
            c = colors[i % len(colors)] if colors else color
            surf.blit(self.glyph(ch, c, scale), (cx, y))
        return w


# ----------------------------------------------------------------------------
# NES-APU-style synthesizer
# ----------------------------------------------------------------------------
CPU_HZ = 1789773
NOISE_PERIODS = [4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068]
DUTY = {0: 0.125, 1: 0.25, 2: 0.5, 3: 0.75}
SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nf(n):
    """Note name -> Hz, e.g. 'A4', 'G#3', 'Bb2'."""
    s = SEMI[n[0]]
    i = 1
    if n[1] == '#':
        s += 1
        i = 2
    elif n[1] == 'b':
        s -= 1
        i = 2
    midi = 12 * (int(n[i:]) + 1) + s
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def cat(*tracks):
    out = []
    for t in tracks:
        out.extend(t)
    return out


CH = {'march': 0, 'shoot': 1, 'inv_die': 2, 'ufo': 3, 'p_die': 4,
      'sfx': 5, 'music': 6, 'shield': 7}


class APU:
    def __init__(self):
        self.ok = False
        self.sfx = {}
        init = pygame.mixer.get_init()
        if not init:
            return
        self.rate, self.fmt, self.ch = init
        if self.fmt not in (-16, 32):
            return
        try:
            pygame.mixer.set_num_channels(12)
            pygame.mixer.set_reserved(8)
            self.build()
            self.ok = True
        except Exception as exc:  # audio is optional
            print("audio disabled:", exc)

    # --- channel generators -------------------------------------------------
    def _n(self, dur):
        return max(1, int(round(dur * self.rate)))

    def silence(self, dur):
        return [0.0] * self._n(dur)

    def pulse(self, freq, dur, duty=2, vol=0.6, decay=0.0, sweep=0.0, gate=1.0):
        n = self._n(dur)
        r = self.rate
        d = DUTY[duty]
        out = [0.0] * n
        ph, f = 0.0, freq
        k = 2.0 ** (sweep / r) if sweep else 1.0
        for i in range(int(n * gate)):
            e = vol - decay * (i / r)
            if e <= 0 or f < 20 or f > 12000:
                break
            e = int(e * 15 + 0.5) / 15.0          # 4-bit volume
            out[i] = e if ph < d else -e
            ph += f / r
            if ph >= 1.0:
                ph -= int(ph)
            f *= k
        return out

    def tri(self, freq, dur, vol=0.8, decay=0.0, sweep=0.0, gate=1.0):
        n = self._n(dur)
        r = self.rate
        out = [0.0] * n
        ph, f = 0.0, freq
        k = 2.0 ** (sweep / r) if sweep else 1.0
        for i in range(int(n * gate)):
            e = vol - decay * (i / r)
            if e <= 0 or f < 20:
                break
            step = int(ph * 32)                    # 32-step triangle
            v = (15 - step) if step < 16 else (step - 16)
            out[i] = (v / 7.5 - 1.0) * e
            ph += f / r
            if ph >= 1.0:
                ph -= int(ph)
            f *= k
        return out

    def noise(self, dur, p0, p1=None, vol=0.6, decay=0.0, short=False):
        n = self._n(dur)
        r = self.rate
        out = [0.0] * n
        p1 = p0 if p1 is None else p1
        steps = [CPU_HZ / p / r for p in NOISE_PERIODS]
        tap = 6 if short else 1
        lfsr, acc = 1, 0.0
        for i in range(n):
            e = vol - decay * (i / r)
            if e <= 0:
                break
            e = int(e * 15 + 0.5) / 15.0
            acc += steps[min(15, int(p0 + (p1 - p0) * i / n))]
            while acc >= 1.0:
                acc -= 1.0
                fb = (lfsr ^ (lfsr >> tap)) & 1
                lfsr = (lfsr >> 1) | (fb << 14)
            out[i] = -e if (lfsr & 1) else e
        return out

    def make(self, samples, gain=0.4):
        if self.fmt == 32:
            a = array.array('f', (max(-1.0, min(1.0, v * gain)) for v in samples))
            z = 0.0
        else:
            a = array.array('h', (int(max(-1.0, min(1.0, v * gain)) * 32767) for v in samples))
            z = 0
        if self.ch > 1:
            b = array.array(a.typecode, [z]) * (len(a) * self.ch)
            for c in range(self.ch):
                b[c::self.ch] = a
            a = b
        return pygame.mixer.Sound(buffer=a.tobytes())

    # --- sound bank (all original) -----------------------------------------
    def build(self):
        S = self.sfx
        S['shoot'] = self.make(mix(self.pulse(1400, .14, 1, .6, 3.5, sweep=-9),
                                   self.noise(.04, 3, vol=.25, decay=6)), .45)
        S['inv_die'] = self.make(mix(self.noise(.28, 3, 9, .7, 2.5),
                                     self.pulse(520, .16, 0, .45, 2.8, sweep=-6)), .5)
        warble = []
        for k in range(12):
            warble += self.pulse(740 if k % 2 == 0 else 990, 1 / 30, 1, .35)
        S['ufo'] = self.make(warble, .35)
        S['ufo_hit'] = self.make(mix(cat(*[self.pulse(nf(n), .05, 1, .5) for n in
                                           ('C6', 'G6', 'E6', 'C7', 'G6', 'C7')]),
                                     self.noise(.3, 4, 10, .4, 1.4)), .45)
        S['p_die'] = self.make(mix(self.noise(1.3, 5, 14, .8, .6),
                                   self.pulse(700, 1.0, 2, .4, .4, sweep=-3.0)), .5)
        S['march'] = [self.make(self.tri(nf(n), .11, .9, decay=6), .8)
                      for n in ('A2', 'C3', 'G2', 'F2')]
        S['move'] = self.make(self.pulse(1760, .035, 1, .4), .4)
        S['select'] = self.make(cat(self.pulse(nf('E6'), .06, 1, .5),
                                    self.pulse(nf('B6'), .14, 1, .5, decay=3)), .4)
        S['extra'] = self.make(cat(*[self.pulse(nf(n), .055, 1, .5) for n in
                                     ('C6', 'E6', 'G6', 'C7', 'G6', 'C7')]), .45)
        S['clear'] = self.make(mix(
            cat(*[self.pulse(nf(n), .09, 1, .5) for n in ('G5', 'C6', 'E6', 'G6')],
                self.silence(.09), self.pulse(nf('E6'), .09, 1, .5),
                self.pulse(nf('G6'), .45, 1, .5, decay=1)),
            cat(self.tri(nf('C3'), .36, .8), self.tri(nf('G2'), .18, .8),
                self.tri(nf('C3'), .45, .8, decay=1.5))), .45)
        S['gameover'] = self.make(mix(
            cat(*[self.pulse(nf(n), .22, 2, .45, gate=.9) for n in ('E5', 'D5', 'C5', 'B4')],
                self.pulse(nf('A4'), .7, 2, .45, decay=.6)),
            cat(*[self.tri(nf(n), .22, .8, gate=.9) for n in ('A3', 'G3', 'F3', 'E3')],
                self.tri(nf('A2'), .7, .8, decay=1))), .45)
        S['shield'] = self.make(self.noise(.05, 6, vol=.4, decay=8), .4)
        S['clash'] = self.make(self.noise(.08, 2, 6, .5, 5), .4)
        S['pause'] = self.make(cat(self.pulse(nf('A5'), .05, 2, .4), self.silence(.03),
                                   self.pulse(nf('A6'), .08, 2, .4)), .4)
        S['music'] = self.make(self.title_theme(), .32)

    def title_theme(self):
        """Original 8-bar A-minor title loop: pulse lead, triangle bass, noise drums."""
        r = self.rate
        spe = int(round(60 / 150 / 2 * r))      # samples per eighth @150 BPM
        lead = [
            ('A4', 1), ('C5', 1), ('E5', 1), ('A5', 1), ('G5', 1), ('E5', 1), ('C5', 1), ('D5', 1),
            ('E5', 2), ('D5', 1), ('C5', 1), ('B4', 2), ('G4', 2),
            ('A4', 1), ('C5', 1), ('E5', 1), ('A5', 1), ('B5', 1), ('A5', 1), ('G5', 1), ('E5', 1),
            ('F5', 1), ('E5', 1), ('D5', 1), ('B4', 1), ('C5', 2), ('A4', 2),
            ('F5', 2), ('E5', 1), ('F5', 1), ('G5', 2), ('E5', 2),
            ('D5', 2), ('C5', 1), ('D5', 1), ('E5', 2), ('C5', 2),
            ('B4', 1), ('C5', 1), ('D5', 1), ('E5', 1), ('F5', 1), ('E5', 1), ('D5', 1), ('C5', 1),
            ('B4', 2), ('G#4', 2), ('A4', 4),
        ]
        bars = [['A2', 'A3'] * 4, ['E2', 'E3'] * 4, ['A2', 'A3'] * 4,
                ['D2', 'D3'] * 2 + ['A2', 'A3'] * 2, ['F2', 'F3'] * 4,
                ['C2', 'C3'] * 4, ['G2', 'G3'] * 4, ['E2', 'E3'] * 2 + ['A2', 'A3'] * 2]
        lead_t = []
        for n, l in lead:
            d = spe * l / r
            lead_t += self.pulse(nf(n), d, 1, .5, decay=.25 / d, gate=.85)
        bass_t = []
        for bar in bars:
            for n in bar:
                bass_t += self.tri(nf(n), spe / r, .8, gate=.9)
        total = spe * 64
        drums = [0.0] * total
        for i in range(64):
            if i % 4 == 0:
                hit = self.tri(170, .08, .9, sweep=-14)
            elif i % 4 == 2:
                hit = self.noise(.09, 5, vol=.45, decay=5)
            else:
                hit = self.noise(.025, 1, vol=.18, decay=7)
            pos = i * spe
            for j, v in enumerate(hit):
                if pos + j < total:
                    drums[pos + j] += v
        return mix(lead_t[:total], bass_t[:total], drums)

    # --- playback -----------------------------------------------------------
    def play(self, name, idx=None, loops=0):
        if not self.ok:
            return
        s = self.sfx[name]
        if idx is not None:
            s = s[idx]
        pygame.mixer.Channel(CH.get(name, CH['sfx'])).play(s, loops=loops)

    def stop(self, name):
        if self.ok:
            pygame.mixer.Channel(CH.get(name, CH['sfx'])).stop()

    def stop_all(self):
        if self.ok:
            pygame.mixer.stop()

    def music(self, on):
        if not self.ok:
            return
        chn = pygame.mixer.Channel(CH['music'])
        if on and not chn.get_busy():
            chn.play(self.sfx['music'], loops=-1)
        elif not on:
            chn.stop()

    def pause_game_channels(self, paused):
        if not self.ok:
            return
        for n in ('march', 'shoot', 'inv_die', 'ufo', 'p_die', 'shield'):
            c = pygame.mixer.Channel(CH[n])
            c.pause() if paused else c.unpause()


# ----------------------------------------------------------------------------
# Destructible paw-print shield
# ----------------------------------------------------------------------------
def paw_mask(w=22, h=16):
    m = [[False] * w for _ in range(h)]

    def disc(cx, cy, rx, ry):
        for y in range(h):
            for x in range(w):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1.0:
                    m[y][x] = True
    disc(11, 11.2, 8.5, 5.0)          # main pad
    disc(3.2, 6.2, 2.8, 3.3)          # toe beans
    disc(8.2, 3.3, 2.8, 3.3)
    disc(13.8, 3.3, 2.8, 3.3)
    disc(18.8, 6.2, 2.8, 3.3)
    return m


class Shield:
    W, H = 22, 16

    def __init__(self, x, y, template, color):
        self.x, self.y = x, y
        self.m = [row[:] for row in template]
        self.color = color
        self.surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.dirty = True

    def rect(self):
        return pygame.Rect(self.x, self.y, self.W, self.H)

    def image(self):
        if self.dirty:
            self.surf.fill((0, 0, 0, 0))
            for yy, row in enumerate(self.m):
                for xx, v in enumerate(row):
                    if v:
                        self.surf.set_at((xx, yy), self.color)
            self.dirty = False
        return self.surf

    def hit(self, r, from_below=False):
        c = self.rect().clip(r)
        if c.w <= 0 or c.h <= 0:
            return None
        ys = range(c.bottom - 1, c.top - 1, -1) if from_below else range(c.top, c.bottom)
        for yy in ys:
            for xx in range(c.left, c.right):
                if self.m[yy - self.y][xx - self.x]:
                    return xx - self.x, yy - self.y
        return None

    def crater(self, lx, ly, rad=3):
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                d2 = dx * dx + dy * dy
                if d2 <= rad * rad and (d2 <= 2 or random.random() < .7):
                    x, y = lx + dx, ly + dy
                    if 0 <= x < self.W and 0 <= y < self.H:
                        self.m[y][x] = False
        self.dirty = True

    def erase(self, r):
        c = self.rect().clip(r)
        if c.w <= 0 or c.h <= 0:
            return
        for yy in range(c.top, c.bottom):
            for xx in range(c.left, c.right):
                self.m[yy - self.y][xx - self.x] = False
        self.dirty = True


class EBullet:
    __slots__ = ('x', 'y', 'kind', 'anim')

    def __init__(self, x, y, kind):
        self.x, self.y, self.kind, self.anim = x, float(y), kind, 0

    def rect(self):
        return pygame.Rect(self.x, int(self.y), 3, 7)


def load_hi():
    try:
        with open(HI_FILE) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def save_hi(v):
    try:
        with open(HI_FILE, 'w') as f:
            f.write(str(int(v)))
    except Exception:
        pass


# ----------------------------------------------------------------------------
# Game
# ----------------------------------------------------------------------------
class Game:
    MENU = ['PLAY GAME', 'HELP', 'ABOUT', 'EXIT']

    def __init__(self, screen):
        self.c = screen
        self.font = Font()
        self.apu = APU()
        self.build_sprites()
        self.paw = paw_mask()
        self.stars = [[random.randrange(W), random.randrange(24, GROUND_Y), random.randrange(80)]
                      for _ in range(48)]
        self.hiscore = load_hi()
        self.state = 'menu'
        self.menu_idx = 0
        self.frame = 0
        self.show_fps = False
        self.fps_value = 0.0
        self.running = True
        self.joy_x = 0
        self.joy_fire = False
        self.joys = []
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            self.joys.append(pygame.joystick.Joystick(i))
        self.reset_vars()
        self.apu.music(True)

    # --- setup --------------------------------------------------------------
    def build_sprites(self):
        mk = make_sprite
        self.inv_spr = [
            [mk(f, {'X': P(0x10), 'p': P(0x25), 'r': P(0x16)}) for f in MOUSE],
            [mk(f, {'X': P(0x21), 'o': P(0x11), 'w': WHITE, 'k': P(0x02)}) for f in FISH],
            [mk(f, {'X': P(0x24), 'y': P(0x28)}) for f in BAT],
        ]
        self.ship = mk(SHIP, {'X': P(0x2A), 'w': WHITE, 'p': P(0x25)})
        self.ship_small = self.ship
        self.mother = [mk(f, {'X': P(0x16), 'p': P(0x35), 'w': WHITE, 'y': P(0x28)})
                       for f in MOTHER]
        self.cat_face = mk(CAT_FACE, {'X': P(0x27), 'p': P(0x25), 'w': WHITE, 'k': BLACK})
        self.boom_inv = mk(BOOM_INV, {'X': WHITE})
        self.boom_ship = [mk(f, {'X': P(0x2A)}) for f in BOOM_SHIP]
        self.burst_w = mk(BURST, {'X': WHITE})
        self.burst_r = mk(BURST, {'X': P(0x16)})
        eb_cols = [P(0x30), P(0x38), P(0x3C)]
        self.eb_spr = [[mk(f, {'X': eb_cols[k]}) for f in EB_ART[k]] for k in range(3)]

    def reset_vars(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.alive = [[True] * COLS for _ in range(ROWS)]
        self.alive_n = COLS * ROWS
        self.fx, self.fy, self.dir = 40, 48, 1
        self.step_timer = 30
        self.anim = 0
        self.march_i = 0
        self.player_x = 121.0
        self.pbullet = None
        self.ebullets = []
        self.fire_cd = 60
        self.ufo = None
        self.ufo_timer = 1500
        self.fx_list = []      # [x, y, surface, timer]
        self.popups = []       # [x, y, text, timer]
        self.shields = []
        self.dying = 0
        self.ready = 0
        self.banner = False
        self.clear_timer = 0
        self.go_timer = 0
        self.new_hi = False

    def new_game(self):
        self.apu.music(False)
        self.reset_vars()
        self.start_wave()
        self.state = 'play'

    def start_wave(self):
        self.alive = [[True] * COLS for _ in range(ROWS)]
        self.alive_n = COLS * ROWS
        self.fx = (W - COLS * CELL_W) // 2
        self.fy = 48 + 8 * min(self.level - 1, 5)
        self.dir = 1
        self.step_timer = 20
        self.anim = 0
        self.pbullet = None
        self.ebullets = []
        self.fire_cd = 90
        self.ufo = None
        self.apu.stop('ufo')
        self.ufo_timer = random.randint(1300, 2100)
        self.shields = [Shield(cx - 11, SHIELD_Y, self.paw, P(0x35))
                        for cx in (43, 99, 157, 213)]
        self.player_x = 121.0
        self.ready = 100
        self.banner = True

    # --- helpers ------------------------------------------------------------
    def inv_rect(self, r, c):
        return pygame.Rect(self.fx + c * CELL_W + 2, self.fy + r * CELL_H, 12, 8)

    def alive_cols(self):
        return [c for c in range(COLS) if any(self.alive[r][c] for r in range(ROWS))]

    def bottom_row(self):
        for r in range(ROWS - 1, -1, -1):
            if any(self.alive[r]):
                return r
        return -1

    def step_interval(self):
        lf = max(0.45, 1.0 - 0.07 * (self.level - 1))
        return max(1, int(1 + self.alive_n * 0.32 * lf))

    def max_ebullets(self):
        return 2 + (self.level >= 3) + (self.level >= 6)

    def player_rect(self):
        return pygame.Rect(int(self.player_x) + 1, PLAYER_Y + 2, 11, 6)

    def add_score(self, pts):
        old = self.score
        self.score += pts
        if old < EXTRA_LIFE_AT <= self.score:
            self.lives += 1
            self.apu.play('extra')
        if self.score > self.hiscore:
            self.hiscore = self.score
            self.new_hi = True

    def boom(self, x, y, surf, t=16):
        self.fx_list.append([x, y, surf, t])

    # --- input --------------------------------------------------------------
    def on_key(self, k):
        st = self.state
        if st == 'menu':
            if k in (pygame.K_UP, pygame.K_w):
                self.menu_idx = (self.menu_idx - 1) % len(self.MENU)
                self.apu.play('move')
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.menu_idx = (self.menu_idx + 1) % len(self.MENU)
                self.apu.play('move')
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_z, pygame.K_SPACE):
                self.apu.play('select')
                self.menu_select()
            elif k == pygame.K_ESCAPE:
                self.menu_idx = 3
                self.apu.play('move')
        elif st in ('help', 'about'):
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_z,
                     pygame.K_x, pygame.K_SPACE, pygame.K_BACKSPACE):
                self.state = 'menu'
                self.apu.play('move')
        elif st == 'play':
            if k in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                self.state = 'pause'
                self.apu.pause_game_channels(True)
                self.apu.play('pause')
        elif st == 'pause':
            if k in (pygame.K_p, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = 'play'
                self.apu.play('pause')
                self.apu.pause_game_channels(False)
            elif k == pygame.K_ESCAPE:
                self.to_menu()
        elif st == 'gameover':
            if self.go_timer <= 0 and k in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                             pygame.K_z, pygame.K_SPACE, pygame.K_ESCAPE):
                self.to_menu()

    def menu_select(self):
        choice = self.MENU[self.menu_idx]
        if choice == 'PLAY GAME':
            self.new_game()
        elif choice == 'HELP':
            self.state = 'help'
        elif choice == 'ABOUT':
            self.state = 'about'
        else:
            self.running = False

    def to_menu(self):
        save_hi(self.hiscore)
        self.apu.stop_all()
        self.state = 'menu'
        self.apu.music(True)

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_F11 or (e.key == pygame.K_RETURN and e.mod & pygame.KMOD_ALT):
                pygame.display.toggle_fullscreen()
            elif e.key == pygame.K_F1:
                self.show_fps = not self.show_fps
            else:
                self.on_key(e.key)
        elif e.type == pygame.JOYDEVICEADDED:
            self.joys.append(pygame.joystick.Joystick(e.device_index))
        elif e.type == pygame.JOYAXISMOTION and e.axis == 0:
            self.joy_x = -1 if e.value < -.5 else (1 if e.value > .5 else 0)
        elif e.type == pygame.JOYHATMOTION:
            self.joy_x = e.value[0]
            if e.value[1] == 1:
                self.on_key(pygame.K_UP)
            elif e.value[1] == -1:
                self.on_key(pygame.K_DOWN)
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button in (0, 1, 2, 3):
                self.joy_fire = True
                if self.state != 'play':
                    self.on_key(pygame.K_z)
            elif e.button in (7, 9):
                self.on_key(pygame.K_RETURN)
            elif e.button in (6, 8):
                self.on_key(pygame.K_ESCAPE)
        elif e.type == pygame.JOYBUTTONUP and e.button in (0, 1, 2, 3):
            self.joy_fire = False

    # --- update -------------------------------------------------------------
    def update(self):
        self.frame += 1
        if self.state == 'play':
            self.update_play()
        elif self.state == 'gameover':
            if self.go_timer > 0:
                self.go_timer -= 1
            self.update_fx()

    def update_fx(self):
        for b in self.fx_list:
            b[3] -= 1
        self.fx_list = [b for b in self.fx_list if b[3] > 0]
        for p in self.popups:
            p[3] -= 1
        self.popups = [p for p in self.popups if p[3] > 0]

    def update_play(self):
        self.update_fx()
        if self.clear_timer:
            self.clear_timer -= 1
            if self.clear_timer == 0:
                self.level += 1
                self.start_wave()
            return
        if self.dying:
            self.dying -= 1
            if self.dying == 0:
                if self.lives <= 0:
                    self.to_gameover()
                else:
                    self.player_x = 121.0
                    self.ebullets = []
                    self.ready = 60
                    self.banner = False
            return
        if self.ready:
            self.ready -= 1
            return

        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a] or self.joy_x < 0
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d] or self.joy_x > 0
        fire = keys[pygame.K_z] or keys[pygame.K_x] or keys[pygame.K_SPACE] or self.joy_fire
        if left and not right:
            self.player_x -= 1.25
        elif right and not left:
            self.player_x += 1.25
        self.player_x = max(8.0, min(W - 8 - 13, self.player_x))
        if fire and self.pbullet is None:
            self.pbullet = [int(self.player_x) + 6, PLAYER_Y - 4]
            self.apu.play('shoot')

        self.update_pbullet()
        if self.alive_n == 0:
            self.wave_clear()
            return
        self.update_invaders()
        if self.dying:
            return
        self.update_enemy_fire()
        self.update_ebullets()
        self.update_ufo()

    def wave_clear(self):
        self.clear_timer = 150
        self.pbullet = None
        self.ebullets = []
        if self.ufo:
            self.ufo = None
            self.apu.stop('ufo')
        self.apu.play('clear')

    def update_pbullet(self):
        b = self.pbullet
        if b is None:
            return
        for _ in range(2):                      # 4 px/frame in 2 px substeps
            b[1] -= 2
            r = pygame.Rect(b[0], b[1], 1, 4)
            if b[1] < 26:
                self.boom(b[0] - 3, 26, self.burst_r, 12)
                self.pbullet = None
                return
            if self.ufo:
                ur = pygame.Rect(int(self.ufo[0]), 30, 16, 7)
                if ur.colliderect(r):
                    pts = random.choice((50, 100, 150, 100, 50, 300))
                    self.add_score(pts)
                    self.popups.append([ur.centerx, 31, str(pts), 70])
                    self.boom(ur.x + 2, 29, self.boom_inv, 20)
                    self.ufo = None
                    self.apu.stop('ufo')
                    self.apu.play('ufo_hit')
                    self.pbullet = None
                    return
            for rr in range(ROWS):
                row = self.alive[rr]
                for cc in range(COLS):
                    if row[cc]:
                        ir = self.inv_rect(rr, cc)
                        if ir.colliderect(r):
                            row[cc] = False
                            self.alive_n -= 1
                            self.add_score(POINTS[ROW_TYPE[rr]])
                            self.boom(ir.x, ir.y, self.boom_inv, 16)
                            self.apu.play('inv_die')
                            self.pbullet = None
                            return
            for eb in self.ebullets:
                if eb.rect().colliderect(r):
                    self.ebullets.remove(eb)
                    self.boom(b[0] - 3, b[1] - 2, self.burst_w, 10)
                    self.apu.play('clash')
                    self.pbullet = None
                    return
            for s in self.shields:
                p = s.hit(r, from_below=True)
                if p:
                    s.crater(p[0], p[1] - 1)
                    self.apu.play('shield')
                    self.pbullet = None
                    return

    def update_invaders(self):
        self.step_timer -= 1
        if self.step_timer > 0:
            return
        self.step_timer = self.step_interval()
        self.anim ^= 1
        self.apu.play('march', self.march_i)
        self.march_i = (self.march_i + 1) % 4
        cols = self.alive_cols()
        minx = self.fx + cols[0] * CELL_W + 2
        maxx = self.fx + cols[-1] * CELL_W + 14
        if (self.dir > 0 and maxx + 2 > W - 8) or (self.dir < 0 and minx - 2 < 8):
            self.fy += 8
            self.dir = -self.dir
        else:
            self.fx += 2 * self.dir
        bottom = self.fy + self.bottom_row() * CELL_H + 8
        if bottom >= SHIELD_Y:
            for rr in range(ROWS):
                for cc in range(COLS):
                    if self.alive[rr][cc]:
                        ir = self.inv_rect(rr, cc)
                        for s in self.shields:
                            s.erase(ir)
        if bottom >= PLAYER_Y:
            self.lives = 0
            self.kill_player()

    def update_enemy_fire(self):
        self.fire_cd -= 1
        if self.fire_cd > 0 or len(self.ebullets) >= self.max_ebullets():
            return
        cols = self.alive_cols()
        pc = self.player_x + 6
        if random.random() < 0.35:
            c = min(cols, key=lambda c: abs(self.fx + c * CELL_W + 8 - pc))
        else:
            c = random.choice(cols)
        r = max(r for r in range(ROWS) if self.alive[r][c])
        self.ebullets.append(EBullet(self.fx + c * CELL_W + 7, self.fy + r * CELL_H + 8,
                                     random.randrange(3)))
        f = max(0.4, 1.0 - 0.08 * (self.level - 1))
        self.fire_cd = random.randint(int(25 * f), int(65 * f))

    def update_ebullets(self):
        spd = min(3.0, 1.4 + 0.12 * (self.level - 1))
        pr = self.player_rect()
        for eb in list(self.ebullets):
            eb.y += spd
            eb.anim += 1
            r = eb.rect()
            if r.bottom >= GROUND_Y:
                self.ebullets.remove(eb)
                self.boom(eb.x - 1, GROUND_Y - 8, self.burst_w, 10)
                continue
            hit_shield = False
            for s in self.shields:
                p = s.hit(r)
                if p:
                    s.crater(p[0], p[1] + 1)
                    hit_shield = True
                    break
            if hit_shield:
                self.ebullets.remove(eb)
                continue
            if r.colliderect(pr):
                self.ebullets.remove(eb)
                self.lives -= 1
                self.kill_player()
                return

    def kill_player(self):
        self.dying = 130
        self.pbullet = None
        if self.ufo:
            self.ufo = None
            self.apu.stop('ufo')
        self.apu.play('p_die')

    def update_ufo(self):
        if self.ufo is None:
            if self.alive_n >= 8:
                self.ufo_timer -= 1
            if self.ufo_timer <= 0:
                d = random.choice((-1, 1))
                self.ufo = [-16.0 if d > 0 else float(W), d]
                self.ufo_timer = random.randint(1300, 2100)
                self.apu.play('ufo', loops=-1)
        else:
            self.ufo[0] += 0.75 * self.ufo[1]
            if self.ufo[0] < -17 or self.ufo[0] > W + 1:
                self.ufo = None
                self.apu.stop('ufo')

    def to_gameover(self):
        self.state = 'gameover'
        self.go_timer = 60
        save_hi(self.hiscore)
        self.apu.stop_all()
        self.apu.play('gameover')

    # --- drawing ------------------------------------------------------------
    def draw_stars(self, dim=True):
        cols = (P(0x02), P(0x0C), P(0x00)) if dim else (P(0x00), P(0x10), P(0x30), P(0x21))
        for sx, sy, ph in self.stars:
            k = ((self.frame + ph * 4) // 24) % len(cols)
            self.c.set_at((sx, sy), cols[k])

    def draw(self):
        self.c.fill(BLACK)
        st = self.state
        if st == 'menu':
            self.draw_menu()
        elif st == 'help':
            self.draw_help()
        elif st == 'about':
            self.draw_about()
        else:
            self.draw_play()
            if st == 'pause':
                self.panel(64, 96, 128, 44)
                self.font.draw(self.c, "PAUSED", 128, 103, P(0x28), 2, 'center')
                self.font.draw(self.c, "ENTER:RESUME ESC:MENU", 128, 125, WHITE, 1, 'center')
            elif st == 'gameover':
                self.panel(48, 84, 160, 68)
                self.font.draw(self.c, "GAME OVER", 128, 92, P(0x16), 2, 'center', P(0x07))
                self.font.draw(self.c, "SCORE %05d" % self.score, 128, 114, WHITE, 1, 'center')
                if self.new_hi:
                    col = P(0x28) if (self.frame // 8) % 2 else P(0x27)
                    self.font.draw(self.c, "NEW HI-SCORE!", 128, 126, col, 1, 'center')
                if self.go_timer <= 0 and (self.frame // 20) % 2 == 0:
                    self.font.draw(self.c, "PRESS ENTER", 128, 140, P(0x21), 1, 'center')
        if self.show_fps:
            self.font.draw(self.c, "%2.0f FPS" % self.fps_value, W - 2, H - 9, P(0x29), 1, 'right')

    def panel(self, x, y, w, h):
        pygame.draw.rect(self.c, BLACK, (x, y, w, h))
        pygame.draw.rect(self.c, P(0x12), (x, y, w, h), 1)
        pygame.draw.rect(self.c, P(0x21), (x + 2, y + 2, w - 4, h - 4), 1)

    def draw_menu(self):
        f, c = self.font, self.c
        self.draw_stars(dim=False)
        f.draw(c, "HI-SCORE %05d" % self.hiscore, 128, 4, P(0x10), 1, 'center')
        bob = int(round(math.sin(self.frame / 20.0) * 2))
        f.draw(c, TITLE_TOP, 128, 18 + bob, P(0x28), 3, 'center', P(0x16))
        tw = f.width(TITLE_TOP, 3)
        c.blit(self.cat_face, (128 - tw // 2 - 20, 22 + bob))
        c.blit(self.cat_face, (128 + tw // 2 + 8, 22 + bob))
        cyc = [P(i) for i in (0x21, 0x2C, 0x2B, 0x29, 0x28, 0x27, 0x26, 0x25, 0x24, 0x23, 0x22)]
        o = self.frame // 5
        rot = cyc[o % len(cyc):] + cyc[:o % len(cyc)]
        f.draw(c, TITLE_MID, 128, 46, scale=2, align='center', shadow=P(0x02), colors=rot)
        f.draw(c, TITLE_VER, 128, 64, P(0x31), 2, 'center', P(0x02))

        a = (self.frame // 30) % 2
        table = [(self.mother[a], "= ??? MYSTERY"),
                 (self.inv_spr[0][a], "= 30 POINTS"),
                 (self.inv_spr[1][a], "= 20 POINTS"),
                 (self.inv_spr[2][a], "= 10 POINTS")]
        for i, (spr, text) in enumerate(table):
            yy = 88 + i * 12
            c.blit(spr, (84 - spr.get_width() // 2, yy))
            f.draw(c, text, 98, yy, P(0x10))

        for i, item in enumerate(self.MENU):
            yy = 144 + i * 13
            sel = i == self.menu_idx
            f.draw(c, item, 128, yy, P(0x30) if sel else P(0x00), 1, 'center')
            if sel and (self.frame // 16) % 2 == 0:
                c.blit(self.ship, (128 - f.width(item) // 2 - 18, yy - 1))
        f.draw(c, "(C) 2026 A.C HOLDINGS / TEAM FLAMES", 128, 214, P(0x00), 1, 'center')
        f.draw(c, "ORIGINAL ART & SOUND - 60 FPS", 128, 225, P(0x12), 1, 'center')

    def draw_text_page(self, title, lines):
        f, c = self.font, self.c
        self.draw_stars()
        f.draw(c, title, 128, 12, P(0x28), 2, 'center', P(0x16))
        y = 38
        for ln in lines:
            if isinstance(ln, tuple):
                txt, col = ln
            else:
                txt, col = ln, P(0x30)
            f.draw(c, txt, 128, y, col, 1, 'center')
            y += 10
        if (self.frame // 20) % 2 == 0:
            f.draw(c, "PRESS ENTER OR ESC TO RETURN", 128, 224, P(0x21), 1, 'center')

    def draw_help(self):
        self.draw_text_page("HOW TO PLAY", [
            ("STOP THE SPACE MICE FLEET", P(0x31)),
            ("BEFORE IT LANDS ON CAT PLANET!", P(0x31)),
            "",
            "LEFT/RIGHT OR A/D ..... MOVE",
            "Z / X / SPACE ......... FIRE",
            "P / ESC / ENTER ...... PAUSE",
            "F11 .............. FULLSCREEN",
            "F1 ................ FPS METER",
            "GAMEPAD: D-PAD + A, START",
            "",
            ("PAW SHIELDS BLOCK SHOTS BUT CRUMBLE.", P(0x35)),
            ("SHOOT THE MOTHERSHIP FOR BONUS.", P(0x35)),
            ("EXTRA LIFE AT %d POINTS." % EXTRA_LIFE_AT, P(0x35)),
            ("THE FLEET SPEEDS UP AS IT SHRINKS.", P(0x35)),
            ("IF THEY REACH THE GROUND: GAME OVER", P(0x26)),
        ])

    def draw_about(self):
        self.draw_text_page("ABOUT", [
            ("CAT'S SPACE INVADERS 1.X  V" + VERSION, P(0x28)),
            "A.C HOLDINGS / TEAM FLAMES",
            "",
            ("ENGINE: PYTHON + PYGAME-CE", P(0x21)),
            ("256X240 @ 60 FPS, 2C02-STYLE PALETTE", P(0x21)),
            ("2X PULSE + TRIANGLE + NOISE SYNTH", P(0x21)),
            "",
            ("COPYRIGHT (C) 2026 A.C HOLDINGS.", P(0x2A)),
            "ALL SPRITES, MUSIC AND SOUND ARE",
            "ORIGINAL WORKS MADE FOR THIS GAME.",
            "",
            ("NOT AFFILIATED WITH OR ENDORSED BY", P(0x10)),
            ("TAITO OR NINTENDO. SPACE INVADERS IS", P(0x10)),
            ("A TRADEMARK OF TAITO CORPORATION.", P(0x10)),
            ("FAMICOM IS A TRADEMARK OF NINTENDO.", P(0x10)),
        ])

    def draw_play(self):
        f, c = self.font, self.c
        self.draw_stars()
        # HUD
        f.draw(c, "SCORE<1>", 8, 4, WHITE)
        f.draw(c, "%05d" % self.score, 8, 14, P(0x28))
        f.draw(c, "HI-SCORE", 128, 4, WHITE, 1, 'center')
        f.draw(c, "%05d" % self.hiscore, 128, 14, P(0x27), 1, 'center')
        f.draw(c, "WAVE", 248, 4, WHITE, 1, 'right')
        f.draw(c, "%02d" % self.level, 248, 14, P(0x21), 1, 'right')
        # shields
        for s in self.shields:
            c.blit(s.image(), (s.x, s.y))
        # fleet
        for rr in range(ROWS):
            spr = self.inv_spr[ROW_TYPE[rr]][self.anim]
            for cc in range(COLS):
                if self.alive[rr][cc]:
                    c.blit(spr, (self.fx + cc * CELL_W + 2, self.fy + rr * CELL_H))
        # mothership
        if self.ufo:
            c.blit(self.mother[(self.frame // 6) % 2], (int(self.ufo[0]), 30))
        # player
        if self.dying:
            if self.dying > 40:
                c.blit(self.boom_ship[(self.dying // 5) % 2], (int(self.player_x), PLAYER_Y))
        elif not (self.ready and self.ready < 60 and (self.ready // 4) % 2):
            c.blit(self.ship, (int(self.player_x), PLAYER_Y))
        # bullets
        if self.pbullet:
            pygame.draw.rect(c, WHITE, (self.pbullet[0], self.pbullet[1], 1, 4))
        for eb in self.ebullets:
            c.blit(self.eb_spr[eb.kind][(eb.anim // 4) % 2], (eb.x, int(eb.y)))
        # effects
        for x, y, s, t in self.fx_list:
            c.blit(s, (x, y))
        for x, y, txt, t in self.popups:
            f.draw(c, txt, x, y, P(0x28), 1, 'center')
        # ground + lives
        pygame.draw.line(c, P(0x2A), (0, GROUND_Y), (W - 1, GROUND_Y))
        f.draw(c, str(self.lives), 8, 228, WHITE)
        for i in range(min(self.lives - 1, 6)):
            c.blit(self.ship, (20 + i * 16, 228))
        f.draw(c, "A.C HOLDINGS", 248, 228, P(0x00), 1, 'right')
        # banners
        if self.ready and self.banner:
            f.draw(c, "WAVE %d" % self.level, 128, 140, P(0x28), 2, 'center', P(0x16))
            f.draw(c, "GET READY!", 128, 160, WHITE, 1, 'center')
        if self.clear_timer:
            f.draw(c, "WAVE CLEAR!", 128, 110, P(0x2B), 2, 'center', P(0x0A))
            f.draw(c, "BONUS PAWS INCOMING", 128, 130, WHITE, 1, 'center')

    # --- main loop ----------------------------------------------------------
    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for e in pygame.event.get():
                self.handle_event(e)
            if not self.running:
                break
            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(FPS)
            self.fps_value = clock.get_fps()
        save_hi(self.hiscore)


def main():
    try:
        pygame.mixer.pre_init(RATE, -16, 1, 512, allowedchanges=0)
    except TypeError:
        pygame.mixer.pre_init(RATE, -16, 1, 512)
    pygame.init()
    if not getattr(pygame, 'IS_CE', False):
        print("note: built for pygame-ce (pip install pygame-ce)")
    pygame.display.set_caption("Cat's Space Invaders 1.X")
    try:
        icon = make_sprite(CAT_FACE, {'X': P(0x27), 'p': P(0x25), 'w': WHITE, 'k': BLACK})
        pygame.display.set_icon(pygame.transform.scale(icon, (48, 40)))
    except Exception:
        pass
    flags = pygame.SCALED
    try:
        screen = pygame.display.set_mode((W, H), flags, vsync=1)
    except Exception:
        screen = pygame.display.set_mode((W, H), flags)
    Game(screen).run()
    pygame.quit()


if __name__ == '__main__':
    main()
