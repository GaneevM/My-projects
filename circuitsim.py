"""
Enhanced Grid Circuit Simulator
Features:
- Click-drag wires on Manhattan grid
- Click to place resistors, batteries, lightbulbs, and switches
- Adjustable voltage and resistance values
- Visual lightbulb brightness based on power (catches fire if overloaded!)
- Right-click components to edit values
- Click switches to toggle on/off
- Click on wires/nodes to probe voltage and current

Controls:
- 1 = Wire tool (click & drag)
- 2 = Resistor tool (click to place)
- 3 = Battery tool (click to place)
- 4 = Lightbulb tool (click to place)
- 5 = Switch tool (click to place, then click switch to toggle)
- E = Erase tool (click component or wire)
- V = Voltage probe tool (click wire/node to see voltage)
- I = Current probe tool (click wire to see current)
- R = Run simulation
- C = Clear all
- Right-click = Edit component values
- Scroll = Rotate component before placing
"""

import math
import pygame
import numpy as np

# Config
W, H = 1200, 760
PANEL_W = 320

GRID_SPACING = 28
GRID_MARGIN = 40
NODE_RADIUS = 4
WIRE_WIDTH = 4

DEFAULT_R = 100.0
DEFAULT_V = 9.0
DEFAULT_BULB_R = 50.0

# Component orientations (in grid units)
ORIENTATIONS = [
    (2, 0),   # horizontal right
    (0, 2),   # vertical down
    (-2, 0),  # horizontal left
    (0, -2),  # vertical up
]

# Helpers
def norm_edge(p, q):
    return (p, q) if p <= q else (q, p)

