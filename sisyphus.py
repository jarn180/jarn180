import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 2                      # supersample
W, H = 1200, 300           # final banner size
N = 48                     # frames per loop
ANGLE = 13                 # hill angle (deg)
BG = (13, 17, 23)
HILL_TOP = (48, 54, 66)
HILL = (26, 31, 40)
FIG = (230, 222, 205)
STONE = (150, 146, 138)
STONE_DK = (104, 100, 94)
ACCENT = (240, 180, 90)

# flat-frame canvas (ground horizontal), rotated afterwards
FW, FH = 1700, 900
GY = 560                   # ground line in flat frame
R = 58                     # boulder radius
BX = 930                   # boulder center x
ROT_PER_LOOP = 2 * math.pi / 3     # 3-fold symmetric boulder markings
D = R * ROT_PER_LOOP               # ground distance travelled per loop

random.seed(7)
tufts = [(random.uniform(0, D), random.uniform(3, 9), random.choice([0, 1, 1, 2])) for _ in range(5)]
pebbles = [(random.uniform(0, D), random.uniform(8, 60), random.uniform(1.5, 3.5)) for _ in range(9)]
stars = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.6, 1.8), random.uniform(0, 1)) for _ in range(110)]

fbig = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 46 * S)
fsmall = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15 * S)


def s(p):
    return (p[0] * S, p[1] * S)


def line(d, a, b, w, c):
    d.line([s(a), s(b)], fill=c, width=int(w * S))
    for p in (a, b):
        r = w / 2
        d.ellipse([s((p[0] - r, p[1] - r)), s((p[0] + r, p[1] + r))], fill=c)


def ik(hip, foot, l1, l2, bend_forward=True):
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    dist = min(math.hypot(dx, dy), l1 + l2 - 0.01)
    a = math.atan2(dy, dx)
    cosb = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    b = math.acos(max(-1, min(1, cosb)))
    ang = a - b if bend_forward else a + b
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))


def flat_frame(t):
    im = Image.new("RGBA", (FW * S, FH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    off = t * D  # ground scroll

    # hill body
    d.rectangle([s((0, GY)), s((FW, FH))], fill=HILL)
    d.rectangle([s((0, GY)), s((FW, GY + 4))], fill=HILL_TOP)

    # scrolling ground details (repeat every D)
    for k in range(-2, int(FW / D) + 3):
        for (x, h, kind) in tufts:
            gx = x + k * D - off
            for j in range(kind + 1):
                line(d, (gx + j * 4, GY), (gx + j * 4 - 3, GY - h + j), 1.6, HILL_TOP)
        for (x, depth, r) in pebbles:
            px = x + k * D - off
            d.ellipse([s((px - r, GY + depth - r)), s((px + r, GY + depth + r))], fill=(38, 44, 55))

    # walk cycle
    ph = 2 * math.pi * t * 2          # two strides per loop
    bob = 2.5 * abs(math.sin(ph))
    hip = (792, GY - 70 + bob)
    lean = math.radians(58)
    shoulder = (hip[0] + 72 * math.sin(lean), hip[1] - 72 * math.cos(lean))
    head = (shoulder[0] + 20 * math.sin(lean + 0.15), shoulder[1] - 20 * math.cos(lean + 0.15))

    # boulder
    bc = (BX, GY - R)
    rot = -t * ROT_PER_LOOP
    d.ellipse([s((bc[0] - R, bc[1] - R)), s((bc[0] + R, bc[1] + R))], fill=STONE)
    d.chord([s((bc[0] - R, bc[1] - R)), s((bc[0] + R, bc[1] + R))], 20, 160, fill=STONE_DK)
    for i in range(3):
        a = rot + i * 2 * math.pi / 3
        p1 = (bc[0] + 0.25 * R * math.cos(a), bc[1] + 0.25 * R * math.sin(a))
        p2 = (bc[0] + 0.8 * R * math.cos(a + 0.35), bc[1] + 0.8 * R * math.sin(a + 0.35))
        line(d, p1, p2, 3, STONE_DK)
        q = (bc[0] + 0.55 * R * math.cos(a + 1.1), bc[1] + 0.55 * R * math.sin(a + 1.1))
        d.ellipse([s((q[0] - 4, q[1] - 4)), s((q[0] + 4, q[1] + 4))], fill=STONE_DK)

    # hands on the boulder
    ha = math.radians(196)
    hand = (bc[0] + (R + 2) * math.cos(ha), bc[1] + (R + 2) * math.sin(ha) + 0.6 * bob)
    hand2 = (hand[0] - 3, hand[1] + 9)

    # legs (back leg darker for depth)
    for i, col in ((1, (170, 163, 150)), (0, FIG)):
        p = ph + i * math.pi
        stride = 30 * math.cos(p)
        lift = max(0, math.sin(p)) * 9
        foot = (hip[0] - 34 + stride, GY - lift)
        knee = ik(hip, foot, 42, 42, bend_forward=True)
        knee = (knee[0], knee[1])
        line(d, hip, knee, 9, col)
        line(d, knee, foot, 8, col)
        line(d, foot, (foot[0] + 10, foot[1]), 6, col)
        if i == 1:
            # back arm
            el = ik(shoulder, hand2, 33, 33, bend_forward=False)
            line(d, shoulder, el, 7, col)
            line(d, el, hand2, 6, col)

    # torso, head, front arm
    line(d, hip, shoulder, 13, FIG)
    d.ellipse([s((head[0] - 12, head[1] - 12)), s((head[0] + 12, head[1] + 12))], fill=FIG)
    el = ik(shoulder, hand, 33, 33, bend_forward=False)
    line(d, shoulder, el, 8, FIG)
    line(d, el, hand, 7, FIG)
    return im


def background(t):
    im = Image.new("RGBA", (W * S, H * S), BG + (255,))
    d = ImageDraw.Draw(im)
    for (x, y, r, p) in stars:
        tw = 0.55 + 0.45 * math.sin(2 * math.pi * (t + p))
        c = tuple(int(BG[i] + (200 - BG[i]) * tw) for i in range(3))
        d.ellipse([s((x - r, y - r)), s((x + r, y + r))], fill=c)
    # moon
    mx, my, mr = 1110, 58, 20
    d.ellipse([s((mx - mr, my - mr)), s((mx + mr, my + mr))], fill=(222, 214, 196))
    d.ellipse([s((mx - mr + 9, my - mr - 4)), s((mx + mr + 9, my + mr - 4))], fill=BG)
    return im


frames = []
for f in range(N):
    t = f / N
    bg = background(t)
    fl = flat_frame(t).rotate(ANGLE, resample=Image.BICUBIC, center=(BX * S, GY * S))
    # place the boulder contact point at a fixed spot on the banner
    cx, cy = 690, 205
    bg.alpha_composite(fl, dest=(0, 0), source=((BX - cx) * S, (GY - cy) * S))
    d = ImageDraw.Draw(bg)
    d.text(s((48, 38)), "Jarren", font=fbig, fill=(236, 232, 222))
    d.text(s((51, 100)), "software engineer  //  still pushing", font=fsmall, fill=ACCENT)
    frames.append(bg.resize((W, H), Image.LANCZOS).convert("RGB"))

pal = frames[0].quantize(colors=128, method=Image.MEDIANCUT)
out = [fr.quantize(palette=pal, dither=Image.NONE) for fr in frames]
out[0].save("sisyphus.gif", save_all=True, append_images=out[1:], duration=60, loop=0, optimize=True, disposal=1)
frames[N // 3].save("preview.png")
print("ok")
