import json
import math
import os
import random
import time
import pygame

W, H = 1300, 740
FPS = 60

LEFT_W = 560
SIDEBAR_W = 260
MARGIN = 12

PLAY_X = LEFT_W + MARGIN
PLAY_Y = MARGIN
PLAY_W = W - LEFT_W - SIDEBAR_W - MARGIN * 3
PLAY_H = H - MARGIN * 2

SIDEBAR_X = W - SIDEBAR_W - MARGIN
SIDEBAR_Y = MARGIN

BG = (18, 19, 24)
PANEL = (28, 31, 40)
PANEL2 = (22, 24, 32)
BORDER = (70, 80, 100)

WHITE = (235, 235, 245)
MUTED = (160, 170, 190)
GOOD = (180, 255, 180)

TOKEN_R = 22

CELL_W = 48
CELL_H = 44
CELL_PAD_X = 6
CELL_PAD_Y = 6
HEADER_H = 58
HSCROLL_H = 22

SHELF_H = 92
SHELF_PAD = 10
SHELF_ITEM_W = 94
SHELF_ITEM_H = 30
SHELF_GAP = 8
SHELF_TITLE_H = 22

TRASH_W = 140
TRASH_H = 70

CLEAR_W = 140
CLEAR_H = 54

HINT_W = 170
HINT_H = 46

SAVE_FILE = "ganeev_chem_save.json"

def clamp(v, a, b):
    return max(a, min(b, v))

def fmt_time(seconds: float) -> str:
    s = max(0, int(seconds + 0.5))
    return f"{s//60}:{s%60:02d}"

def stars_for_time(seconds: float) -> int:
    if seconds <= 60.0:
        return 3
    if seconds <= 120.0:
        return 2
    return 1

def draw_stars_text(n: int) -> str:
    return "★" * n + "☆" * (3 - n)

ELEMENTS = [
    (1, "H", "Hydrogen", 1, 1),
    (2, "He", "Helium", 1, 18),

    (3, "Li", "Lithium", 2, 1),
    (4, "Be", "Beryllium", 2, 2),
    (5, "B", "Boron", 2, 13),
    (6, "C", "Carbon", 2, 14),
    (7, "N", "Nitrogen", 2, 15),
    (8, "O", "Oxygen", 2, 16),
    (9, "F", "Fluorine", 2, 17),
    (10, "Ne", "Neon", 2, 18),

    (11, "Na", "Sodium", 3, 1),
    (12, "Mg", "Magnesium", 3, 2),
    (13, "Al", "Aluminum", 3, 13),
    (14, "Si", "Silicon", 3, 14),
    (15, "P", "Phosphorus", 3, 15),
    (16, "S", "Sulfur", 3, 16),
    (17, "Cl", "Chlorine", 3, 17),
    (18, "Ar", "Argon", 3, 18),

    (19, "K", "Potassium", 4, 1),
    (20, "Ca", "Calcium", 4, 2),
    (21, "Sc", "Scandium", 4, 3),
    (22, "Ti", "Titanium", 4, 4),
    (23, "V", "Vanadium", 4, 5),
    (24, "Cr", "Chromium", 4, 6),
    (25, "Mn", "Manganese", 4, 7),
    (26, "Fe", "Iron", 4, 8),
    (27, "Co", "Cobalt", 4, 9),
    (28, "Ni", "Nickel", 4, 10),
    (29, "Cu", "Copper", 4, 11),
    (30, "Zn", "Zinc", 4, 12),
    (31, "Ga", "Gallium", 4, 13),
    (32, "Ge", "Germanium", 4, 14),
    (33, "As", "Arsenic", 4, 15),
    (34, "Se", "Selenium", 4, 16),
    (35, "Br", "Bromine", 4, 17),
    (36, "Kr", "Krypton", 4, 18),

    (37, "Rb", "Rubidium", 5, 1),
    (38, "Sr", "Strontium", 5, 2),
    (39, "Y", "Yttrium", 5, 3),
    (40, "Zr", "Zirconium", 5, 4),
    (41, "Nb", "Niobium", 5, 5),
    (42, "Mo", "Molybdenum", 5, 6),
    (43, "Tc", "Technetium", 5, 7),
    (44, "Ru", "Ruthenium", 5, 8),
    (45, "Rh", "Rhodium", 5, 9),
    (46, "Pd", "Palladium", 5, 10),
    (47, "Ag", "Silver", 5, 11),
    (48, "Cd", "Cadmium", 5, 12),
    (49, "In", "Indium", 5, 13),
    (50, "Sn", "Tin", 5, 14),
    (51, "Sb", "Antimony", 5, 15),
    (52, "Te", "Tellurium", 5, 16),
    (53, "I", "Iodine", 5, 17),
    (54, "Xe", "Xenon", 5, 18),

    (55, "Cs", "Cesium", 6, 1),
    (56, "Ba", "Barium", 6, 2),
    (57, "La", "Lanthanum", 6, 3),
    (72, "Hf", "Hafnium", 6, 4),
    (73, "Ta", "Tantalum", 6, 5),
    (74, "W", "Tungsten", 6, 6),
    (75, "Re", "Rhenium", 6, 7),
    (76, "Os", "Osmium", 6, 8),
    (77, "Ir", "Iridium", 6, 9),
    (78, "Pt", "Platinum", 6, 10),
    (79, "Au", "Gold", 6, 11),
    (80, "Hg", "Mercury", 6, 12),
    (81, "Tl", "Thallium", 6, 13),
    (82, "Pb", "Lead", 6, 14),
    (83, "Bi", "Bismuth", 6, 15),
    (84, "Po", "Polonium", 6, 16),
    (85, "At", "Astatine", 6, 17),
    (86, "Rn", "Radon", 6, 18),

    (87, "Fr", "Francium", 7, 1),
    (88, "Ra", "Radium", 7, 2),
    (89, "Ac", "Actinium", 7, 3),
    (104, "Rf", "Rutherfordium", 7, 4),
    (105, "Db", "Dubnium", 7, 5),
    (106, "Sg", "Seaborgium", 7, 6),
    (107, "Bh", "Bohrium", 7, 7),
    (108, "Hs", "Hassium", 7, 8),
    (109, "Mt", "Meitnerium", 7, 9),
    (110, "Ds", "Darmstadtium", 7, 10),
    (111, "Rg", "Roentgenium", 7, 11),
    (112, "Cn", "Copernicium", 7, 12),
    (113, "Nh", "Nihonium", 7, 13),
    (114, "Fl", "Flerovium", 7, 14),
    (115, "Mc", "Moscovium", 7, 15),
    (116, "Lv", "Livermorium", 7, 16),
    (117, "Ts", "Tennessine", 7, 17),
    (118, "Og", "Oganesson", 7, 18),
]

