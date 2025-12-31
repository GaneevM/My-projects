import os
import sys
import json
import math
import random
import pygame
from dataclasses import dataclass



def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


WIDTH, HEIGHT = 1280, 720
FPS = 60

BG = (14, 18, 28)
PANEL = (24, 30, 44)
PANEL2 = (30, 38, 56)
WHITE = (235, 235, 235)
MUTED = (170, 170, 185)
ACCENT = (120, 200, 255)
RED = (235, 70, 85)
GREEN = (60, 210, 120)
BLUE = (60, 140, 255)
YELLOW = (245, 200, 70)
PURPLE = (180, 120, 255)

WORLD_RECT = pygame.Rect(30, 90, 820, 580)
RIGHT_RECT = pygame.Rect(880, 90, 370, 580)

MAX_DAYS = 365
DAY_SECONDS_BASE = 0.85

GEOJSON_FILENAME = "ne_110m_admin_0_countries.geojson"


def clamp(x, a, b):
    return max(a, min(b, x))

def lerp(a, b, t):
    return a + (b - a) * t

def draw_panel(surf, rect, color=PANEL, border=PANEL2):
    pygame.draw.rect(surf, color, rect, border_radius=14)
    pygame.draw.rect(surf, border, rect, 2, border_radius=14)

def draw_text(surf, text, font, color, pos, align="center"):
    img = font.render(text, True, color)
    r = img.get_rect()
    setattr(r, align, pos)
    surf.blit(img, r)
    return r

def draw_text_centered_in_rect(surf, text, font, color, rect):
    return draw_text(surf, text, font, color, rect.center, align="center")

def project_latlon(lat, lon, rect):
    x = rect.left + (lon + 180.0) / 360.0 * rect.w
    y = rect.top + (90.0 - lat) / 180.0 * rect.h
    return (x, y)

def poly_bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))

def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)):
            x_int = (xj - xi) * (y - yi) / ((yj - yi) + 1e-12) + xi
            if x < x_int:
                inside = not inside
        j = i
    return inside

def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))

def tooltip(surf, x, y, lines, font):
    pad = 10
    rendered = [font.render(line, True, WHITE) for line in lines]
    w = max(r.get_width() for r in rendered) + pad * 2
    h = sum(r.get_height() for r in rendered) + pad * 2

    x = clamp(x, 10, WIDTH - w - 10)
    y = clamp(y, 10, HEIGHT - h - 10)

    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, (18, 18, 24), rect, border_radius=10)
    pygame.draw.rect(surf, (90, 100, 130), rect, 2, border_radius=10)

    yy = y + pad
    for r in rendered:
        surf.blit(r, (x + pad, yy))
        yy += r.get_height()



class Button:
    def __init__(self, rect, label, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font

    def draw(self, surf, enabled=True):
        mx, my = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mx, my)

        base = (38, 48, 72) if enabled else (30, 32, 38)
        hi = (55, 70, 110) if enabled else (30, 32, 38)
        color = hi if (hover and enabled) else base

        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        pygame.draw.rect(surf, (80, 90, 120), self.rect, 2, border_radius=12)
        draw_text_centered_in_rect(surf, self.label, self.font, WHITE if enabled else MUTED, self.rect)

    def clicked(self, event, enabled=True):
        if not enabled:
            return False
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

class Checkbox:
    def __init__(self, x, y, label, font, value=True):
        self.box = pygame.Rect(x, y, 24, 24)
        self.hit = self.box.inflate(250, 10)
        self.label = label
        self.font = font
        self.value = value

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hit.collidepoint(event.pos):
                self.value = not self.value

    def draw(self, surf):
        pygame.draw.rect(surf, (40, 48, 70), self.box, border_radius=6)
        pygame.draw.rect(surf, (90, 100, 130), self.box, 2, border_radius=6)
        if self.value:
            pygame.draw.line(surf, ACCENT, (self.box.x + 5, self.box.y + 13), (self.box.x + 10, self.box.y + 18), 3)
            pygame.draw.line(surf, ACCENT, (self.box.x + 10, self.box.y + 18), (self.box.x + 19, self.box.y + 6), 3)
        draw_text(surf, self.label, self.font, WHITE, (self.box.right + 10, self.box.centery), align="midleft")