def manhattan_path(p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    path = []
    step = 1 if x1 >= x0 else -1
    for xx in range(x0, x1 + step, step):
        path.append((xx, y0))
    step = 1 if y1 >= y0 else -1
    for yy in range(y0 + step, y1 + step, step):
        path.append((x1, yy))
    return path

# Model
class Resistor:
    def __init__(self, a, b, ohms, rid):
        self.a = a
        self.b = b
        self.ohms = float(ohms)
        self.id = rid
        self.power = 0.0

class Battery:
    def __init__(self, plus, minus, volts, bid):
        self.plus = plus
        self.minus = minus
        self.volts = float(volts)
        self.id = bid

class Lightbulb:
    def __init__(self, a, b, ohms, lid):
        self.a = a
        self.b = b
        self.ohms = float(ohms)
        self.id = lid
        self.power = 0.0
        self.brightness = 0.0
        self.on_fire = False
        self.current = 0.0

class Switch:
    def __init__(self, a, b, sid):
        self.a = a
        self.b = b
        self.id = sid
        self.closed = True  # True = conducts, False = open circuit

# DSU for node merging
class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        if x not in self.p:
            self.p[x] = x
            return x
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra

def solve_dc(wires, resistors, batteries, lightbulbs, switches):
    if len(batteries) == 0:
        raise ValueError("Add at least one battery.")

    pts = set()
    for e in wires:
        pts.add(e[0]); pts.add(e[1])
    for r in resistors:
        pts.add(r.a); pts.add(r.b)
    for b in batteries:
        pts.add(b.plus); pts.add(b.minus)
    for lb in lightbulbs:
        pts.add(lb.a); pts.add(lb.b)
    for sw in switches:
        pts.add(sw.a); pts.add(sw.b)

    if not pts:
        raise ValueError("Nothing to solve.")

    dsu = DSU()
    for p in pts:
        dsu.find(p)
    for (p, q) in wires:
        dsu.union(p, q)
    
    # Closed switches act like wires
    for sw in switches:
        if sw.closed:
            dsu.union(sw.a, sw.b)

    ground_pt = batteries[0].minus
    ground = dsu.find(ground_pt)

    roots = {}
    for p in pts:
        rp = dsu.find(p)
        roots[rp] = True
    roots = list(roots.keys())

    node_roots = [r for r in roots if r != ground]
    node_roots.sort(key=lambda t: (t[0], t[1]))
    n = len(node_roots)

    idx = {root: i for i, root in enumerate(node_roots)}

    m = len(batteries)
    size = n + m
    if size == 0:
        return {ground: 0.0}, {ground_pt: 0.0}, {}, {}, {}, {}, ground_pt

    A = np.zeros((size, size), dtype=float)
    z = np.zeros((size,), dtype=float)

    def vi(root):
        if root == ground:
            return None
        return idx[root]

    # Stamp resistors
    for r in resistors:
        ra = dsu.find(r.a)
        rb = dsu.find(r.b)
        if ra == rb:
            continue
        g = 1.0 / r.ohms
        i = vi(ra)
        j = vi(rb)
        if i is not None:
            A[i, i] += g
        if j is not None:
            A[j, j] += g
        if i is not None and j is not None:
            A[i, j] -= g
            A[j, i] -= g

    # Stamp lightbulbs (they're just resistors)
    for lb in lightbulbs:
        ra = dsu.find(lb.a)
        rb = dsu.find(lb.b)
        if ra == rb:
            continue
        g = 1.0 / lb.ohms
        i = vi(ra)
        j = vi(rb)
        if i is not None:
            A[i, i] += g
        if j is not None:
            A[j, j] += g
        if i is not None and j is not None:
            A[i, j] -= g
            A[j, i] -= g

    # Stamp batteries
    for k, b in enumerate(batteries):
        row = n + k
        rp = dsu.find(b.plus)
        rm = dsu.find(b.minus)

        ip = vi(rp)
        im = vi(rm)

        if ip is not None:
            A[ip, row] += 1.0
            A[row, ip] += 1.0
        if im is not None:
            A[im, row] -= 1.0
            A[row, im] -= 1.0

        z[row] += b.volts

    try:
        x = np.linalg.solve(A, z)
    except np.linalg.LinAlgError:
        raise ValueError(
            "Can't solve circuit (singular).\n"
            "Check for floating sections or\n"
            "battery loops with no resistance."
        )

    node_voltage = {ground: 0.0}
    for root in node_roots:
        node_voltage[root] = float(x[idx[root]])

    point_voltage = {}
    for p in pts:
        point_voltage[p] = node_voltage[dsu.find(p)]

    resistor_current = {}
    for r in resistors:
        va = point_voltage.get(r.a, 0.0)
        vb = point_voltage.get(r.b, 0.0)
        i = (va - vb) / r.ohms
        resistor_current[r.id] = i
        r.power = abs(i * (va - vb))

    lightbulb_current = {}
    for lb in lightbulbs:
        va = point_voltage.get(lb.a, 0.0)
        vb = point_voltage.get(lb.b, 0.0)
        i = (va - vb) / lb.ohms
        lightbulb_current[lb.id] = i
        lb.current = abs(i)
        lb.power = abs(i * (va - vb))
        # Brightness: normalize to ~5W max for full brightness
        lb.brightness = min(1.0, lb.power / 5.0)
        
        # Fire detection: realistic bulb failure
        # Typical incandescent bulbs rated for ~60W at ~120V (household)
        # Small bulbs (like our 9V circuits) might be rated for 1-3W
        # If power exceeds 10W or current exceeds 0.5A, bulb catches fire
        MAX_SAFE_POWER = 10.0  # Watts
        MAX_SAFE_CURRENT = 0.5  # Amps
        
        if lb.power > MAX_SAFE_POWER or lb.current > MAX_SAFE_CURRENT:
            lb.on_fire = True
        else:
            lb.on_fire = False

    battery_current = {}
    for k, b in enumerate(batteries):
        battery_current[b.id] = float(x[n + k])

    # Calculate wire currents using KCL
    wire_currents = {}
    for edge in wires:
        p1, p2 = edge
        # Current from p1 to p2
        current = 0.0
        
        # Sum currents from components connected to p1
        for r in resistors:
            if r.a == p1:
                current += resistor_current[r.id]
            elif r.b == p1:
                current -= resistor_current[r.id]
        
        for lb in lightbulbs:
            if lb.a == p1:
                current += lightbulb_current[lb.id]
            elif lb.b == p1:
                current -= lightbulb_current[lb.id]
        
        for k, b in enumerate(batteries):
            if b.plus == p1:
                current += battery_current[b.id]
            elif b.minus == p1:
                current -= battery_current[b.id]
        
        wire_currents[edge] = current

    return node_voltage, point_voltage, resistor_current, battery_current, lightbulb_current, wire_currents, ground_pt

# UI
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def hit(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, screen, font, active=False):
        bg = (200, 225, 255) if active else (235, 235, 235)
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 2, border_radius=10)
        surf = font.render(self.text, True, (20, 20, 20))
        screen.blit(surf, (self.rect.x + 10, self.rect.y + 10))

