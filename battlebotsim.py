import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1200, 750
FPS = 60

WHITE = (245, 245, 245)
BLACK = (20, 20, 25)
RED = (200, 40, 40)
BLUE = (40, 80, 200)
STEEL = (140, 145, 155)
DARK_STEEL = (60, 65, 70)
GOLD = (218, 165, 32)
NEON_GREEN = (57, 255, 20)
PANEL_BG = (35, 38, 45)

HEADS = {
    "Sentry Dome": {"hp": 60, "color": (100, 140, 180), "shape": "dome", "desc": "Lightweight. Features a 'Determined' face. Low HP."},
    "Iron Cube": {"hp": 110, "color": (150, 60, 60), "shape": "cube", "desc": "Heavy plating. Features a 'Grumpy' face. High HP."},
    "Spike Unit": {"hp": 80, "color": (180, 130, 40), "shape": "spike", "desc": "Aerodynamic. Features a 'Crazy' face. Balanced."}
}

BODIES = {
    "Scout": {"hp": 120, "speed": 6.5, "accel": 0.8, "mass": 1.0, "color": (130, 180, 130), "size": (45, 55), "desc": "High agility. Very low armor. Drifts easily."},
    "Warrior": {"hp": 180, "speed": 4.5, "accel": 0.5, "mass": 2.0, "color": (130, 130, 170), "size": (55, 65), "desc": "Standard military chassis. Reliable movement."},
    "Goliath": {"hp": 300, "speed": 2.8, "accel": 0.2, "mass": 4.0, "color": (160, 120, 80), "size": (75, 85), "desc": "Slow juggernaut. Extreme HP. Hard to stop."}
}

ARMS = {
    "Plasma Blaster": {"damage": 28, "cooldown": 35, "range": 450, "type": "projectile", "color": NEON_GREEN, "desc": "Long range plasma bolts. High recoil."},
    "Pulse Laser": {"damage": 5, "cooldown": 1, "range": 320, "type": "beam", "color": (0, 255, 255), "desc": "Continuous energy beam. No travel time."},
    "Mega Hammer": {"damage": 85, "cooldown": 70, "range": 130, "type": "melee", "color": STEEL, "desc": "Crushing melee damage. Slow swing speed."}
}

LEGS = {
    "Heavy Wheels": {"speed_mult": 1.4, "def": 5, "friction": 0.92, "color": (30, 30, 30), "desc": "Highest top speed. Poor defense."},
    "Tank Treads": {"speed_mult": 0.8, "def": 20, "friction": 0.85, "color": (70, 65, 60), "desc": "Unstoppable traction. Massive armor bonus."},
    "Mag-Lev": {"speed_mult": 1.2, "def": 8, "friction": 0.98, "color": (100, 180, 220), "desc": "Smooth hovering. Excellent control."}
}