LANTH = [
    (57, "La", "Lanthanum"),
    (58, "Ce", "Cerium"),
    (59, "Pr", "Praseodymium"),
    (60, "Nd", "Neodymium"),
    (61, "Pm", "Promethium"),
    (62, "Sm", "Samarium"),
    (63, "Eu", "Europium"),
    (64, "Gd", "Gadolinium"),
    (65, "Tb", "Terbium"),
    (66, "Dy", "Dysprosium"),
    (67, "Ho", "Holmium"),
    (68, "Er", "Erbium"),
    (69, "Tm", "Thulium"),
    (70, "Yb", "Ytterbium"),
    (71, "Lu", "Lutetium"),
]
ACT = [
    (89, "Ac", "Actinium"),
    (90, "Th", "Thorium"),
    (91, "Pa", "Protactinium"),
    (92, "U", "Uranium"),
    (93, "Np", "Neptunium"),
    (94, "Pu", "Plutonium"),
    (95, "Am", "Americium"),
    (96, "Cm", "Curium"),
    (97, "Bk", "Berkelium"),
    (98, "Cf", "Californium"),
    (99, "Es", "Einsteinium"),
    (100, "Fm", "Fermium"),
    (101, "Md", "Mendelevium"),
    (102, "No", "Nobelium"),
    (103, "Lr", "Lawrencium"),
]

RECIPES = {
    frozenset({"H", "O"}): ("H2O", "Water", "2H + O → H₂O"),
    frozenset({"N", "H"}): ("NH3", "Ammonia", "N + 3H → NH₃"),
    frozenset({"C", "O"}): ("CO2", "Carbon Dioxide", "C + O₂ → CO₂"),
    frozenset({"Mg", "O"}): ("MgO", "Magnesium Oxide", "2Mg + O₂ → 2MgO"),
    frozenset({"MgO", "H2O"}): ("Minerals", "Minerals", "MgO + H₂O → Minerals"),

    frozenset({"Sun", "H2O"}): ("LifeJuice", "Life Juice", "Sun + Water → Life Juice"),
    frozenset({"LifeJuice", "NH3"}): ("AminoAcids", "Amino Acids", "Life Juice + NH₃ → Amino Acids"),
    frozenset({"AminoAcids", "Minerals"}): ("Cells", "Cells", "Amino Acids + Minerals → Cells"),
    frozenset({"Cells", "O"}): ("Organism", "Organism", "Cells + O₂ → Organism"),
    frozenset({"C", "N"}): ("Nucleotides", "Nucleotides", "C + N → Nucleotides"),
    frozenset({"Nucleotides", "LifeJuice"}): ("DNA", "DNA", "Nucleotides + Life Juice → DNA"),
    frozenset({"Organism", "DNA"}): ("Human", "Human", "Organism + DNA → Human"),

    frozenset({"H2O", "Heat"}): ("Steam", "Steam", "Water + Heat → Steam"),
    frozenset({"Fe", "O"}): ("Fe2O3", "Rust", "4Fe + 3O₂ → 2Fe₂O₃"),
    frozenset({"Fe2O3", "C"}): ("Steel", "Steel", "Rust + C → Steel (kinda)"),
    frozenset({"Steam", "Steel"}): ("SteamEngine", "Steam Engine", "Steam + Steel → Steam Engine"),

    frozenset({"N", "O"}): ("NOx", "Nitrogen Oxides", "N + O → NOx"),
    frozenset({"NOx", "H2O"}): ("Acid", "Rocket Acid", "NOx + H₂O → Acid"),
    frozenset({"Acid", "NH3"}): ("Fuel", "Rocket Fuel", "Acid + NH₃ → Fuel"),
    frozenset({"Fuel", "SteamEngine"}): ("Rocket", "Rocket Ship", "Fuel + Steam Engine → Rocket Ship"),

    frozenset({"Si", "O"}): ("SiO2", "Silica", "Si + O → SiO₂"),
    frozenset({"SiO2", "C"}): ("SolarCells", "Solar Cells", "Silica + C → Solar Cells"),
    frozenset({"SolarCells", "Rocket"}): ("Satellites", "Satellites", "Solar Cells + Rocket → Satellites"),
    frozenset({"Satellites", "Sun"}): ("DysonSphere", "Dyson Sphere", "Satellites + Sun → Dyson Sphere"),
}

STARTER_ITEMS = [
    ("Sun", "Sun"),
    ("Heat", "Heat"),
]