class InputDialog:
    def __init__(self, title, fields):
        self.title = title
        self.fields = fields  # list of (label, initial_value)
        self.values = [str(v) for _, v in fields]
        self.active = 0
        self.result = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    self.result = [float(v) for v in self.values]
                    return True
                except:
                    pass
            elif event.key == pygame.K_ESCAPE:
                self.result = None
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.values[self.active] = self.values[self.active][:-1]
            elif event.key == pygame.K_TAB:
                self.active = (self.active + 1) % len(self.fields)
            elif event.unicode.isprintable():
                self.values[self.active] += event.unicode
        return False

    def draw(self, screen, font):
        box_w, box_h = 400, 80 + len(self.fields) * 60
        box_x = (W - box_w) // 2
        box_y = (H - box_h) // 2
        
        pygame.draw.rect(screen, (240, 240, 240), (box_x, box_y, box_w, box_h), border_radius=10)
        pygame.draw.rect(screen, (50, 50, 50), (box_x, box_y, box_w, box_h), 3, border_radius=10)
        
        title_surf = font.render(self.title, True, (20, 20, 20))
        screen.blit(title_surf, (box_x + 20, box_y + 20))
        
        for i, ((label, _), value) in enumerate(zip(self.fields, self.values)):
            y = box_y + 60 + i * 60
            label_surf = font.render(label + ":", True, (50, 50, 50))
            screen.blit(label_surf, (box_x + 20, y))
            
            input_rect = pygame.Rect(box_x + 150, y - 5, 230, 35)
            color = (200, 220, 255) if i == self.active else (255, 255, 255)
            pygame.draw.rect(screen, color, input_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), input_rect, 2, border_radius=5)
            
            value_surf = font.render(value, True, (20, 20, 20))
            screen.blit(value_surf, (input_rect.x + 8, input_rect.y + 8))

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Enhanced Circuit Simulator")

    font = pygame.font.SysFont("Arial", 18)
    big = pygame.font.SysFont("Arial", 22, bold=True)
    tiny = pygame.font.SysFont("Arial", 14)

    tool = "WIRE"
    wires = set()
    resistors = []
    batteries = []
    lightbulbs = []
    switches = []

    next_r = 0
    next_b = 0
    next_lb = 0
    next_sw = 0

    current_orientation = 0  # index into ORIENTATIONS

    solved = False
    pointV = {}
    rI = {}
    bI = {}
    lbI = {}
    wireI = {}
    ground_pt = None
    last_error = ""

    input_dialog = None

    btns = [
        ("WIRE", Button((20, 20, PANEL_W - 40, 44), "Wire [1]")),
        ("RES",  Button((20, 74, PANEL_W - 40, 44), "Resistor [2]")),
        ("BAT",  Button((20, 128, PANEL_W - 40, 44), "Battery [3]")),
        ("BULB", Button((20, 182, PANEL_W - 40, 44), "Lightbulb [4]")),
        ("SWITCH", Button((20, 236, PANEL_W - 40, 44), "Switch [5]")),
        ("VPROBE", Button((20, 290, PANEL_W - 40, 44), "Voltage Probe [V]")),
        ("IPROBE", Button((20, 344, PANEL_W - 40, 44), "Current Probe [I]")),
        ("ERASE",Button((20, 398, PANEL_W - 40, 44), "Erase [E]")),
    ]
    run_btn = Button((20, 462, PANEL_W - 40, 52), "RUN [R]")
    clr_btn = Button((20, 524, PANEL_W - 40, 52), "Clear [C]")

    info_y = 598

    wire_start = None
    wire_end = None
    dragging_wire = False

    ghost_component = None  # (type, grid_pos, orientation_idx)
    voltage_probes = set()  # grid points where user wants to see voltage
    current_probes = set()  # wire edges where user wants to see current

    def grid_from_mouse(mx, my):
        if mx < PANEL_W:
            return None
        gx = round((mx - PANEL_W - GRID_MARGIN) / GRID_SPACING)
        gy = round((my - GRID_MARGIN) / GRID_SPACING)
        return (gx, gy)

    def mouse_from_grid(gp):
        gx, gy = gp
        x = PANEL_W + GRID_MARGIN + gx * GRID_SPACING
        y = GRID_MARGIN + gy * GRID_SPACING
        return (x, y)

    def in_bounds(gp):
        x, y = mouse_from_grid(gp)
        return (PANEL_W + 10 <= x <= W - 10) and (10 <= y <= H - 10)

    def add_wire_path(p0, p1):
        path = manhattan_path(p0, p1)
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]
            if not in_bounds(a) or not in_bounds(b):
                continue
            if abs(a[0]-b[0]) + abs(a[1]-b[1]) != 1:
                continue
            wires.add(norm_edge(a, b))

    def get_component_at(gp):
        for r in resistors:
            if gp in (r.a, r.b):
                return ('resistor', r)
        for b in batteries:
            if gp in (b.plus, b.minus):
                return ('battery', b)
        for lb in lightbulbs:
            if gp in (lb.a, lb.b):
                return ('lightbulb', lb)
        for sw in switches:
            if gp in (sw.a, sw.b):
                return ('switch', sw)
        return None

    def erase_at(gp):
        nonlocal resistors, batteries, lightbulbs, switches, wires, solved
        
        x, y = gp
        nbrs = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
        for q in nbrs:
            e = norm_edge(gp, q)
            if e in wires:
                wires.remove(e)
                solved = False
                return

        resistors = [r for r in resistors if gp not in (r.a, r.b)]
        batteries = [b for b in batteries if gp not in (b.plus, b.minus)]
        lightbulbs = [lb for lb in lightbulbs if gp not in (lb.a, lb.b)]
        switches = [sw for sw in switches if gp not in (sw.a, sw.b)]
        solved = False

    def solve_now():
        nonlocal solved, pointV, rI, bI, lbI, wireI, last_error, ground_pt
        try:
            _, pointV, rI, bI, lbI, wireI, ground_pt = solve_dc(wires, resistors, batteries, lightbulbs, switches)
            solved = True
            last_error = ""
        except Exception as e:
            solved = False
            last_error = str(e)

    def clear_all():
        nonlocal wires, resistors, batteries, lightbulbs, switches, wire_start, wire_end, solved, pointV, rI, bI, lbI, wireI, last_error, ghost_component, voltage_probes, current_probes
        wires = set()
        resistors = []
        batteries = []
        lightbulbs = []
        switches = []
        wire_start = None
        wire_end = None
        solved = False
        pointV, rI, bI, lbI, wireI = {}, {}, {}, {}, {}
        last_error = ""
        ghost_component = None
        voltage_probes = set()
        current_probes = set()

    clock = pygame.time.Clock()

    while True:
        mouse_pos = pygame.mouse.get_pos()
        mouse_grid = grid_from_mouse(*mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            # Handle input dialog
            if input_dialog:
                if input_dialog.handle_event(event):
                    if input_dialog.result:
                        # Apply changes
                        comp_type, comp = input_dialog.component
                        if comp_type == 'resistor':
                            comp.ohms = input_dialog.result[0]
                        elif comp_type == 'battery':
                            comp.volts = input_dialog.result[0]
                        elif comp_type == 'lightbulb':
                            comp.ohms = input_dialog.result[0]
                        solved = False
                    input_dialog = None
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: tool = "WIRE"
                if event.key == pygame.K_2: tool = "RES"
                if event.key == pygame.K_3: tool = "BAT"
                if event.key == pygame.K_4: tool = "BULB"
                if event.key == pygame.K_5: tool = "SWITCH"
                if event.key == pygame.K_v: tool = "VPROBE"
                if event.key == pygame.K_i: tool = "IPROBE"
                if event.key == pygame.K_e: tool = "ERASE"
                if event.key == pygame.K_r: solve_now()
                if event.key == pygame.K_c: clear_all()

            if event.type == pygame.MOUSEWHEEL:
                # Rotate component orientation
                if tool in ("RES", "BAT", "BULB"):
                    current_orientation = (current_orientation + event.y) % 4

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                # Right click to edit
                if event.button == 3:
                    gp = grid_from_mouse(mx, my)
                    if gp and in_bounds(gp):
                        comp_info = get_component_at(gp)
                        if comp_info:
                            comp_type, comp = comp_info
                            if comp_type == 'resistor':
                                input_dialog = InputDialog("Edit Resistor", [("Resistance (Ω)", comp.ohms)])
                            elif comp_type == 'battery':
                                input_dialog = InputDialog("Edit Battery", [("Voltage (V)", comp.volts)])
                            elif comp_type == 'lightbulb':
                                input_dialog = InputDialog("Edit Lightbulb", [("Resistance (Ω)", comp.ohms)])
                            elif comp_type == 'switch':
                                # Toggle switch instead of edit
                                comp.closed = not comp.closed
                                # Auto-run if already solved once
                                if solved or len(pointV) > 0:
                                    solve_now()
                                else:
                                    solved = False
                                continue
                            input_dialog.component = comp_info
                    continue

                if event.button == 1:
                    clicked_ui = False
                    for t, b in btns:
                        if b.hit((mx, my)):
                            tool = t
                            clicked_ui = True
                    if run_btn.hit((mx, my)):
                        solve_now()
                        clicked_ui = True
                    if clr_btn.hit((mx, my)):
                        clear_all()
                        clicked_ui = True
                    if clicked_ui:
                        continue

                    gp = grid_from_mouse(mx, my)
                    if gp is None or not in_bounds(gp):
                        continue
                    
                    # Check if clicking on a switch to toggle it
                    comp_info = get_component_at(gp)
                    if comp_info and comp_info[0] == 'switch' and tool != "ERASE":
                        sw = comp_info[1]
                        sw.closed = not sw.closed
                        # Auto-run if already solved once
                        if solved or len(pointV) > 0:
                            solve_now()
                        else:
                            solved = False
                        continue

                    if tool == "WIRE":
                        wire_start = gp
                        wire_end = gp
                        dragging_wire = True

                    elif tool == "VPROBE":
                        # Toggle voltage probe at this point
                        if gp in voltage_probes:
                            voltage_probes.remove(gp)
                        else:
                            voltage_probes.add(gp)

                    elif tool == "IPROBE":
                        # Toggle current probe on nearby wire
                        x, y = gp
                        nbrs = [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]
                        found = False
                        for q in nbrs:
                            e = norm_edge(gp, q)
                            if e in wires:
                                if e in current_probes:
                                    current_probes.remove(e)
                                else:
                                    current_probes.add(e)
                                found = True
                                break
                        if not found:
                            # Just toggle the point itself as a marker
                            if gp in current_probes:
                                current_probes.discard(gp)
                            else:
                                # Find any adjacent wire edge
                                for q in nbrs:
                                    e = norm_edge(gp, q)
                                    if e in wires:
                                        current_probes.add(e)
                                        break

                    elif tool == "RES":
                        dx, dy = ORIENTATIONS[current_orientation]
                        b_pos = (gp[0] + dx, gp[1] + dy)
                        if in_bounds(b_pos):
                            resistors.append(Resistor(gp, b_pos, DEFAULT_R, next_r))
                            next_r += 1
                            solved = False

                    elif tool == "BAT":
                        dx, dy = ORIENTATIONS[current_orientation]
                        minus_pos = (gp[0] + dx, gp[1] + dy)
                        if in_bounds(minus_pos):
                            batteries.append(Battery(gp, minus_pos, DEFAULT_V, next_b))
                            next_b += 1
                            solved = False

                    elif tool == "BULB":
                        dx, dy = ORIENTATIONS[current_orientation]
                        b_pos = (gp[0] + dx, gp[1] + dy)
                        if in_bounds(b_pos):
                            lightbulbs.append(Lightbulb(gp, b_pos, DEFAULT_BULB_R, next_lb))
                            next_lb += 1
                            solved = False

                    elif tool == "SWITCH":
                        dx, dy = ORIENTATIONS[current_orientation]
                        b_pos = (gp[0] + dx, gp[1] + dy)
                        if in_bounds(b_pos):
                            switches.append(Switch(gp, b_pos, next_sw))
                            next_sw += 1
                            solved = False

                    elif tool == "ERASE":
                        erase_at(gp)

            if event.type == pygame.MOUSEMOTION:
                if dragging_wire and tool == "WIRE":
                    gp = grid_from_mouse(*event.pos)
                    if gp is not None and in_bounds(gp):
                        wire_end = gp

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging_wire and tool == "WIRE":
                    dragging_wire = False
                    if wire_start is not None and wire_end is not None:
                        add_wire_path(wire_start, wire_end)
                    wire_start = None
                    wire_end = None
                    solved = False

        # Update ghost component
        if tool in ("RES", "BAT", "BULB", "SWITCH") and mouse_grid and in_bounds(mouse_grid) and not input_dialog:
            ghost_component = (tool, mouse_grid, current_orientation)
        else:
            ghost_component = None

        # Draw
        screen.fill((250, 250, 250))

        # Panel
        pygame.draw.rect(screen, (245, 245, 245), (0, 0, PANEL_W, H))
        pygame.draw.line(screen, (210, 210, 210), (PANEL_W, 0), (PANEL_W, H), 2)

        screen.blit(big.render("Circuit Simulator", True, (20, 20, 20)), (20, H - 50))

        for t, b in btns:
            b.draw(screen, font, active=(tool == t))
        run_btn.draw(screen, font)
        clr_btn.draw(screen, font)

        # Info
        info = [
            "Click to place components",
            "Click-drag to draw wires",
            "Scroll to rotate before placing",
            "Right-click to edit values",
            "V: probe voltage at nodes",
            "I: probe current through wires",
        ]
        y = info_y
        for line in info:
            screen.blit(tiny.render(line, True, (60, 60, 60)), (20, y))
            y += 18

        if last_error:
            y += 10
            for line in last_error.splitlines():
                screen.blit(tiny.render(line, True, (140, 40, 40)), (20, y))
                y += 16

        # Grid
        gx_min, gx_max = -5, int((W - PANEL_W - 2 * GRID_MARGIN) / GRID_SPACING) + 5
        gy_min, gy_max = -2, int((H - 2 * GRID_MARGIN) / GRID_SPACING) + 2

        for gx in range(gx_min, gx_max + 1):
            for gy in range(gy_min, gy_max + 1):
                p = (gx, gy)
                if not in_bounds(p):
                    continue
                x, y = mouse_from_grid(p)
                pygame.draw.circle(screen, (220, 220, 220), (int(x), int(y)), NODE_RADIUS)

        # Wires
        for (a, b) in wires:
            x1, y1 = mouse_from_grid(a)
            x2, y2 = mouse_from_grid(b)
            pygame.draw.line(screen, (20, 20, 20), (x1, y1), (x2, y2), WIRE_WIDTH)
            
            # Draw current arrow only if this wire has a current probe
            edge = norm_edge(a, b)
            if solved and edge in current_probes and edge in wireI:
                current = wireI[edge]
                if abs(current) > 0.001:
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    
                    dx, dy = x2 - x1, y2 - y1
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        dx, dy = dx/length, dy/length
                        
                        if current < 0:
                            dx, dy = -dx, -dy
                        
                        arrow_len = 12
                        arrow_size = 6
                        end_x = mx + dx * arrow_len
                        end_y = my + dy * arrow_len
                        
                        perp_x, perp_y = -dy, dx
                        
                        wing1_x = end_x - dx * arrow_size - perp_x * arrow_size
                        wing1_y = end_y - dy * arrow_size - perp_y * arrow_size
                        wing2_x = end_x - dx * arrow_size + perp_x * arrow_size
                        wing2_y = end_y - dy * arrow_size + perp_y * arrow_size
                        
                        arrow_color = (200, 0, 200)
                        pygame.draw.line(screen, arrow_color, (mx, my), (end_x, end_y), 3)
                        pygame.draw.polygon(screen, arrow_color, [
                            (end_x, end_y),
                            (wing1_x, wing1_y),
                            (wing2_x, wing2_y)
                        ])
                        
                        label = f"{abs(current):.3g}A"
                        label_surf = tiny.render(label, True, (150, 0, 150))
                        label_bg = pygame.Surface((label_surf.get_width() + 8, label_surf.get_height() + 4))
                        label_bg.fill((255, 230, 255))
                        label_bg.set_alpha(230)
                        
                        label_x = mx + perp_x * 18
                        label_y = my + perp_y * 18
                        screen.blit(label_bg, (label_x - 4, label_y - 2))
                        screen.blit(label_surf, (label_x, label_y))
            
            # Show current probe marker (even when not solved)
            if edge in current_probes:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                pygame.draw.circle(screen, (200, 100, 200), (int(mx), int(my)), 6)
                pygame.draw.circle(screen, (150, 50, 150), (int(mx), int(my)), 6, 2)

        # Ghost wire
        if dragging_wire and wire_start and wire_end:
            path = manhattan_path(wire_start, wire_end)
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                if not in_bounds(a) or not in_bounds(b):
                    continue
                x1, y1 = mouse_from_grid(a)
                x2, y2 = mouse_from_grid(b)
                pygame.draw.line(screen, (80, 160, 255), (x1, y1), (x2, y2), WIRE_WIDTH)

        # Components
        def draw_line(p0, p1, color, width):
            x1, y1 = mouse_from_grid(p0)
            x2, y2 = mouse_from_grid(p1)
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), width)

        for r in resistors:
            draw_line(r.a, r.b, (70, 70, 70), 7)
            mx = (mouse_from_grid(r.a)[0] + mouse_from_grid(r.b)[0]) / 2
            my = (mouse_from_grid(r.a)[1] + mouse_from_grid(r.b)[1]) / 2
            label = f"{r.ohms:g}Ω"
            if solved and r.id in rI:
                label += f" {r.power:.2f}W"
            screen.blit(tiny.render(label, True, (10, 10, 10)), (mx + 8, my - 18))

        for b in batteries:
            draw_line(b.plus, b.minus, (40, 40, 40), 8)
            xP, yP = mouse_from_grid(b.plus)
            xM, yM = mouse_from_grid(b.minus)
            pygame.draw.circle(screen, (200, 50, 50), (int(xP), int(yP)), 8)
            pygame.draw.circle(screen, (50, 50, 200), (int(xM), int(yM)), 8)
            screen.blit(tiny.render("+", True, (255, 255, 255)), (xP - 4, yP - 8))
            screen.blit(tiny.render("-", True, (255, 255, 255)), (xM - 5, yM - 8))

            mx = (xP + xM) / 2
            my = (yP + yM) / 2
            label = f"{b.volts:g}V"
            if solved and b.id in bI:
                label += f" {bI[b.id]:.3g}A"
            screen.blit(tiny.render(label, True, (10, 10, 10)), (mx + 8, my - 18))

        for lb in lightbulbs:
            x1, y1 = mouse_from_grid(lb.a)
            x2, y2 = mouse_from_grid(lb.b)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            
            # Draw connection lines
            pygame.draw.line(screen, (60, 60, 60), (x1, y1), (mx, my), 4)
            pygame.draw.line(screen, (60, 60, 60), (mx, my), (x2, y2), 4)
            
            # Draw bulb shape - realistic bulb
            bulb_radius = 18
            
            # Glass bulb (circle)
            if solved and lb.on_fire:
                # FIRE! Draw animated fire effect
                import random
                fire_colors = [
                    (255, 69, 0),   # Red-orange
                    (255, 140, 0),  # Dark orange
                    (255, 215, 0),  # Gold
                    (255, 69, 0),   # Red-orange
                ]
                # Draw multiple flame particles
                for _ in range(8):
                    offset_x = random.randint(-8, 8)
                    offset_y = random.randint(-12, -2)
                    flame_size = random.randint(4, 10)
                    color = random.choice(fire_colors)
                    flame_x = int(mx + offset_x)
                    flame_y = int(my + offset_y)
                    pygame.draw.circle(screen, color, (flame_x, flame_y), flame_size)
                
                # Draw smoke
                smoke_color = (80, 80, 80)
                for i in range(3):
                    smoke_y = int(my - 15 - i * 8)
                    smoke_size = 5 + i * 2
                    pygame.draw.circle(screen, smoke_color, (int(mx), smoke_y), smoke_size)
                
                # Blackened bulb
                pygame.draw.circle(screen, (40, 40, 40), (int(mx), int(my)), bulb_radius)
                pygame.draw.circle(screen, (20, 20, 20), (int(mx), int(my)), bulb_radius, 3)
                
            elif solved:
                # Normal bulb with brightness
                brightness = int(255 * lb.brightness)
                # Bulb glows yellow when lit
                glow_color = (brightness, brightness, min(100 + int(brightness * 0.7), 255))
                inner_glow = max(0, brightness - 50)
                
                # Outer glow effect
                if brightness > 50:
                    for r in range(bulb_radius + 8, bulb_radius, -2):
                        alpha_glow = int((brightness / 255) * 30)
                        glow_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*glow_color, alpha_glow), (r, r), r)
                        screen.blit(glow_surf, (int(mx - r), int(my - r)))
                
                # Glass bulb
                pygame.draw.circle(screen, glow_color, (int(mx), int(my)), bulb_radius)
                
                # Filament (brighter center)
                if brightness > 20:
                    filament_color = (255, 255, min(255, 150 + inner_glow))
                    pygame.draw.circle(screen, filament_color, (int(mx), int(my)), int(bulb_radius * 0.4))
                
                # Glass outline
                pygame.draw.circle(screen, (120, 120, 120), (int(mx), int(my)), bulb_radius, 2)
            else:
                # Unlit bulb
                pygame.draw.circle(screen, (200, 200, 200), (int(mx), int(my)), bulb_radius)
                pygame.draw.circle(screen, (100, 100, 100), (int(mx), int(my)), bulb_radius, 2)
                # Filament visible when off
                pygame.draw.line(screen, (80, 80, 80), 
                               (int(mx - 6), int(my - 3)), 
                               (int(mx + 6), int(my + 3)), 2)
            
            # Screw base
            base_rect = pygame.Rect(int(mx - 6), int(my + bulb_radius - 5), 12, 8)
            pygame.draw.rect(screen, (150, 150, 150), base_rect)
            pygame.draw.line(screen, (100, 100, 100), 
                           (base_rect.left, base_rect.top + 3),
                           (base_rect.right, base_rect.top + 3), 1)
            pygame.draw.line(screen, (100, 100, 100), 
                           (base_rect.left, base_rect.top + 6),
                           (base_rect.right, base_rect.top + 6), 1)
            
            # Label
            label = f"{lb.ohms:g}Ω"
            if solved:
                if lb.on_fire:
                    label += " 🔥 OVERLOAD!"
                    label_color = (255, 0, 0)
                else:
                    label += f" {lb.power:.2f}W"
                    label_color = (10, 10, 10)
            else:
                label_color = (10, 10, 10)
            screen.blit(tiny.render(label, True, label_color), (mx + 24, my - 18))

        # Draw switches
        for sw in switches:
            x1, y1 = mouse_from_grid(sw.a)
            x2, y2 = mouse_from_grid(sw.b)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            
            # Draw terminals
            pygame.draw.circle(screen, (100, 100, 100), (int(x1), int(y1)), 6)
            pygame.draw.circle(screen, (100, 100, 100), (int(x2), int(y2)), 6)
            
            if sw.closed:
                # Closed switch - straight line
                pygame.draw.line(screen, (50, 150, 50), (x1, y1), (x2, y2), 5)
                status = "CLOSED"
                status_color = (0, 150, 0)
            else:
                # Open switch - angled line to show it's open
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    # Draw line from a to midpoint, then angled up
                    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                    # Perpendicular offset
                    perp_x, perp_y = -dy / length, dx / length
                    open_x = mid_x + perp_x * 15
                    open_y = mid_y + perp_y * 15
                    
                    pygame.draw.line(screen, (200, 50, 50), (x1, y1), (open_x, open_y), 5)
                    pygame.draw.line(screen, (200, 50, 50), (open_x, open_y), (x2, y2), 5)
                status = "OPEN"
                status_color = (200, 0, 0)
            
            # Label
            label = f"SW{sw.id} {status}"
            screen.blit(tiny.render(label, True, status_color), (mx + 8, my - 25))
            screen.blit(tiny.render("(click to toggle)", True, (100, 100, 100)), (mx + 8, my - 10))

        # Ghost component
        if ghost_component:
            comp_type, gp, ori_idx = ghost_component
            dx, dy = ORIENTATIONS[ori_idx]
            b_pos = (gp[0] + dx, gp[1] + dy)
            if in_bounds(b_pos):
                if comp_type == "RES":
                    draw_line(gp, b_pos, (150, 150, 255), 5)
                elif comp_type == "BAT":
                    draw_line(gp, b_pos, (150, 150, 255), 6)
                    xP, yP = mouse_from_grid(gp)
                    pygame.draw.circle(screen, (200, 150, 255), (int(xP), int(yP)), 6)
                elif comp_type == "BULB":
                    x1, y1 = mouse_from_grid(gp)
                    x2, y2 = mouse_from_grid(b_pos)
                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    pygame.draw.line(screen, (150, 150, 255), (x1, y1), (mx, my), 3)
                    pygame.draw.line(screen, (150, 150, 255), (mx, my), (x2, y2), 3)
                    pygame.draw.circle(screen, (200, 200, 255), (int(mx), int(my)), 12, 2)
                elif comp_type == "SWITCH":
                    x1, y1 = mouse_from_grid(gp)
                    x2, y2 = mouse_from_grid(b_pos)
                    pygame.draw.line(screen, (150, 150, 255), (x1, y1), (x2, y2), 4)

        # Show voltage probes
        if solved:
            for gp in voltage_probes:
                if gp in pointV:
                    x, y = mouse_from_grid(gp)
                    v = pointV[gp]
                    
                    # Draw probe marker
                    pygame.draw.circle(screen, (255, 200, 0), (int(x), int(y)), 8)
                    pygame.draw.circle(screen, (200, 150, 0), (int(x), int(y)), 8, 2)
                    
                    # Draw voltage label with background
                    label = f"{v:.2f}V"
                    label_surf = tiny.render(label, True, (0, 0, 0))
                    label_bg = pygame.Surface((label_surf.get_width() + 8, label_surf.get_height() + 4))
                    label_bg.fill((255, 255, 200))
                    label_bg.set_alpha(230)
                    
                    label_x, label_y = x + 12, y - 10
                    screen.blit(label_bg, (label_x - 4, label_y - 2))
                    screen.blit(label_surf, (label_x, label_y))
        
        # Show probe markers even when not solved
        if not solved:
            for gp in voltage_probes:
                if in_bounds(gp):
                    x, y = mouse_from_grid(gp)
                    pygame.draw.circle(screen, (200, 200, 200), (int(x), int(y)), 8)
                    pygame.draw.circle(screen, (150, 150, 150), (int(x), int(y)), 8, 2)

        # Draw watermark in center of canvas
        # Try cursive fonts, fallback to italic
        available_fonts = pygame.font.get_fonts()
        cursive_fonts = ['brushscriptmt', 'brushscript', 'lucidahandwriting', 'zapfchancery', 'mistral']
        
        watermark_font = None
        for font_name in cursive_fonts:
            if font_name in available_fonts:
                try:
                    watermark_font = pygame.font.SysFont(font_name, 72)
                    break
                except:
                    continue
        
        if watermark_font is None:
            # Fallback to italic
            watermark_font = pygame.font.SysFont("Arial", 60, italic=True)
        
        watermark_text = "Ganeev's Circuit Sim"
        watermark_surf = watermark_font.render(watermark_text, True, (180, 180, 180))
        watermark_surf.set_alpha(120)  # More visible but still faded
        watermark_x = PANEL_W + (W - PANEL_W - watermark_surf.get_width()) // 2
        watermark_y = (H - watermark_surf.get_height()) // 2
        screen.blit(watermark_surf, (watermark_x, watermark_y))

        # Draw input dialog on top
        if input_dialog:
            # Semi-transparent overlay
            overlay = pygame.Surface((W, H))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            input_dialog.draw(screen, font)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()