def draw_mech_part(screen, x, y, p_type, p_name, scale=1.0, angle=0, flip=False):
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    cx, cy = 100, 100
    
    if p_type == "head":
        d = HEADS[p_name]
        main_c = d["color"]
        if d["shape"] == "dome":
            pygame.draw.circle(surface, main_c, (cx, cy), 35)
            pygame.draw.circle(surface, WHITE, (cx-10, cy-5), 6)
            pygame.draw.circle(surface, WHITE, (cx+10, cy-5), 6)
            pygame.draw.circle(surface, BLACK, (cx-10, cy-5), 2)
            pygame.draw.circle(surface, BLACK, (cx+10, cy-5), 2)
            pygame.draw.line(surface, BLACK, (cx-10, cy+15), (cx+10, cy+15), 3)
        elif d["shape"] == "cube":
            pygame.draw.rect(surface, main_c, (cx-30, cy-30, 60, 60), 0, 5)
            pygame.draw.line(surface, BLACK, (cx-15, cy-15), (cx-5, cy-10), 3)
            pygame.draw.line(surface, BLACK, (cx+15, cy-15), (cx+5, cy-10), 3)
            pygame.draw.rect(surface, (255, 50, 50), (cx-12, cy+10, 24, 4))
        elif d["shape"] == "spike":
            pygame.draw.polygon(surface, main_c, [(cx, cy-45), (cx-30, cy+20), (cx+30, cy+20)])
            pygame.draw.circle(surface, WHITE, (cx-8, cy-5), 10)
            pygame.draw.circle(surface, WHITE, (cx+8, cy-5), 5)
            pygame.draw.circle(surface, BLACK, (cx-8, cy-5), 4)
            pygame.draw.circle(surface, BLACK, (cx+8, cy-5), 2)
            pygame.draw.arc(surface, BLACK, (cx-10, cy+2, 20, 15), 3.14, 0, 3)

    elif p_type == "body":
        w, h = BODIES[p_name]["size"]
        pygame.draw.rect(surface, BODIES[p_name]["color"], (cx-w//2, cy-h//2, w, h), 0, 10)
        pygame.draw.rect(surface, (0,0,0,150), (cx-w//2, cy-h//2, w, h), 4, 10)
        for i in range(4): pygame.draw.line(surface, (40,40,40), (cx-w//2+8, cy-20+i*12), (cx+w//2-8, cy-20+i*12), 3)

    elif p_type == "arms":
        if p_name == "Mega Hammer":
            pygame.draw.rect(surface, DARK_STEEL, (cx-6, cy, 12, 60))
            pygame.draw.rect(surface, STEEL, (cx-25, cy-20, 50, 40), 0, 4)
        elif p_name == "Pulse Laser":
            pygame.draw.rect(surface, DARK_STEEL, (cx-12, cy-12, 65, 24), 0, 6)
            pygame.draw.circle(surface, (0, 255, 255), (cx+50, cy), 8)
        elif p_name == "Plasma Blaster":
            pygame.draw.rect(surface, (50,50,55), (cx-10, cy-18, 75, 36), 0, 3)
            pygame.draw.rect(surface, NEON_GREEN, (cx+40, cy-12, 20, 24))

    elif p_type == "legs":
        if p_name == "Heavy Wheels":
            pygame.draw.circle(surface, (20,20,25), (cx-35, cy+10), 22)
            pygame.draw.circle(surface, (20,20,25), (cx+35, cy+10), 22)
        elif p_name == "Tank Treads":
            pygame.draw.rect(surface, (30,30,30), (cx-55, cy, 110, 35), 0, 12)
        elif p_name == "Mag-Lev":
            pygame.draw.ellipse(surface, (100, 200, 255, 160), (cx-50, cy+5, 100, 30))

    if flip: surface = pygame.transform.flip(surface, True, False)
    rotated = pygame.transform.rotozoom(surface, angle, scale)
    screen.blit(rotated, (x - rotated.get_width()//2, y - rotated.get_height()//2))

class Projectile:
    def __init__(self, x, y, angle, damage, color, owner):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle)*15, math.sin(angle)*15
        self.damage, self.color, self.owner = damage, color, owner
        self.alive = True

    def update(self, target):
        self.x += self.vx
        self.y += self.vy
        if math.hypot(target.x - self.x, target.y - self.y) < 55:
            target.hp -= self.damage
            self.alive = False
        if not (0 < self.x < WIDTH and 0 < self.y < HEIGHT): self.alive = False

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 10)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 5)

class Robot:
    def __init__(self, x, y, parts, p_num):
        self.x, self.y, self.p_num, self.parts = x, y, p_num, parts
        self.hp = HEADS[parts['head']]['hp'] + BODIES[parts['body']]['hp']
        self.max_hp = self.hp
        self.vx, self.vy = 0, 0
        self.stats = BODIES[parts['body']]
        self.l_stats = LEGS[parts['legs']]
        self.arm_stats = ARMS[parts['arms']]
        self.cooldown, self.bob, self.arm_angle = 0, 0, 0

    def move(self, keys):
        if self.hp <= 0: return
        ax, ay = 0, 0
        u, d, l, r = (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d) if self.p_num==1 else (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
        if keys[u]: ay -= self.stats['accel']
        if keys[d]: ay += self.stats['accel']
        if keys[l]: ax -= self.stats['accel']
        if keys[r]: ax += self.stats['accel']
        self.vx = (self.vx + ax) * self.l_stats['friction']
        self.vy = (self.vy + ay) * self.l_stats['friction']
        self.x += self.vx * self.l_stats['speed_mult']
        self.y += self.vy * self.l_stats['speed_mult']
        self.x, self.y = max(60, min(WIDTH-60, self.x)), max(60, min(HEIGHT-60, self.y))

    def action(self, enemy, projectiles):
        if self.hp <= 0: return
        if self.cooldown > 0: self.cooldown -= 1
        dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
        if dist < self.arm_stats['range'] and self.cooldown == 0:
            if self.arm_stats['type'] == "projectile":
                ang = math.atan2(enemy.y - self.y, enemy.x - self.x)
                projectiles.append(Projectile(self.x, self.y, ang, self.arm_stats['damage'], self.arm_stats['color'], self.p_num))
                self.cooldown = self.arm_stats['cooldown']
            elif self.arm_stats['type'] == "melee":
                self.arm_angle = 90
                enemy.hp -= max(5, self.arm_stats['damage'] - enemy.l_stats['def'])
                self.cooldown = self.arm_stats['cooldown']
            elif self.arm_stats['type'] == "beam":
                enemy.hp -= self.arm_stats['damage'] / 8

    def draw(self, screen, enemy):
        if self.hp <= 0: return
        self.bob = math.sin(pygame.time.get_ticks() * 0.01) * 4
        if self.arm_angle > 0: self.arm_angle -= 6
        bx, by = self.x, self.y + self.bob
        if self.arm_stats['type'] == "beam" and math.hypot(enemy.x-self.x, enemy.y-self.y) < self.arm_stats['range']:
            pygame.draw.line(screen, self.arm_stats['color'], (bx, by), (enemy.x, enemy.y), 6)
        is_left = self.x > enemy.x
        draw_mech_part(screen, bx, by+40, "legs", self.parts['legs'])
        draw_mech_part(screen, bx-45, by, "arms", self.parts['arms'], angle=self.arm_angle, flip=is_left)
        draw_mech_part(screen, bx+45, by, "arms", self.parts['arms'], angle=-self.arm_angle, flip=not is_left)
        draw_mech_part(screen, bx, by, "body", self.parts['body'])
        draw_mech_part(screen, bx, by-55, "head", self.parts['head'])
        pygame.draw.rect(screen, BLACK, (bx-52, by-102, 104, 14))
        p = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, RED if self.p_num==1 else BLUE, (bx-50, by-100, 100*p, 10))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Ganeev's Battlebot Sim")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Impact", 28)
        self.sm_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.lg_font = pygame.font.SysFont("Impact", 80)
        self.state = "MENU"
        self.reset()

    def reset(self):
        self.p1_b = {"head": "Sentry Dome", "body": "Warrior", "arms": "Pulse Laser", "legs": "Heavy Wheels"}
        self.p2_b = {"head": "Sentry Dome", "body": "Warrior", "arms": "Pulse Laser", "legs": "Heavy Wheels"}
        self.p_turn, self.is_sp, self.projectiles, self.winner = 1, True, [], None

    def draw_forge(self):
        self.screen.fill(PANEL_BG)
        b = self.p1_b if self.p_turn == 1 else self.p2_b
        self.btns = []
        hover_desc = ""
        m_pos = pygame.mouse.get_pos()

        for i, (cat, data) in enumerate([("head", HEADS), ("body", BODIES), ("arms", ARMS), ("legs", LEGS)]):
            y = 100 + i * 120
            self.screen.blit(self.font.render(cat.upper(), True, GOLD), (50, y))
            for j, name in enumerate(data.keys()):
                r = pygame.Rect(50 + j*130, y+40, 120, 60)
                is_hover = r.collidepoint(m_pos)
                pygame.draw.rect(self.screen, GOLD if b[cat]==name else (STEEL if is_hover else DARK_STEEL), r, 0, 8)
                self.screen.blit(self.sm_font.render(name, True, BLACK), (r.x+10, r.y+20))
                self.btns.append((r, cat, name))
                if is_hover: hover_desc = data[name]["desc"]
        
        if hover_desc:
            pygame.draw.rect(self.screen, BLACK, (50, 650, 600, 40), 0, 5)
            self.screen.blit(self.sm_font.render(hover_desc, True, WHITE), (70, 660))

        pygame.draw.rect(self.screen, BLACK, (WIDTH-450, 100, 400, 500), 0, 20)
        p_bot = Robot(WIDTH-250, 350, b, self.p_turn)
        p_bot.draw(self.screen, p_bot)
        self.b_ready = pygame.draw.rect(self.screen, NEON_GREEN, (WIDTH-350, 620, 200, 60), 0, 12)
        self.screen.blit(self.font.render("LOCK IN", True, BLACK), (WIDTH-295, 630))

    def run(self):
        while True:
            m_pos = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "MENU":
                        if pygame.Rect(WIDTH//2-150, 350, 300, 60).collidepoint(m_pos): self.is_sp, self.state = True, "FORGE"
                        if pygame.Rect(WIDTH//2-150, 450, 300, 60).collidepoint(m_pos): self.is_sp, self.state = False, "FORGE"
                    elif self.state == "FORGE":
                        for r, cat, n in self.btns:
                            if r.collidepoint(m_pos): 
                                if self.p_turn == 1: self.p1_b[cat] = n
                                else: self.p2_b[cat] = n
                        if self.b_ready.collidepoint(m_pos):
                            if self.p_turn == 1 and not self.is_sp: self.p_turn = 2
                            else:
                                if self.is_sp: self.p2_b = {"head": random.choice(list(HEADS)), "body": random.choice(list(BODIES)), "arms": random.choice(list(ARMS)), "legs": random.choice(list(LEGS))}
                                self.r1, self.r2 = Robot(200,375,self.p1_b,1), Robot(1000,375,self.p2_b,2)
                                self.state = "BATTLE"
                    elif self.state == "WIN" and pygame.Rect(WIDTH//2-100, 450, 200, 60).collidepoint(m_pos):
                        self.reset(); self.state = "MENU"

            if self.state == "MENU":
                self.screen.fill(BLACK)
                t = self.lg_font.render("GANEEV'S BATTLEBOT SIM", True, WHITE)
                self.screen.blit(t, (WIDTH//2-t.get_width()//2, 150))
                pygame.draw.rect(self.screen, STEEL, (WIDTH//2-150, 350, 300, 60), 0, 12)
                pygame.draw.rect(self.screen, STEEL, (WIDTH//2-150, 450, 300, 60), 0, 12)
                self.screen.blit(self.font.render("SINGLE PLAYER", True, BLACK), (WIDTH//2-85, 362))
                self.screen.blit(self.font.render("MULTIPLAYER", True, BLACK), (WIDTH//2-75, 462))
            elif self.state == "FORGE": self.draw_forge()
            elif self.state == "BATTLE":
                self.screen.fill((40, 42, 45))
                wm = self.lg_font.render("GANEEV'S BATTLEBOT SIM", True, (0,0,0,30))
                self.screen.blit(wm, (WIDTH//2-wm.get_width()//2, HEIGHT//2-50))
                keys = pygame.key.get_pressed()
                self.r1.move(keys)
                if self.is_sp:
                    d = math.hypot(self.r1.x-self.r2.x, self.r1.y-self.r2.y)
                    if d > 150: self.r2.vx += (self.r1.x-self.r2.x)/d * 0.2; self.r2.vy += (self.r1.y-self.r2.y)/d * 0.2
                    self.r2.x += self.r2.vx; self.r2.y += self.r2.vy
                else: self.r2.move(keys)
                self.r1.action(self.r2, self.projectiles); self.r2.action(self.r1, self.projectiles)
                for p in self.projectiles[:]:
                    p.update(self.r1 if p.owner==2 else self.r2)
                    p.draw(self.screen)
                    if not p.alive: self.projectiles.remove(p)
                self.r1.draw(self.screen, self.r2); self.r2.draw(self.screen, self.r1)
                if self.r1.hp <= 0 or self.r2.hp <= 0: self.winner, self.state = (1 if self.r1.hp > 0 else 2), "WIN"
            elif self.state == "WIN":
                self.screen.fill(BLACK)
                c = RED if self.winner == 1 else BLUE
                t = self.lg_font.render(f"PLAYER {self.winner} VICTORIOUS", True, c)
                self.screen.blit(t, (WIDTH//2-t.get_width()//2, 250))
                pygame.draw.rect(self.screen, WHITE, (WIDTH//2-100, 450, 200, 60), 0, 12)
                self.screen.blit(self.font.render("RESTART", True, BLACK), (WIDTH//2-50, 462))
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    Game().run()