COLOR_BY = {
    "H": (120, 190, 255),
    "O": (255, 120, 140),
    "C": (180, 180, 190),
    "N": (150, 150, 255),
    "Mg": (240, 200, 255),
    "Fe": (230, 170, 130),
    "Si": (210, 210, 230),

    "Sun": (255, 235, 140),
    "Heat": (255, 170, 120),

    "H2O": (140, 210, 255),
    "NH3": (200, 220, 255),
    "CO2": (180, 180, 200),
    "MgO": (240, 220, 255),
    "Minerals": (180, 200, 160),
    "LifeJuice": (180, 255, 170),
    "AminoAcids": (255, 190, 220),
    "Cells": (210, 210, 255),
    "Organism": (170, 255, 170),
    "Nucleotides": (210, 190, 255),
    "DNA": (190, 255, 210),
    "Human": (255, 255, 255),

    "Steam": (210, 240, 255),
    "Fe2O3": (210, 140, 100),
    "Steel": (210, 210, 220),
    "SteamEngine": (240, 240, 240),

    "NOx": (220, 200, 255),
    "Acid": (170, 255, 190),
    "Fuel": (255, 210, 170),
    "Rocket": (255, 255, 255),

    "SiO2": (230, 230, 240),
    "SolarCells": (180, 220, 255),
    "Satellites": (200, 200, 230),
    "DysonSphere": (255, 240, 190),
}

def token_color(sym: str):
    if sym in COLOR_BY:
        return COLOR_BY[sym]
    random.seed(sym)
    return (120 + random.randint(0, 90), 120 + random.randint(0, 90), 120 + random.randint(0, 90))

LEVELS = [
    {
        "id": 1,
        "goal": "Cells",
        "goal_name": "Cell",
        "path": [
            ("H", "O", "H2O"),
            ("Mg", "O", "MgO"),
            ("MgO", "H2O", "Minerals"),
            ("Sun", "H2O", "LifeJuice"),
            ("N", "H", "NH3"),
            ("LifeJuice", "NH3", "AminoAcids"),
            ("AminoAcids", "Minerals", "Cells"),
        ],
    },
    {
        "id": 2,
        "goal": "Human",
        "goal_name": "Human",
        "path": [
            ("H", "O", "H2O"),
            ("Mg", "O", "MgO"),
            ("MgO", "H2O", "Minerals"),
            ("Sun", "H2O", "LifeJuice"),
            ("N", "H", "NH3"),
            ("LifeJuice", "NH3", "AminoAcids"),
            ("AminoAcids", "Minerals", "Cells"),
            ("Cells", "O", "Organism"),
            ("C", "N", "Nucleotides"),
            ("Nucleotides", "LifeJuice", "DNA"),
            ("Organism", "DNA", "Human"),
        ],
    },
    {
        "id": 3,
        "goal": "SteamEngine",
        "goal_name": "Steam Engine",
        "path": [
            ("H", "O", "H2O"),
            ("H2O", "Heat", "Steam"),
            ("Fe", "O", "Fe2O3"),
            ("Fe2O3", "C", "Steel"),
            ("Steam", "Steel", "SteamEngine"),
        ],
    },
    {
        "id": 4,
        "goal": "Rocket",
        "goal_name": "Rocket Ship",
        "path": [
            ("H", "O", "H2O"),
            ("N", "O", "NOx"),
            ("NOx", "H2O", "Acid"),
            ("N", "H", "NH3"),
            ("Acid", "NH3", "Fuel"),
            ("Fe", "O", "Fe2O3"),
            ("Fe2O3", "C", "Steel"),
            ("H2O", "Heat", "Steam"),
            ("Steam", "Steel", "SteamEngine"),
            ("Fuel", "SteamEngine", "Rocket"),
        ],
    },
    {
        "id": 5,
        "goal": "DysonSphere",
        "goal_name": "Dyson Sphere",
        "path": [
            ("Si", "O", "SiO2"),
            ("SiO2", "C", "SolarCells"),
            ("H", "O", "H2O"),
            ("N", "O", "NOx"),
            ("NOx", "H2O", "Acid"),
            ("N", "H", "NH3"),
            ("Acid", "NH3", "Fuel"),
            ("Fe", "O", "Fe2O3"),
            ("Fe2O3", "C", "Steel"),
            ("H2O", "Heat", "Steam"),
            ("Steam", "Steel", "SteamEngine"),
            ("Fuel", "SteamEngine", "Rocket"),
            ("SolarCells", "Rocket", "Satellites"),
            ("Satellites", "Sun", "DysonSphere"),
        ],
    },
]

def load_save():
    data = {
        "unlocked": 1,
        "best_stars": {str(i): 0 for i in range(1, 6)},
    }
    if not os.path.exists(SAVE_FILE):
        return data
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            data["unlocked"] = int(loaded.get("unlocked", data["unlocked"]))
            bs = loaded.get("best_stars", {})
            if isinstance(bs, dict):
                for i in range(1, 6):
                    data["best_stars"][str(i)] = int(bs.get(str(i), 0))
    except Exception:
        pass
    data["unlocked"] = clamp(data["unlocked"], 1, 5)
    for i in range(1, 6):
        data["best_stars"][str(i)] = clamp(data["best_stars"].get(str(i), 0), 0, 3)
    return data