class Slider:
    def __init__(self, x, y, w, mn, mx, v, label, font):
        self.rect = pygame.Rect(x, y, w, 18)
        self.mn = mn
        self.mx = mx
        self.value = v
        self.drag = False
        self.label = label
        self.font = font

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.drag = True
            self._set(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.drag = False
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self._set(event.pos[0])

    def _set(self, mx):
        t = clamp((mx - self.rect.x) / self.rect.w, 0, 1)
        self.value = self.mn + t * (self.mx - self.mn)

    def draw(self, surf):
        draw_text(surf, f"{self.label}: {self.value:.2f}x", self.font, WHITE,
                  (self.rect.centerx, self.rect.y - 6), align="midbottom")
        pygame.draw.rect(surf, (44, 52, 72), self.rect, border_radius=10)
        pygame.draw.rect(surf, (90, 100, 130), self.rect, 2, border_radius=10)
        t = (self.value - self.mn) / (self.mx - self.mn)
        kx = int(self.rect.x + t * self.rect.w)
        pygame.draw.circle(surf, ACCENT, (kx, self.rect.centery), 9)
        pygame.draw.circle(surf, (30, 30, 50), (kx, self.rect.centery), 9, 2)

class TextBox:
    def __init__(self, rect, font, placeholder="Type a country…"):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.active = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            else:
                if len(event.unicode) == 1 and (event.unicode.isalnum() or event.unicode in " -'.()&/"):
                    if len(self.text) < 32:
                        self.text += event.unicode

    def draw(self, surf, label):
        pygame.draw.rect(surf, (34, 42, 62), self.rect, border_radius=10)
        pygame.draw.rect(surf, ACCENT if self.active else (90, 100, 130), self.rect, 2, border_radius=10)
        shown = self.text if self.text else self.placeholder
        col = WHITE if self.text else MUTED
        draw_text(surf, shown, self.font, col, (self.rect.x + 10, self.rect.centery), align="midleft")
        draw_text(surf, label, self.font, WHITE, (self.rect.centerx, self.rect.y - 6), align="midbottom")


@dataclass
class Part:
    name: str
    pros: str
    cons: str
    mods: dict

@dataclass
class Category:
    name: str
    parts: list

def build_categories():
    return [
        Category("Transmission", [
            Part("Airborne Mist", "+Spreads far\n+Fast in crowds", "-Usually less deadly",
                 {"beta": +0.030, "land_spread": +0.010, "fatality": -0.010}),
            Part("Close Contact", "+Strong local spread", "-Harder overseas spread",
                 {"beta": +0.020, "land_spread": +0.006}),
            Part("Superspreader", "+Big spikes", "-Can fizzle",
                 {"beta": +0.012, "burst": 1}),
            Part("Waterborne", "+Hard to trace", "-Slower growth",
                 {"beta": +0.016, "land_spread": +0.008, "recovery_days": +1}),
            Part("Droplet Heavy", "+More severe", "-Short reach",
                 {"beta": +0.018, "land_spread": +0.004, "fatality": +0.015}),
        ]),
        Category("Disease Course", [
            Part("Fast & Loud", "+Rapid wave", "-Shorter infection",
                 {"recovery_days": -3, "beta": +0.007, "fatality": +0.008}),
            Part("Slow Burner", "+Lingering", "-Slower ramp",
                 {"recovery_days": +6, "beta": -0.004}),
            Part("High Fever", "+Deadlier", "-May reduce spread",
                 {"fatality": +0.050, "beta": -0.010}),
            Part("Stealthy", "+Hard to notice", "-Lower peak",
                 {"beta": +0.010, "recovery_days": +2, "fatality": -0.012, "stealth": 1}),
            Part("Reinfection", "+Come back again", "-Less immediate power",
                 {"immune_escape": +0.30, "beta": -0.003}),
        ]),
        Category("Mutation", [
            Part("Immune Escape", "+Vaccines weaker", "-Slightly slower early",
                 {"immune_escape": +0.40, "beta": -0.004}),
            Part("Stable Genome", "+Strong early wave", "-Vaccines better",
                 {"immune_escape": -0.10, "beta": +0.010}),
            Part("Rapid Mutation", "+Adapts", "-Random drift",
                 {"immune_escape": +0.18, "beta": +0.006, "mutation": 1, "fatality": -0.005}),
            Part("Antibody Decoy", "+Weakens immunity", "-Longer sickness",
                 {"immune_escape": +0.22, "recovery_days": +2}),
            Part("No Mutation", "+Simple", "-Humans counter well",
                 {"immune_escape": -0.20}),
        ]),
        Category("Human Response", [
            Part("Slow Gov", "+Vaccines late", "-Late response spikes",
                 {"vax_rate": -0.001}),
            Part("Fast Vaccination", "+High vax pressure", "-Harder to win",
                 {"vax_rate": +0.003}),
            Part("Strong Masking", "+Lower spread", "-Need high contagion",
                 {"beta": -0.010, "land_spread": -0.004}),
            Part("Panic Mode", "+Isolation", "-Long timeline",
                 {"beta": -0.008, "land_spread": -0.004, "vax_rate": +0.001}),
            Part("Fake News", "+Vax slower", "-Weird late waves",
                 {"vax_rate": -0.0005, "hesitancy": 1}),
        ]),
    ]

def base_params():
    return {
        "beta": 0.022,
        "land_spread": 0.006,
        "recovery_days": 10.0,
        "fatality": 0.02,
        "immune_escape": 0.0,
        "vax_rate": 0.0012,
        "vax_effect": 0.78,
    }

def apply_mods(p, mods):
    for k, v in mods.items():
        p[k] = p.get(k, 0) + v
    p["beta"] = clamp(p["beta"], 0.0, 0.12)
    p["land_spread"] = clamp(p.get("land_spread", 0.006), 0.0, 0.03)
    p["recovery_days"] = clamp(p["recovery_days"], 3, 28)
    p["fatality"] = clamp(p["fatality"], 0.0, 0.35)
    p["immune_escape"] = clamp(p["immune_escape"], -0.3, 0.8)
    p["vax_rate"] = clamp(p["vax_rate"], 0.0, 0.01)
    p["vax_effect"] = clamp(p["vax_effect"], 0.0, 0.95)
    return p

LANDLOCKED = {
    "Afghanistan","Andorra","Armenia","Austria","Azerbaijan","Belarus","Bhutan","Bolivia","Botswana","Burkina Faso",
    "Burundi","Central African Republic","Chad","Czechia","Eswatini","Ethiopia","Hungary","Kazakhstan","Kosovo",
    "Kyrgyzstan","Laos","Lesotho","Liechtenstein","Luxembourg","Malawi","Mali","Moldova","Mongolia","Nepal","Niger",
    "North Macedonia","Paraguay","Rwanda","San Marino","Serbia","Slovakia","South Sudan","Switzerland","Tajikistan",
    "Turkmenistan","Uganda","Uzbekistan","Vatican","Zambia","Zimbabwe"
}

@dataclass
class CountryGeom:
    name: str
    pop: int
    coastal: bool
    polys: list
    bboxes: list
    centroid: tuple

def load_countries(geojson_path, rect):
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(
            f"Can't find map file at:\n{geojson_path}\n\n"
            f"Expected filename: {GEOJSON_FILENAME}\n"
            f"(If you built an .exe, make sure you rebuilt with --add-data.)"
        )

    with open(geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    inner = rect.inflate(-16, -16)
    out = []

    feats = gj.get("features", [])
    for feat in feats:
        props = feat.get("properties", {}) or {}
        geom = feat.get("geometry", {}) or {}

        name = props.get("ADMIN") or props.get("NAME") or props.get("name") or props.get("NAME_LONG") or "Unknown"
        pop_est = props.get("POP_EST") or props.get("pop_est") or props.get("POP2005") or 1_000_000
        try:
            pop = int(pop_est)
        except:
            pop = 1_000_000

        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        polys = []

        def convert_ring(ring_lonlat):
            pts = []
            for lon, lat in ring_lonlat:
                x, y = project_latlon(lat, lon, inner)
                pts.append((x, y))

            if len(pts) > 700:
                step = max(1, len(pts) // 350)
                pts = pts[::step]
            elif len(pts) > 350:
                x, y = project_latlon(lat, lon, inner)
                pts.append((x, y))

            if len(pts) > 700:
                step = max(1, len(pts) // 350)
                pts = pts[::step]
            elif len(pts) > 350:
                step = max(1, len(pts) // 250)
                pts = pts[::step]
            return pts

        if gtype == "Polygon":
            if coords and coords[0]:
                outer = convert_ring(coords[0])
                if len(outer) >= 3:
                    polys.append(outer)

        elif gtype == "MultiPolygon":
            for poly in coords:
                if poly and poly[0]:
                    outer = convert_ring(poly[0])
                    if len(outer) >= 3:
                        polys.append(outer)

        if not polys:
            continue

        bboxes = [poly_bbox(p) for p in polys]

        def area(bb):
            x0, y0, x1, y1 = bb
            return (x1-x0)*(y1-y0)

        main_idx = max(range(len(polys)), key=lambda i: area(bboxes[i]))
        cxy = centroid(polys[main_idx])

        coastal = (name not in LANDLOCKED)
        out.append(CountryGeom(name=name, pop=pop, coastal=coastal, polys=polys, bboxes=bboxes, centroid=cxy))

    out.sort(key=lambda c: c.name.lower())
    return out


class TravelParticle:
    def __init__(self, a, b, color, duration=0.9):
        self.ax, self.ay = a
        self.bx, self.by = b
        self.color = color
        self.t = 0.0
        self.duration = duration

    def update(self, dt):
        self.t += dt / self.duration
        return self.t >= 1.0

    def draw(self, surf):
        tt = clamp(self.t, 0, 1)
        x = lerp(self.ax, self.bx, tt)
        y = lerp(self.ay, self.by, tt)
        pygame.draw.circle(surf, self.color, (int(x), int(y)), 3)

class Pulse:
    def __init__(self, pos, color):
        self.x, self.y = pos
        self.color = color
        self.life = 0.0
        self.r = 6

    def update(self, dt):
        self.life += dt
        self.r += 45 * dt
        return self.life > 0.9

    def draw(self, surf):
        alpha = int(255 * (1 - clamp(self.life / 0.9, 0, 1)))
        s = pygame.Surface((int(self.r*2+8), int(self.r*2+8)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (s.get_width()//2, s.get_height()//2), int(self.r), 2)
        surf.blit(s, (self.x - s.get_width()//2, self.y - s.get_height()//2))


class WorldSim:
    def __init__(self, params, countries, start_name, flights_on, boats_on):
        self.params = params
        self.countries = countries
        self.day = 0.0
        self.speed_mult = 1.0

        self.flights_on = flights_on
        self.boats_on = boats_on

        n = len(countries)
        self.S = [max(0, c.pop) for c in countries]
        self.I = [0]*n
        self.R = [0]*n
        self.V = [0]*n
        self.D = [0]*n

        self.name_to_idx = {c.name: i for i, c in enumerate(countries)}
        start_idx = self.name_to_idx.get(start_name, 0)

        seed = max(50, int(countries[start_idx].pop * 0.001))
        seed = min(seed, self.S[start_idx])
        self.S[start_idx] -= seed
        self.I[start_idx] += seed

        self.neigh = [[] for _ in range(n)]
        for i in range(n):
            ax, ay = countries[i].centroid
            for j in range(i+1, n):
                bx, by = countries[j].centroid
                d = math.hypot(ax-bx, ay-by)
                if d < 70:
                    self.neigh[i].append(j)
                    self.neigh[j].append(i)

        self.pulses = []
        self.travel = []

    def totals(self):
        return (sum(self.S), sum(self.I), sum(self.R), sum(self.V), sum(self.D))

    def step(self, dt_real):
        days_dt = (dt_real / DAY_SECONDS_BASE) * self.speed_mult
        if days_dt <= 0:
            return
        self.day += days_dt

        beta = self.params["beta"]
        land_spread = self.params.get("land_spread", 0.006)
        recovery_days = self.params["recovery_days"]
        fatality = self.params["fatality"]
        vax_rate = self.params["vax_rate"]
        vax_effect = self.params["vax_effect"]
        immune_escape = self.params["immune_escape"]

        if self.params.get("mutation", 0) == 1:
            beta = clamp(beta + math.sin(self.day * 0.18) * 0.003, 0.0, 0.12)
            immune_escape = clamp(immune_escape + math.cos(self.day * 0.11) * 0.02, -0.3, 0.8)

        burst = 1.0
        if self.params.get("burst", 0) == 1 and int(self.day) % 25 in (0, 1, 2):
            burst = 1.8

        if self.params.get("hesitancy", 0) == 1:
            ramp = clamp((self.day - 35) / 40, 0, 1)
            vax_rate = vax_rate * (0.35 + 0.65 * ramp)

        n = len(self.countries)

        if vax_rate > 0:
            for k in range(n):
                if self.S[k] <= 0:
                    continue
                vacc = int(self.S[k] * vax_rate * days_dt)
                vacc = clamp(vacc, 0, self.S[k])
                self.S[k] -= vacc
                self.V[k] += vacc

        for k in range(n):
            alive = self.S[k] + self.I[k] + self.R[k] + self.V[k]
            if alive <= 0 or self.I[k] <= 0 or self.S[k] <= 0:
                continue
            pressure = self.I[k] / alive
            eff = beta * burst

            vacc_frac = (self.V[k] / alive) if alive else 0.0
            eff *= (1.0 - 0.25 * clamp(vacc_frac * vax_effect, 0, 1))

            new_inf = int(eff * pressure * self.S[k] * days_dt * 2.6)
            new_inf = clamp(new_inf, 0, self.S[k])
            if new_inf > 0:
                self.S[k] -= new_inf
                self.I[k] += new_inf
                if random.random() < 0.18:
                    self.pulses.append(Pulse(self.countries[k].centroid, RED))

        for k in range(n):
            if self.I[k] <= 0:
                continue
            for nb in self.neigh[k]:
                if self.S[nb] <= 0:
                    continue
                spill = int(land_spread * burst * (self.I[k] / max(1, self.countries[k].pop)) * self.S[nb] * days_dt * 220)
                spill = clamp(spill, 0, self.S[nb])
                if spill > 0:
                    self.S[nb] -= spill
                    self.I[nb] += spill
                    if random.random() < 0.08:
                        self.pulses.append(Pulse(self.countries[nb].centroid, RED))

        if self.flights_on or self.boats_on:
            _, I_tot, _, _, _ = self.totals()
            travel_base = clamp(I_tot / 60_000_000, 0.0, 1.0)

            for k in range(n):
                if self.I[k] <= 0:
                    continue

                if self.flights_on and random.random() < (0.02 + 0.10 * travel_base) * days_dt:
                    j = random.randrange(n)
                    if j != k and self.S[j] > 0:
                        moved = clamp(int(50 + self.I[k] * 0.000002), 10, 900)
                        moved = clamp(moved, 0, self.S[j])
                        if moved > 0:
                            self.S[j] -= moved
                            self.I[j] += moved
                            self.travel.append(TravelParticle(self.countries[k].centroid, self.countries[j].centroid, YELLOW, 0.7))
                            self.pulses.append(Pulse(self.countries[j].centroid, RED))

                if self.boats_on and self.countries[k].coastal and random.random() < (0.012 + 0.06 * travel_base) * days_dt:
                    coastal_idxs = [idx for idx, c in enumerate(self.countries) if c.coastal and idx != k]
                    if coastal_idxs:
                        j = random.choice(coastal_idxs)
                        if self.S[j] > 0:
                            moved = clamp(int(30 + self.I[k] * 0.0000015), 8, 600)
                            moved = clamp(moved, 0, self.S[j])
                            if moved > 0:
                                self.S[j] -= moved
                                self.I[j] += moved
                                self.travel.append(TravelParticle(self.countries[k].centroid, self.countries[j].centroid, (120, 255, 190), 1.05))
                                self.pulses.append(Pulse(self.countries[j].centroid, RED))

        for k in range(n):
            if self.I[k] <= 0:
                continue

            death_per_day = fatality / max(1.0, recovery_days)
            deaths = int(self.I[k] * death_per_day * days_dt)
            deaths = clamp(deaths, 0, self.I[k])
            self.I[k] -= deaths
            self.D[k] += deaths

            rec_per_day = 1.0 / max(1.0, recovery_days)
            rec = int(self.I[k] * rec_per_day * days_dt)
            rec = clamp(rec, 0, self.I[k])
            self.I[k] -= rec
            self.R[k] += rec

            if immune_escape > 0 and self.R[k] > 0 and self.I[k] > 0:
                reinf = int(self.R[k] * (immune_escape * 0.01) * days_dt)
                reinf = clamp(reinf, 0, self.R[k])
                if reinf > 0:
                    self.R[k] -= reinf
                    self.I[k] += reinf
                    if random.random() < 0.03:
                        self.pulses.append(Pulse(self.countries[k].centroid, PURPLE))

            if immune_escape > 0 and self.V[k] > 0 and self.I[k] > 0:
                protection = clamp(vax_effect * (1.0 - immune_escape), 0.0, 1.0)
                breakthrough = int(self.V[k] * (1.0 - protection) * 0.0015 * days_dt)
                breakthrough = clamp(breakthrough, 0, self.V[k])
                if breakthrough > 0:
                    self.V[k] -= breakthrough
                    self.I[k] += breakthrough
                    if random.random() < 0.02:
                        self.pulses.append(Pulse(self.countries[k].centroid, RED))

        self.pulses = [p for p in self.pulses if not p.update(dt_real)]
        self.travel = [t for t in self.travel if not t.update(dt_real)]

    def is_over(self):
        S, I, R, V, D = self.totals()
        alive = S + I + R + V
        wiped = (alive == 0)
        infection_gone = (I == 0)
        timed_out = (self.day >= MAX_DAYS)
        return wiped, infection_gone, timed_out


def render_base_map_surface(countries):
    surf = pygame.Surface((WORLD_RECT.w, WORLD_RECT.h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    inner = pygame.Rect(16, 16, WORLD_RECT.w - 32, WORLD_RECT.h - 32)
    pygame.draw.rect(surf, (16, 28, 50), inner, border_radius=16)

    for lon in range(-180, 181, 60):
        x = inner.left + (lon + 180) / 360 * inner.w
        pygame.draw.line(surf, (22, 40, 70), (x, inner.top), (x, inner.bottom), 1)
    for lat in range(-60, 61, 30):
        y = inner.top + (90 - lat) / 180 * inner.h
        pygame.draw.line(surf, (22, 40, 70), (inner.left, y), (inner.right, y), 1)

    base_land = (30, 110, 78)
    border = (20, 70, 55)

    for c in countries:
        for poly in c.polys:
            local = [(x - WORLD_RECT.left, y - WORLD_RECT.top) for (x, y) in poly]
            pygame.draw.polygon(surf, base_land, local)
            pygame.draw.polygon(surf, border, local, 1)

    return surf

def build_hover_grid(countries, cell=48):
    cols = (WORLD_RECT.w + cell - 1) // cell
    rows = (WORLD_RECT.h + cell - 1) // cell
    grid = [[[] for _ in range(cols)] for _ in range(rows)]

    for ci, c in enumerate(countries):
        for pi, bb in enumerate(c.bboxes):
            x0, y0, x1, y1 = bb
            x0 -= WORLD_RECT.left; x1 -= WORLD_RECT.left
            y0 -= WORLD_RECT.top;  y1 -= WORLD_RECT.top

            gx0 = clamp(int(x0 // cell), 0, cols-1)
            gx1 = clamp(int(x1 // cell), 0, cols-1)
            gy0 = clamp(int(y0 // cell), 0, rows-1)
            gy1 = clamp(int(y1 // cell), 0, rows-1)

            for gy in range(gy0, gy1+1):
                for gx in range(gx0, gx1+1):
                    grid[gy][gx].append((ci, pi))

    return grid, cols, rows, cell

def pick_hovered_country(sim, hover_grid, cols, rows, cell, mx, my):
    if not WORLD_RECT.collidepoint(mx, my):
        return None

    lx = mx - WORLD_RECT.left
    ly = my - WORLD_RECT.top
    gx = int(lx // cell)
    gy = int(ly // cell)
    if gx < 0 or gy < 0 or gx >= cols or gy >= rows:
        return None

    candidates = hover_grid[gy][gx]
    for ci, pi in candidates:
        poly = sim.countries[ci].polys[pi]
        bb = sim.countries[ci].bboxes[pi]
        x0,y0,x1,y1 = bb
        if mx < x0 or mx > x1 or my < y0 or my > y1:
            continue
        if point_in_poly(mx, my, poly):
            return ci
    return None

def build_country_masks(countries):
    masks = []
    for c in countries:
        m = pygame.Surface((WORLD_RECT.w, WORLD_RECT.h), pygame.SRCALPHA)
        for poly in c.polys:
            local = [(x - WORLD_RECT.left, y - WORLD_RECT.top) for (x, y) in poly]
            pygame.draw.polygon(m, (255, 255, 255, 255), local)
        masks.append(m)
    return masks


def draw_bar(surf, x, y, w, h, frac, label, value, font):
    pygame.draw.rect(surf, (30, 35, 48), (x, y, w, h), border_radius=8)
    pygame.draw.rect(surf, (80, 90, 120), (x, y, w, h), 2, border_radius=8)
    fill = int(w * clamp(frac, 0, 1))
    pygame.draw.rect(surf, (90, 160, 255), (x, y, fill, h), border_radius=8)
    draw_text(surf, label, font, WHITE, (x, y - 6), align="midleft")
    draw_text(surf, value, font, MUTED, (x + w, y - 6), align="midright")

def draw_stats(surf, sim, font, font_small, paused, hovered_idx=None):
    draw_panel(surf, RIGHT_RECT)
    draw_text(surf, "Live Stats", font, WHITE, (RIGHT_RECT.centerx, RIGHT_RECT.top + 22), align="center")

    S, I, R, V, D = sim.totals()
    total = S + I + R + V + D
    alive = S + I + R + V
    vacc_pct = (V / total) if total else 0.0

    draw_text(surf, f"Day {sim.day:.1f}", font_small, WHITE, (RIGHT_RECT.centerx, RIGHT_RECT.top + 56), align="center")
    if paused:
        draw_text(surf, "PAUSED (SPACE)", font_small, YELLOW, (RIGHT_RECT.centerx, RIGHT_RECT.top + 76), align="center")

    lines = [
        (f"Alive: {alive:,}/{total:,}", WHITE),
        (f"Infected: {I:,}", RED),
        (f"Recovered: {R:,}", GREEN),
        (f"Vaccinated: {V:,} ({vacc_pct*100:.1f}%)", BLUE),
        (f"Dead: {D:,}", MUTED),
    ]
    y = RIGHT_RECT.top + 102
    for t, c in lines:
        draw_text(surf, t, font_small, c, (RIGHT_RECT.centerx, y), align="center")
        y += 22

    beta = sim.params["beta"]
    recovery = sim.params["recovery_days"]

    bx = RIGHT_RECT.left + 18
    bw = RIGHT_RECT.w - 36
    y0 = RIGHT_RECT.top + 250

    draw_bar(surf, bx, y0, bw, 22, beta / 0.12, "Transmission rate (beta)", f"{beta:.3f}", font_small)
    draw_bar(surf, bx, y0 + 60, bw, 22, (recovery - 3) / 25, "Recovery time (days)", f"{recovery:.1f}", font_small)
    draw_bar(surf, bx, y0 + 120, bw, 22, vacc_pct, "Vaccination % (current)", f"{vacc_pct*100:.1f}%", font_small)

    list_top = RIGHT_RECT.top + 455
    draw_text(surf, "Top infected countries:", font_small, WHITE, (RIGHT_RECT.centerx, list_top), align="center")

    pairs = [(idx, sim.I[idx]) for idx in range(len(sim.countries)) if sim.I[idx] > 0]
    pairs.sort(key=lambda x: x[1], reverse=True)
    pairs = pairs[:8]

    yy = list_top + 20
    if not pairs:
        draw_text(surf, "No active infections.", font_small, MUTED, (RIGHT_RECT.centerx, yy + 10), align="center")
    else:
        for idx, infected in pairs:
            c = sim.countries[idx]
            alive_c = sim.S[idx] + sim.I[idx] + sim.R[idx] + sim.V[idx]
            pct = (infected / alive_c * 100) if alive_c else 0.0

            name = c.name
            if len(name) > 22:
                name = name[:21] + "…"

            is_hover = (hovered_idx == idx)
            col = ACCENT if is_hover else WHITE
            draw_text(surf, f"{name}", font_small, col, (RIGHT_RECT.left + 18, yy), align="topleft")
            draw_text(surf, f"{infected:,}  ({pct:.2f}%)", font_small, RED if infected > 0 else MUTED,
                      (RIGHT_RECT.right - 18, yy), align="topright")
            yy += 18

    draw_text(surf, "SPACE: pause  |  R: restart", font_small, MUTED,
              (RIGHT_RECT.centerx, RIGHT_RECT.bottom - 22), align="center")


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ganeev's Pandemic Simulator")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("consolas", 34, bold=True)
    font = pygame.font.SysFont("consolas", 22, bold=True)
    font_small = pygame.font.SysFont("consolas", 16)

    try:
        geojson_path = resource_path(GEOJSON_FILENAME)
        countries = load_countries(geojson_path, WORLD_RECT)
    except Exception as e:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.fill((10, 10, 14))
            draw_text(screen, "MAP FILE ERROR", font_big, RED, (WIDTH//2, 120), align="center")
            msg = str(e).splitlines()
            y = 200
            for line in msg[:12]:
                draw_text(screen, line, font_small, WHITE, (WIDTH//2, y), align="center")
                y += 22
            pygame.display.flip()
        pygame.quit()
        return

    country_names = [c.name for c in countries]

    base_map = render_base_map_surface(countries)
    hover_grid, cols, rows, cell = build_hover_grid(countries, cell=48)
    masks = build_country_masks(countries)

    overlay_cache = [None] * len(countries)
    overlay_alpha_last = [-999] * len(countries)

    cats = build_categories()
    selected = [None, None, None, None]

    country_box = TextBox((920, 190, 290, 38), font_small)
    default_start = "United States of America" if "United States of America" in country_names else (country_names[0] if country_names else "")
    chosen = default_start
    country_box.text = chosen

    flights_cb = Checkbox(920, 420, "Flights enabled", font_small, True)
    boats_cb = Checkbox(920, 455, "Boats enabled", font_small, True)

    start_btn = Button((920, 610, 290, 48), "START SIMULATION", font_small)
    back_btn = Button((30, 24, 110, 38), "BACK", font_small)
    restart_btn = Button((WIDTH//2 - 150, HEIGHT//2 + 160, 300, 50), "BUILD A NEW VIRUS", font_small)

    speed = Slider(250, 52, 420, 0.2, 4.0, 1.0, "Time speed", font_small)

    scene = "builder"
    sim = None
    paused = False
    final_message = ""
    final_sub = ""
    final_stats = []

    def reset_sim():
        nonlocal sim, paused
        params = base_params()
        for ci, oi in enumerate(selected):
            params = apply_mods(params, cats[ci].parts[oi].mods)
        sim = WorldSim(params, countries, chosen, flights_cb.value, boats_cb.value)
        paused = False

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if scene == "builder":
                country_box.handle(event)
                flights_cb.handle(event)
                boats_cb.handle(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    for ci, cat in enumerate(cats):
                        px = 30 + ci * 212
                        panel_top = 100
                        for oi in range(5):
                            rr = pygame.Rect(px + 10, panel_top + 58 + oi * 98, 192, 86)
                            if rr.collidepoint(mx, my):
                                selected[ci] = oi

                    typed = country_box.text.strip().lower()
                    matches = [n for n in country_names if n.lower().startswith(typed)] if typed else country_names[:8]
                    sx, sy = 920, 240
                    for k in range(min(8, len(matches))):
                        rr = pygame.Rect(sx, sy + k*26, 290, 22)
                        if rr.collidepoint(mx, my):
                            chosen = matches[k]
                            country_box.text = chosen
                            country_box.active = False

                t = country_box.text.strip().lower()
                for n in country_names:
                    if n.lower() == t:
                        chosen = n
                        break

                can_start = all(x is not None for x in selected) and (chosen in country_names)
                if start_btn.clicked(event, enabled=can_start):
                    reset_sim()
                    scene = "sim"

            elif scene == "sim":
                speed.handle(event)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                    if event.key == pygame.K_r:
                        reset_sim()

                if back_btn.clicked(event, enabled=True):
                    scene = "builder"
                    sim = None
                    paused = False

            elif scene == "gameover":
                if restart_btn.clicked(event, enabled=True):
                    selected[:] = [None, None, None, None]
                    chosen = default_start
                    country_box.text = chosen
                    sim = None
                    paused = False
                    scene = "builder"

        screen.fill(BG)

        if scene == "builder":
            draw_text(screen, "VIRUS BUILDER", font_big, WHITE, (WIDTH//2, 34), align="center")
            draw_text(screen, "Pick 1 option per category • Hover for pros/cons • Choose starting country",
                      font_small, MUTED, (WIDTH//2, 62), align="center")

            hovered_tip = None

            for ci, cat in enumerate(cats):
                px = 30 + ci * 212
                panel = pygame.Rect(px, 100, 202, 560)
                draw_panel(screen, panel)
                draw_text_centered_in_rect(screen, cat.name, font_small, WHITE, pygame.Rect(panel.left, panel.top + 6, panel.w, 28))

                for oi, part in enumerate(cat.parts):
                    rr = pygame.Rect(panel.left + 10, panel.top + 58 + oi*98, 192, 86)
                    mx, my = pygame.mouse.get_pos()
                    hov = rr.collidepoint(mx, my)
                    sel = (selected[ci] == oi)

                    base = (34, 42, 62)
                    hover = (50, 62, 92)
                    chosen_col = (70, 90, 135)
                    col = chosen_col if sel else (hover if hov else base)

                    pygame.draw.rect(screen, col, rr, border_radius=12)
                    pygame.draw.rect(screen, (90, 100, 130), rr, 2, border_radius=12)
                    draw_text_centered_in_rect(screen, part.name, font_small, WHITE, rr)

                    if hov:
                        hovered_tip = (mx + 18, my + 18, [
                            f"{cat.name}: {part.name}",
                            "",
                            "Pros:",
                            *[f"  {x}" for x in part.pros.split("\n")],
                            "",
                            "Cons:",
                            *[f"  {x}" for x in part.cons.split("\n")],
                        ])

            config = pygame.Rect(880, 100, 370, 560)
            draw_panel(screen, config)
            draw_text_centered_in_rect(screen, "Outbreak Setup", font, WHITE, pygame.Rect(config.left, config.top + 6, config.w, 34))

            country_box.draw(screen, "Starting country")

            typed = country_box.text.strip().lower()
            matches = [n for n in country_names if n.lower().startswith(typed)] if typed else country_names[:8]
            sx, sy = 920, 240
            for k in range(min(8, len(matches))):
                rr = pygame.Rect(sx, sy + k*26, 290, 22)
                hov = rr.collidepoint(*pygame.mouse.get_pos())
                pygame.draw.rect(screen, (44, 52, 72) if not hov else (58, 72, 110), rr, border_radius=8)
                pygame.draw.rect(screen, (90, 100, 130), rr, 1, border_radius=8)
                draw_text_centered_in_rect(screen, matches[k], font_small, WHITE, rr)

            draw_text(screen, "Travel options", font_small, WHITE, (config.centerx, 395), align="center")
            flights_cb.draw(screen)
            boats_cb.draw(screen)

            can_start = all(x is not None for x in selected) and (chosen in country_names)
            start_btn.draw(screen, enabled=can_start)

            if can_start:
                draw_text(screen, f"Starting in: {chosen}", font_small, ACCENT, (config.centerx, config.bottom - 78), align="center")
            else:
                draw_text(screen, "Select 1 option in each category.", font_small, MUTED, (config.centerx, config.bottom - 78), align="center")

            if hovered_tip:
                tx, ty, lines = hovered_tip
                tooltip(screen, tx, ty, lines, font_small)

        elif scene == "sim":
            draw_text(screen, "SIMULATION", font_big, WHITE, (WIDTH//2, 26), align="center")
            back_btn.draw(screen, True)
            speed.draw(screen)

            sim.speed_mult = speed.value
            if not paused:
                sim.step(dt)

            draw_panel(screen, WORLD_RECT, color=(18, 24, 38), border=(50, 70, 110))
            screen.blit(base_map, (WORLD_RECT.left, WORLD_RECT.top))

            mx, my = pygame.mouse.get_pos()
            hovered = pick_hovered_country(sim, hover_grid, cols, rows, cell, mx, my)

            for idx, c in enumerate(sim.countries):
                I = sim.I[idx]
                if I <= 0:
                    continue

                alive = sim.S[idx] + sim.I[idx] + sim.R[idx] + sim.V[idx]
                if alive <= 0:
                    continue

                inf_frac = I / alive

                strength = clamp(math.sqrt(inf_frac) * 3.0, 0.0, 1.0)
                alpha = int(30 + 190 * strength)

                if abs(alpha - overlay_alpha_last[idx]) >= 6 or overlay_cache[idx] is None:
                    overlay_alpha_last[idx] = alpha
                    ov = masks[idx].copy()
                    ov.fill((RED[0], RED[1], RED[2], alpha), special_flags=pygame.BLEND_RGBA_MULT)
                    overlay_cache[idx] = ov

                screen.blit(overlay_cache[idx], (WORLD_RECT.left, WORLD_RECT.top))

            if hovered is not None:
                for poly in sim.countries[hovered].polys:
                    pygame.draw.polygon(screen, (240, 240, 245), poly, 2)

            for t in sim.travel:
                t.draw(screen)
            for p in sim.pulses:
                p.draw(screen)

            leg_text1 = "Green = healthy land"
            leg_text2 = "More red = more infected"
            tw1 = font_small.size(leg_text1)[0]
            tw2 = font_small.size(leg_text2)[0]
            box_w = max(tw1, tw2) + 70
            box_h = 52

            leg = pygame.Rect(WORLD_RECT.left + 18, WORLD_RECT.bottom - (box_h + 14), box_w, box_h)
            pygame.draw.rect(screen, (18, 18, 24), leg, border_radius=10)
            pygame.draw.rect(screen, (90, 100, 130), leg, 2, border_radius=10)

            pygame.draw.rect(screen, (30, 110, 78), (leg.left + 12, leg.top + 12, 14, 14), border_radius=4)
            pygame.draw.rect(screen, RED, (leg.left + 12, leg.top + 30, 14, 14), border_radius=4)
            draw_text(screen, leg_text1, font_small, WHITE, (leg.left + 34, leg.top + 19), align="midleft")
            draw_text(screen, leg_text2, font_small, WHITE, (leg.left + 34, leg.top + 37), align="midleft")

            draw_stats(screen, sim, font, font_small, paused, hovered_idx=hovered)

            if hovered is not None:
                c = sim.countries[hovered]
                S = sim.S[hovered]; I = sim.I[hovered]; R = sim.R[hovered]; V = sim.V[hovered]; D = sim.D[hovered]
                tot = S + I + R + V + D
                alive = S + I + R + V
                pct = (I / alive * 100) if alive else 0.0
                tooltip(screen, mx + 18, my + 18, [
                    c.name,
                    f"Population: {tot:,}",
                    f"S: {S:,}   V: {V:,}",
                    f"I: {I:,}   R: {R:,}",
                    f"D: {D:,}",
                    f"Infected: {pct:.2f}%",
                ], font_small)

            wiped, infection_gone, timed_out = sim.is_over()
            if wiped or infection_gone or timed_out:
                scene = "gameover"
                S, I, R, V, D = sim.totals()
                total = S + I + R + V + D

                if wiped:
                    final_message = "GAME OVER: WORLD WIPED OUT"
                    final_sub = f"It took {sim.day:.1f} days."
                elif infection_gone:
                    final_message = "OUTBREAK ENDED"
                    final_sub = f"The virus stopped spreading after {sim.day:.1f} days."
                else:
                    final_message = "TIME LIMIT REACHED"
                    final_sub = f"Simulation ended at {MAX_DAYS} days."

                final_stats = [
                    f"Dead: {D:,} / {total:,}",
                    f"Recovered: {R:,}",
                    f"Vaccinated: {V:,}",
                    f"Remaining infected: {I:,}",
                ]

        elif scene == "gameover":
            screen.fill((6, 6, 10))
            draw_text(screen, final_message, font_big, WHITE, (WIDTH//2, HEIGHT//2 - 180), align="center")
            draw_text(screen, final_sub, font, MUTED, (WIDTH//2, HEIGHT//2 - 135), align="center")

            yy = HEIGHT//2 - 85
            for line in final_stats[:6]:
                draw_text(screen, line, font_small, WHITE, (WIDTH//2, yy), align="center")
                yy += 22

            restart_btn.draw(screen, True)

        pygame.display.flip()


if __name__ == "__main__":
    main()