def save_save(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

class Particle:
    def __init__(self, pos):
        self.x, self.y = pos
        ang = random.random() * math.tau
        spd = random.uniform(2.0, 8.0)
        self.vx = math.cos(ang) * spd
        self.vy = math.sin(ang) * spd
        self.life = random.randint(22, 42)
        self.r = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= 1

    def draw(self, surf):
        if self.life <= 0:
            return
        alpha = clamp(int(255 * (self.life / 42)), 0, 255)
        c = (255, 210, 120, alpha)
        s = pygame.Surface((self.r * 2 + 2, self.r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, c, (self.r + 1, self.r + 1), self.r)
        surf.blit(s, (self.x - self.r - 1, self.y - self.r - 1))

class Explosion:
    def __init__(self, pos, reaction_text):
        self.pos = pos
        self.text = reaction_text
        self.particles = [Particle(pos) for _ in range(90)]
        self.timer = 55

    def update(self):
        for p in self.particles:
            p.update()
        self.timer -= 1

    def done(self):
        return self.timer <= 0

    def draw(self, surf, font_small):
        for p in self.particles:
            p.draw(surf)
        if self.timer > 0:
            txt = font_small.render(self.text, True, (255, 235, 220))
            pad = 8
            box = txt.get_rect(center=self.pos).inflate(pad * 2, pad * 2)
            pygame.draw.rect(surf, (0, 0, 0), box, border_radius=10)
            pygame.draw.rect(surf, (255, 200, 140), box, 2, border_radius=10)
            surf.blit(txt, txt.get_rect(center=self.pos))

class Token:
    def __init__(self, sym, name, x, y):
        self.sym = sym
        self.name = name
        self.x = x
        self.y = y
        self.r = TOKEN_R
        self.dragging = False
        self.dx = 0
        self.dy = 0

    def hit(self, mx, my):
        return (mx - self.x) ** 2 + (my - self.y) ** 2 <= self.r ** 2

    def start_drag(self, mx, my):
        self.dragging = True
        self.dx = self.x - mx
        self.dy = self.y - my

    def drag_to(self, mx, my):
        if self.dragging:
            self.x = mx + self.dx
            self.y = my + self.dy

    def stop_drag(self):
        self.dragging = False

    def draw(self, surf, font_sym, font_tiny):
        col = token_color(self.sym)
        pygame.draw.circle(surf, (0, 0, 0), (int(self.x) + 3, int(self.y) + 3), self.r + 2)
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.r, 2)

        sym_txt = font_sym.render(self.sym, True, (15, 15, 20))
        surf.blit(sym_txt, sym_txt.get_rect(center=(self.x, self.y)))

        nm = font_tiny.render(self.name, True, WHITE)
        surf.blit(nm, nm.get_rect(midbottom=(self.x, self.y - self.r - 6)))

class TableCell:
    def __init__(self, z, sym, name, rect):
        self.z = z
        self.sym = sym
        self.name = name
        self.rect = rect

def build_table_cells(panel_rect, table_top_y):
    cells = []
    grid_left = panel_rect.x + 12
    grid_top = table_top_y

    for z, sym, name, period, group in ELEMENTS:
        x = grid_left + (group - 1) * (CELL_W + CELL_PAD_X)
        y = grid_top + (period - 1) * (CELL_H + CELL_PAD_Y)
        cells.append(TableCell(z, sym, name, pygame.Rect(x, y, CELL_W, CELL_H)))

    start_group = 4
    lant_y = grid_top + 7 * (CELL_H + CELL_PAD_Y) + 16
    act_y = lant_y + (CELL_H + CELL_PAD_Y)

    for i, (z, sym, name) in enumerate(LANTH):
        group = start_group + i
        x = grid_left + (group - 1) * (CELL_W + CELL_PAD_X)
        cells.append(TableCell(z, sym, name, pygame.Rect(x, lant_y, CELL_W, CELL_H)))

    for i, (z, sym, name) in enumerate(ACT):
        group = start_group + i
        x = grid_left + (group - 1) * (CELL_W + CELL_PAD_X)
        cells.append(TableCell(z, sym, name, pygame.Rect(x, act_y, CELL_W, CELL_H)))

    content_h = (7 * (CELL_H + CELL_PAD_Y) + 16 + 2 * (CELL_H + CELL_PAD_Y) + 12)
    content_w = 12 + 18 * CELL_W + 17 * CELL_PAD_X + 12
    return cells, content_w, content_h

def build_shelf_item_rects(shelf_rect, made_list):
    items = []
    x = shelf_rect.x + SHELF_PAD
    y = shelf_rect.y + SHELF_TITLE_H + 6
    max_x = shelf_rect.right - SHELF_PAD

    for sym, name in made_list:
        r = pygame.Rect(x, y, SHELF_ITEM_W, SHELF_ITEM_H)
        if r.right > max_x:
            x = shelf_rect.x + SHELF_PAD
            y += SHELF_ITEM_H + SHELF_GAP
            r = pygame.Rect(x, y, SHELF_ITEM_W, SHELF_ITEM_H)
        if r.bottom > shelf_rect.bottom - 6:
            break
        items.append((r, sym, name))
        x += SHELF_ITEM_W + SHELF_GAP
    return items

def draw_shelf(surf, shelf_rect, items, font_tiny):
    pygame.draw.rect(surf, (24, 26, 34), shelf_rect, border_radius=14)
    pygame.draw.rect(surf, (90, 100, 125), shelf_rect, 2, border_radius=14)
    title = font_tiny.render("Made Stuff (drag out):", True, MUTED)
    surf.blit(title, (shelf_rect.x + 12, shelf_rect.y + 8))
    for r, sym, _name in items:
        pygame.draw.rect(surf, (50, 54, 70), r, border_radius=10)
        pygame.draw.rect(surf, (120, 130, 160), r, 1, border_radius=10)
        txt = font_tiny.render(sym, True, WHITE)
        surf.blit(txt, (r.x + 8, r.y + 7))

def draw_button(surf, rect, text, font, hovering=False, enabled=True):
    if not enabled:
        base = (50, 52, 62)
        border = (90, 95, 110)
        text_col = (120, 125, 140)
    else:
        base = (70, 72, 88) if not hovering else (95, 98, 120)
        border = (170, 175, 200)
        text_col = WHITE
    pygame.draw.rect(surf, base, rect, border_radius=14)
    pygame.draw.rect(surf, border, rect, 2, border_radius=14)
    t = font.render(text, True, text_col)
    surf.blit(t, t.get_rect(center=rect.center))

def draw_trashcan(surf, rect, font_tiny, hovering=False):
    base = (55, 58, 70) if not hovering else (75, 78, 92)
    pygame.draw.rect(surf, base, rect, border_radius=14)
    pygame.draw.rect(surf, (120, 130, 160), rect, 2, border_radius=14)
    lid = pygame.Rect(rect.x + 30, rect.y + 14, rect.w - 60, 10)
    body = pygame.Rect(rect.x + 40, rect.y + 26, rect.w - 80, rect.h - 40)
    pygame.draw.rect(surf, (30, 30, 35), lid, border_radius=6)
    pygame.draw.rect(surf, (30, 30, 35), body, border_radius=10)
    for i in range(3):
        x = body.x + 10 + i * ((body.w - 20) // 2)
        pygame.draw.line(surf, (90, 95, 110), (x, body.y + 8), (x, body.bottom - 8), 2)
    label = font_tiny.render("TRASH", True, (230, 230, 240))
    surf.blit(label, label.get_rect(center=(rect.centerx, rect.bottom - 14)))

def draw_hscrollbar(surf, track_rect, knob_rect, font_tiny):
    pygame.draw.rect(surf, (24, 26, 34), track_rect, border_radius=10)
    pygame.draw.rect(surf, (80, 90, 115), track_rect, 1, border_radius=10)
    pygame.draw.rect(surf, (110, 120, 150), knob_rect, border_radius=10)
    pygame.draw.rect(surf, (200, 205, 220), knob_rect, 1, border_radius=10)
    label = font_tiny.render("⇆", True, (20, 20, 25))
    surf.blit(label, label.get_rect(center=knob_rect.center))

def knob_from_scroll(scroll_x, max_scroll_x, track_rect, knob_w):
    if max_scroll_x <= 0:
        return pygame.Rect(track_rect.x, track_rect.y, track_rect.w, track_rect.h)
    usable = track_rect.w - knob_w
    t = scroll_x / max_scroll_x
    x = track_rect.x + int(t * usable)
    return pygame.Rect(x, track_rect.y, knob_w, track_rect.h)

def scroll_from_knob(knob_rect, max_scroll_x, track_rect, knob_w):
    if max_scroll_x <= 0:
        return 0
    usable = track_rect.w - knob_w
    t = (knob_rect.x - track_rect.x) / max(1, usable)
    return int(t * max_scroll_x)

def next_hint_for_level(level, made_set, hint_cursor: int):
    path = level["path"]
    if not path:
        return ("No hints.", 0)
    n = len(path)
    for offset in range(n):
        i = (hint_cursor + offset) % n
        a, b, prod = path[i]
        if prod not in made_set:
            reaction = RECIPES.get(frozenset({a, b}))
            if reaction:
                rx = reaction[2]
                return (f"Next: {rx}", (i + 1) % n)
            return (f"Next: {a} + {b} → {prod}", (i + 1) % n)
    return ("You're basically done — make the goal item!", hint_cursor)

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Ganeev's Chem Sim")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("arial", 28, bold=True)
    font_sym = pygame.font.SysFont("arial", 16, bold=True)
    font_z = pygame.font.SysFont("arial", 12)
    font_tiny = pygame.font.SysFont("arial", 14)
    font_mid = pygame.font.SysFont("arial", 22, bold=True)
    font_big = pygame.font.SysFont("arial", 44, bold=True)

    cursive_candidates = ["segoescript", "brushscriptmt", "lucidahandwriting", "comicsansms", "georgia"]
    watermark_font = None
    for f in cursive_candidates:
        watermark_font = pygame.font.SysFont(f, 44, italic=True)
        if watermark_font:
            break
    if watermark_font is None:
        watermark_font = pygame.font.SysFont("arial", 44, italic=True)

    left_rect = pygame.Rect(MARGIN, MARGIN, LEFT_W, H - MARGIN * 2)
    play_rect = pygame.Rect(LEFT_W + MARGIN * 2, MARGIN, PLAY_W, PLAY_H)
    sidebar_rect = pygame.Rect(SIDEBAR_X, SIDEBAR_Y, SIDEBAR_W, H - MARGIN * 2)

    left_inner = left_rect.inflate(-10, -10)
    shelf_rect = pygame.Rect(left_inner.x, left_inner.y + HEADER_H, left_inner.w, SHELF_H)

    table_top_y = shelf_rect.bottom + 10
    table_draw_area = pygame.Rect(
        left_inner.x, table_top_y, left_inner.w,
        left_inner.bottom - table_top_y - HSCROLL_H - 6
    )
    track_rect = pygame.Rect(left_inner.x + 12, table_draw_area.bottom + 6, left_inner.w - 24, HSCROLL_H)

    trash_rect = pygame.Rect(0, 0, TRASH_W, TRASH_H)
    trash_rect.centerx = play_rect.centerx
    trash_rect.bottom = play_rect.bottom - 14

    clear_rect = pygame.Rect(0, 0, CLEAR_W, CLEAR_H)
    clear_rect.right = play_rect.right - 14
    clear_rect.bottom = play_rect.bottom - 14

    hint_rect = pygame.Rect(0, 0, HINT_W, HINT_H)
    hint_rect.left = play_rect.left + 14
    hint_rect.bottom = play_rect.bottom - 14

    wm_text = watermark_font.render("Ganeev's chem lab", True, (255, 255, 255))
    wm = pygame.Surface(wm_text.get_size(), pygame.SRCALPHA)
    wm.blit(wm_text, (0, 0))
    wm.set_alpha(85)

    table_cells, table_content_w, table_content_h = build_table_cells(left_rect, table_top_y)
    vscroll = 0
    hscroll = 0
    knob_w = int((left_inner.w - 24) * (table_draw_area.w / max(table_draw_area.w, table_content_w)))
    knob_w = clamp(knob_w, 60, left_inner.w - 24)
    h_knob = knob_from_scroll(hscroll, max(0, table_content_w - table_draw_area.w), track_rect, knob_w)
    dragging_knob = False
    knob_drag_dx = 0

    save_data = load_save()

    STATE_MENU, STATE_PLAY, STATE_END = "menu", "play", "end"
    state = STATE_MENU

    current_level = None
    level_start_time = 0.0
    level_elapsed = 0.0
    level_stars = 0
    end_message = ""
    hint_cursor = 0
    hint_message = "Press NEXT HINT"
    hint_flash_timer = 0.0

    tokens = []
    dragging_token = None
    explosions = []

    made = []
    made_set = set()

    def add_made(sym, name):
        if sym not in made_set:
            made.append((sym, name))
            made_set.add(sym)

    def spawn_token(sym, name, pos):
        x = clamp(pos[0], play_rect.left + TOKEN_R, play_rect.right - TOKEN_R)
        y = clamp(pos[1], play_rect.top + TOKEN_R, play_rect.bottom - TOKEN_R)
        tokens.append(Token(sym, name, x, y))

    def reset_for_level(level):
        nonlocal current_level, tokens, dragging_token, explosions
        nonlocal made, made_set, level_start_time, level_elapsed
        nonlocal hint_cursor, hint_message, hint_flash_timer

        current_level = level
        tokens = []
        dragging_token = None
        explosions = []

        made = []
        made_set = set()
        for sym, name in STARTER_ITEMS:
            add_made(sym, name)

        level_start_time = time.time()
        level_elapsed = 0.0

        hint_cursor = 0
        hint_message = "Press NEXT HINT"
        hint_flash_timer = 0.0

    def finish_level():
        nonlocal state, level_elapsed, level_stars, end_message
        level_elapsed = time.time() - level_start_time
        level_stars = stars_for_time(level_elapsed)
        end_message = f"You made {current_level['goal_name']} in {fmt_time(level_elapsed)}  ({draw_stars_text(level_stars)})"

        cid = current_level["id"]
        if save_data["unlocked"] < cid + 1 and cid < len(LEVELS):
            save_data["unlocked"] = cid + 1

        best = save_data["best_stars"].get(str(cid), 0)
        if level_stars > best:
            save_data["best_stars"][str(cid)] = level_stars

        save_save(save_data)
        state = STATE_END

    def try_mix(dropped):
        for other in tokens:
            if other is dropped:
                continue
            dx = dropped.x - other.x
            dy = dropped.y - other.y
            if dx * dx + dy * dy <= (dropped.r + other.r) ** 2:
                key = frozenset({dropped.sym, other.sym})
                if key in RECIPES:
                    prod_sym, prod_name, reaction = RECIPES[key]
                    mx = int((dropped.x + other.x) / 2)
                    my = int((dropped.y + other.y) / 2)

                    explosions.append(Explosion((mx, my), reaction))

                    if dropped in tokens:
                        tokens.remove(dropped)
                    if other in tokens:
                        tokens.remove(other)

                    spawn_token(prod_sym, prod_name, (mx, my))
                    add_made(prod_sym, prod_name)

                    if current_level and prod_sym == current_level["goal"]:
                        finish_level()
                return

    def table_cell_under_mouse(mx, my):
        for c in table_cells:
            r = c.rect.move(-hscroll, -vscroll)
            if r.collidepoint(mx, my):
                return c, r
        return None, None

    def shelf_item_under_mouse(mx, my, shelf_items):
        for r, sym, name in shelf_items:
            if r.collidepoint(mx, my):
                return sym, name
        return None

    grid_w = 3
    btn_w, btn_h = 260, 92
    gap = 18
    start_x = play_rect.centerx - (grid_w * btn_w + (grid_w - 1) * gap) // 2
    start_y = play_rect.centery - 120

    menu_buttons = []
    for i, lv in enumerate(LEVELS):
        row = i // grid_w
        col = i % grid_w
        x = start_x + col * (btn_w + gap)
        y = start_y + row * (btn_h + gap)
        menu_buttons.append((lv, pygame.Rect(x, y, btn_w, btn_h)))

    end_menu_btn = pygame.Rect(0, 0, 200, 56)
    end_menu_btn.centerx = play_rect.centerx - 120
    end_menu_btn.centery = play_rect.centery + 120

    end_next_btn = pygame.Rect(0, 0, 200, 56)
    end_next_btn.centerx = play_rect.centerx + 120
    end_next_btn.centery = play_rect.centery + 120

    end_replay_btn = pygame.Rect(0, 0, 220, 56)
    end_replay_btn.centerx = play_rect.centerx
    end_replay_btn.centery = play_rect.centery + 190

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()

        if state == STATE_PLAY:
            level_elapsed = time.time() - level_start_time
            if hint_flash_timer > 0:
                hint_flash_timer -= dt

        max_vscroll = max(0, table_content_h - table_draw_area.h)
        max_hscroll = max(0, table_content_w - table_draw_area.w)
        vscroll = clamp(vscroll, 0, max_vscroll)
        hscroll = clamp(hscroll, 0, max_hscroll)
        if not dragging_knob:
            h_knob = knob_from_scroll(hscroll, max_hscroll, track_rect, knob_w)

        shelf_items = build_shelf_item_rects(shelf_rect, made)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for lv, r in menu_buttons:
                        if r.collidepoint(mx, my):
                            if lv["id"] <= save_data["unlocked"]:
                                reset_for_level(lv)
                                state = STATE_PLAY
                            break

            elif state == STATE_PLAY:
                if event.type == pygame.MOUSEWHEEL:
                    if table_draw_area.collidepoint(mx, my) and not dragging_knob:
                        vscroll -= event.y * 36
                        vscroll = clamp(vscroll, 0, max_vscroll)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if h_knob.collidepoint(mx, my):
                        dragging_knob = True
                        knob_drag_dx = mx - h_knob.x
                        continue

                    if hint_rect.collidepoint(mx, my):
                        hint_message, hint_cursor = next_hint_for_level(current_level, made_set, hint_cursor)
                        hint_flash_timer = 1.8
                        continue

                    if clear_rect.collidepoint(mx, my):
                        tokens.clear()
                        explosions.clear()
                        dragging_token = None
                        continue

                    for t in reversed(tokens):
                        if t.hit(mx, my):
                            dragging_token = t
                            t.start_drag(mx, my)
                            break

                    if dragging_token is None and shelf_rect.collidepoint(mx, my):
                        hit = shelf_item_under_mouse(mx, my, shelf_items)
                        if hit:
                            sym, name = hit
                            spawn_token(sym, name, (play_rect.left + 80, play_rect.top + 90))
                            dragging_token = tokens[-1]
                            dragging_token.start_drag(mx, my)
                            continue

                    if dragging_token is None and table_draw_area.collidepoint(mx, my):
                        cell, _ = table_cell_under_mouse(mx, my)
                        if cell:
                            spawn_token(cell.sym, cell.name, (play_rect.left + 70, play_rect.top + 80))
                            dragging_token = tokens[-1]
                            dragging_token.start_drag(mx, my)

                elif event.type == pygame.MOUSEMOTION:
                    if dragging_knob:
                        new_x = mx - knob_drag_dx
                        new_x = clamp(new_x, track_rect.x, track_rect.right - h_knob.w)
                        h_knob.x = new_x
                        hscroll = scroll_from_knob(h_knob, max_hscroll, track_rect, knob_w)

                    if dragging_token:
                        dragging_token.drag_to(mx, my)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if dragging_knob:
                        dragging_knob = False

                    if dragging_token:
                        dragging_token.stop_drag()

                        if trash_rect.collidepoint((dragging_token.x, dragging_token.y)):
                            if dragging_token in tokens:
                                tokens.remove(dragging_token)
                            dragging_token = None
                            continue

                        dragging_token.x = clamp(dragging_token.x, play_rect.left + TOKEN_R, play_rect.right - TOKEN_R)
                        dragging_token.y = clamp(dragging_token.y, play_rect.top + TOKEN_R, play_rect.bottom - TOKEN_R)

                        if play_rect.collidepoint((dragging_token.x, dragging_token.y)):
                            try_mix(dragging_token)
                        dragging_token = None

            elif state == STATE_END:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if end_menu_btn.collidepoint(mx, my):
                        state = STATE_MENU
                        continue
                    if end_replay_btn.collidepoint(mx, my):
                        reset_for_level(current_level)
                        state = STATE_PLAY
                        continue
                    next_id = current_level["id"] + 1
                    next_enabled = (next_id <= len(LEVELS)) and (next_id <= save_data["unlocked"])
                    if end_next_btn.collidepoint(mx, my) and next_enabled:
                        reset_for_level(LEVELS[next_id - 1])
                        state = STATE_PLAY
                        continue

        for ex in explosions:
            ex.update()
        explosions = [e for e in explosions if not e.done()]

        screen.fill(BG)
        pygame.draw.rect(screen, PANEL, left_rect, border_radius=14)
        pygame.draw.rect(screen, BORDER, left_rect, 2, border_radius=14)
        pygame.draw.rect(screen, PANEL2, play_rect, border_radius=14)
        pygame.draw.rect(screen, BORDER, play_rect, 2, border_radius=14)
        pygame.draw.rect(screen, PANEL, sidebar_rect, border_radius=14)
        pygame.draw.rect(screen, BORDER, sidebar_rect, 2, border_radius=14)

        screen.blit(font_title.render("Periodic Table", True, WHITE), (left_rect.x + 14, left_rect.y + 12))
        if state == STATE_PLAY:
            sub = "Wheel = up/down. Bottom bar = left/right. Shelf items reusable."
        else:
            sub = "Start a level to play."
        screen.blit(font_tiny.render(sub, True, MUTED), (left_rect.x + 14, left_rect.y + 40))

        draw_shelf(screen, shelf_rect, shelf_items, font_tiny)

        clip = screen.get_clip()
        screen.set_clip(table_draw_area)
        for c in table_cells:
            r = c.rect.move(-hscroll, -vscroll)
            if r.right < table_draw_area.left or r.left > table_draw_area.right:
                continue
            if r.bottom < table_draw_area.top or r.top > table_draw_area.bottom:
                continue
            pygame.draw.rect(screen, (40, 44, 58), r, border_radius=8)
            pygame.draw.rect(screen, (85, 95, 120), r, 1, border_radius=8)
            screen.blit(font_z.render(str(c.z), True, (200, 200, 210)), (r.x + 5, r.y + 4))
            st = font_sym.render(c.sym, True, WHITE)
            screen.blit(st, st.get_rect(center=(r.centerx, r.centery + 4)))
        screen.set_clip(clip)

        draw_hscrollbar(screen, track_rect, h_knob, font_tiny)

        wm_rect = wm.get_rect(center=play_rect.center)
        clip = screen.get_clip()
        screen.set_clip(play_rect)
        screen.blit(wm, wm_rect)
        screen.set_clip(clip)

        if table_draw_area.collidepoint(mx, my):
            cell, _ = table_cell_under_mouse(mx, my)
            if cell:
                tip = f"{cell.z}  {cell.sym} — {cell.name}"
                tip_s = font_tiny.render(tip, True, (255, 245, 235))
                pad = 8
                box = tip_s.get_rect(topleft=(mx + 14, my + 10)).inflate(pad * 2, pad * 2)
                pygame.draw.rect(screen, (0, 0, 0), box, border_radius=10)
                pygame.draw.rect(screen, (255, 200, 140), box, 2, border_radius=10)
                screen.blit(tip_s, (box.x + pad, box.y + pad))

        if state == STATE_MENU:
            screen.blit(font_big.render("Ganeev's Chem Sim", True, WHITE),
                        (play_rect.centerx - 220, play_rect.y + 80))
            screen.blit(font_mid.render("Choose your goal (locks + stars)", True, MUTED),
                        (play_rect.centerx - 190, play_rect.y + 130))

            for lv, r in menu_buttons:
                unlocked = (lv["id"] <= save_data["unlocked"])
                draw_button(screen, r, "", font_mid, hovering=r.collidepoint(mx, my), enabled=unlocked)

                badge = pygame.Rect(r.x + 14, r.y + 18, 42, 42)
                pygame.draw.rect(screen, (25, 25, 30), badge, border_radius=12)
                pygame.draw.rect(screen, (160, 165, 190), badge, 2, border_radius=12)
                screen.blit(font_mid.render(str(lv["id"]), True, WHITE), font_mid.render(str(lv["id"]), True, WHITE).get_rect(center=badge.center))

                goal = font_mid.render(lv["goal_name"], True, WHITE if unlocked else (140, 145, 160))
                screen.blit(goal, (r.x + 70, r.y + 20))

                bs = save_data["best_stars"].get(str(lv["id"]), 0)
                stars = font_tiny.render(draw_stars_text(bs), True, (255, 220, 160) if bs > 0 else MUTED)
                screen.blit(stars, (r.x + 70, r.y + 54))

                if not unlocked:
                    lock = font_mid.render("LOCKED", True, (200, 200, 210))
                    screen.blit(lock, lock.get_rect(midright=(r.right - 16, r.centery)))

            screen.blit(font_title.render("Progress", True, WHITE), (sidebar_rect.x + 14, sidebar_rect.y + 12))
            info = [
                f"Unlocked: Level {save_data['unlocked']}/{len(LEVELS)}",
                "Beat a level to unlock next.",
                "",
                "Stars:",
                "≤ 1:00 → ★★★",
                "≤ 2:00 → ★★☆",
                "> 2:00 → ★☆☆",
            ]
            yy = sidebar_rect.y + 56
            for line in info:
                col = WHITE if line == "Stars:" else MUTED
                screen.blit(font_tiny.render(line, True, col), (sidebar_rect.x + 14, yy))
                yy += 18

        elif state == STATE_PLAY:
            draw_trashcan(screen, trash_rect, font_tiny,
                          hovering=trash_rect.collidepoint(mx, my) or (dragging_token and trash_rect.collidepoint((dragging_token.x, dragging_token.y))))
            draw_button(screen, clear_rect, "CLEAR", font_tiny, hovering=clear_rect.collidepoint(mx, my), enabled=True)
            draw_button(screen, hint_rect, "NEXT HINT", font_tiny, hovering=hint_rect.collidepoint(mx, my), enabled=True)

            if hint_flash_timer > 0:
                bubble = font_tiny.render(hint_message, True, WHITE)
                pad = 10
                box = bubble.get_rect()
                box.midbottom = (play_rect.centerx, play_rect.bottom - 92)
                box = box.inflate(pad * 2, pad * 2)
                pygame.draw.rect(screen, (0, 0, 0), box, border_radius=12)
                pygame.draw.rect(screen, (255, 220, 160), box, 2, border_radius=12)
                screen.blit(bubble, bubble.get_rect(center=box.center))

            for t in tokens:
                t.draw(screen, font_sym, font_tiny)
            for ex in explosions:
                ex.draw(screen, font_tiny)

            screen.blit(font_title.render("Level", True, WHITE), (sidebar_rect.x + 14, sidebar_rect.y + 12))
            screen.blit(font_tiny.render(f"{current_level['id']}: Make {current_level['goal_name']}", True, MUTED),
                        (sidebar_rect.x + 14, sidebar_rect.y + 50))
            if current_level["goal"] in made_set:
                g = font_tiny.render("✅ Goal completed!", True, GOOD)
            else:
                g = font_tiny.render("Goal not yet made", True, MUTED)
            screen.blit(g, (sidebar_rect.x + 14, sidebar_rect.y + 70))

            screen.blit(font_tiny.render("Made:", True, WHITE), (sidebar_rect.x + 14, sidebar_rect.y + 102))
            yy = sidebar_rect.y + 124
            if not made:
                screen.blit(font_tiny.render("(nothing yet)", True, MUTED), (sidebar_rect.x + 14, yy))
            else:
                for sym, nm in made[-26:]:
                    screen.blit(font_tiny.render(f"{sym} — {nm}", True, WHITE), (sidebar_rect.x + 14, yy))
                    yy += 18

            timer_txt = font_mid.render(fmt_time(level_elapsed), True, WHITE)
            screen.blit(timer_txt, timer_txt.get_rect(topright=(play_rect.right - 16, play_rect.top + 14)))

        elif state == STATE_END:
            screen.blit(font_big.render("LEVEL COMPLETE!", True, WHITE),
                        font_big.render("LEVEL COMPLETE!", True, WHITE).get_rect(center=(play_rect.centerx, play_rect.centery - 120)))

            msg = font_mid.render(end_message, True, (255, 220, 160))
            screen.blit(msg, msg.get_rect(center=(play_rect.centerx, play_rect.centery - 70)))

            stars = font_big.render(draw_stars_text(level_stars), True, (255, 220, 160))
            screen.blit(stars, stars.get_rect(center=(play_rect.centerx, play_rect.centery - 5)))

            draw_button(screen, end_menu_btn, "MENU", font_tiny, hovering=end_menu_btn.collidepoint(mx, my), enabled=True)

            next_id = current_level["id"] + 1
            next_enabled = (next_id <= len(LEVELS)) and (next_id <= save_data["unlocked"])
            draw_button(screen, end_next_btn, "NEXT", font_tiny, hovering=end_next_btn.collidepoint(mx, my), enabled=next_enabled)

            draw_button(screen, end_replay_btn, "REPLAY LEVEL", font_tiny, hovering=end_replay_btn.collidepoint(mx, my), enabled=True)

            screen.blit(font_title.render("Results", True, WHITE), (sidebar_rect.x + 14, sidebar_rect.y + 12))
            lines = [
                f"Time: {fmt_time(level_elapsed)}",
                f"Stars: {draw_stars_text(level_stars)}",
                "",
                f"Unlocked: Level {save_data['unlocked']}/{len(LEVELS)}",
            ]
            yy = sidebar_rect.y + 56
            for line in lines:
                screen.blit(font_tiny.render(line, True, MUTED), (sidebar_rect.x + 14, yy))
                yy += 18

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
