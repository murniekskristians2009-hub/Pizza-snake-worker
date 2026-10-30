import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import random
import math
from game.logic import PizzaSnakeGame, DIFFICULTIES, GRID_OPTIONS

# Nosaka precīzu ceļu līdz projekta saknes mapei (kur atrodas .png)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- Konfigurācija ----------
BOARD_SIZE = 600
PANEL_WIDTH = 280
WIDTH = BOARD_SIZE + PANEL_WIDTH
HEIGHT = BOARD_SIZE

BG = (15, 12, 41)
BOARD_BG = (26, 26, 46)
GRID_LINE = (40, 40, 70)
SNAKE_HEAD = (134, 239, 172)
SNAKE_BODY = (74, 222, 128)
SNAKE_SHADOW = (10, 40, 20)
SHIELD_COLOR = (80, 200, 255)
TEXT_LIGHT = (230, 230, 250)
TEXT_DIM = (140, 140, 170)
ACCENT = (74, 222, 128)
PANEL_BG = (22, 22, 42)
BTN_BG = (40, 40, 70)
BTN_HOVER = (60, 60, 100)
BTN_ACTIVE = (74, 222, 128)
BTN_ACTIVE_TEXT = (15, 12, 41)

SPLINE_SAMPLES = 6

def load_and_scale_image(filename, size):
    try:
        # Pievieno pilnu ceļu, lai atrastu bildi jebkurā gadījumā
        full_path = os.path.join(BASE_DIR, filename)
        img = pygame.image.load(full_path).convert_alpha()
        return pygame.transform.smoothscale(img, (size, size))
    except Exception as e:
        # Ja bildes nav, spēle nemetīs erroru, bet uzzīmēs apli
        return None

def catmull_rom_segment(p0, p1, p2, p3, samples):
    pts = []
    for i in range(samples):
        t = i / samples; t2 = t * t; t3 = t2 * t
        x = 0.5 * (2*p1[0] + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
        y = 0.5 * (2*p1[1] + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
        pts.append((x, y))
    pts.append(p2)
    return pts

def build_spline(positions, samples=SPLINE_SAMPLES):
    if len(positions) < 2: return list(positions)
    if len(positions) == 2: return [positions[0], positions[1]]
    ext = [positions[0]] + list(positions) + [positions[-1]]
    dense = []
    for i in range(len(ext) - 3):
        seg = catmull_rom_segment(ext[i], ext[i+1], ext[i+2], ext[i+3], samples)
        if i == 0: dense.extend(seg)
        else: dense.extend(seg[1:])
    return dense

def draw_snake(screen, game, cell_size, t, ox=0, oy=0):
    if not game.snake: return
    positions = []
    for i, (tx, ty) in enumerate(game.snake):
        if i < len(game.prev_snake):
            fx, fy = game.prev_snake[i]
        else:
            fx, fy = game.prev_snake[-1] if game.prev_snake else game.snake[-1]
        gx = fx + (tx - fx) * t
        gy = fy + (ty - fy) * t
        positions.append((gx * cell_size + cell_size / 2 + ox, gy * cell_size + cell_size / 2 + oy))

    dense = build_spline(positions, SPLINE_SAMPLES)
    radius = int(cell_size * 0.42)

    for i in range(len(dense) - 1):
        p1 = (round(dense[i][0]) + 1, round(dense[i][1]) + 2)
        p2 = (round(dense[i+1][0]) + 1, round(dense[i+1][1]) + 2)
        pygame.draw.line(screen, SNAKE_SHADOW, p1, p2, radius * 2)
    for p in dense:
        pygame.draw.circle(screen, SNAKE_SHADOW, (round(p[0]) + 1, round(p[1]) + 2), radius)

    for i in range(len(dense) - 1):
        p1 = (round(dense[i][0]), round(dense[i][1]))
        p2 = (round(dense[i+1][0]), round(dense[i+1][1]))
        pygame.draw.line(screen, SNAKE_BODY, p1, p2, radius * 2)
    for p in dense:
        pygame.draw.circle(screen, SNAKE_BODY, (round(p[0]), round(p[1])), radius)

    head = positions[0]
    pygame.draw.circle(screen, SNAKE_HEAD, (round(head[0]), round(head[1])), radius)

    eye_dir = game.input_queue[0] if game.input_queue else game.direction
    dx, dy = eye_dir
    px, py = -dy, dx
    off = radius * 0.45; fwd = radius * 0.2
    e1 = (head[0] + dx * fwd + px * off, head[1] + dy * fwd + py * off)
    e2 = (head[0] + dx * fwd - px * off, head[1] + dy * fwd - py * off)
    pygame.draw.circle(screen, (255, 255, 255), (int(e1[0]), int(e1[1])), max(2, radius // 4))
    pygame.draw.circle(screen, (255, 255, 255), (int(e2[0]), int(e2[1])), max(2, radius // 4))
    pygame.draw.circle(screen, (10, 10, 10), (int(e1[0] + dx*2), int(e1[1] + dy*2)), max(1, radius // 8))
    pygame.draw.circle(screen, (10, 10, 10), (int(e2[0] + dx*2), int(e2[1] + dy*2)), max(1, radius // 8))

    if game.invincible_time > 0:
        pulse = (math.sin(pygame.time.get_ticks() / 80) + 1) / 2
        shield_alpha = int(100 + 100 * pulse)
        shield_radius = radius + 3
        shield_surf = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        for i in range(len(dense) - 1):
            pygame.draw.line(shield_surf, (*SHIELD_COLOR, shield_alpha), (round(dense[i][0]), round(dense[i][1])), (round(dense[i+1][0]), round(dense[i+1][1])), shield_radius * 2)
        for p in dense:
            pygame.draw.circle(shield_surf, (*SHIELD_COLOR, shield_alpha), (round(p[0]), round(p[1])), shield_radius)
            pygame.draw.circle(shield_surf, (0, 0, 0, 0), (round(p[0]), round(p[1])), radius)
        screen.blit(shield_surf, (0, 0))

def draw_button(screen, rect, text, active, hover, font, buttons, name):
    color = BTN_ACTIVE if active else (BTN_HOVER if hover else BTN_BG)
    text_color = BTN_ACTIVE_TEXT if active else TEXT_LIGHT
    pygame.draw.rect(screen, color, rect, border_radius=8)
    lbl = font.render(text, True, text_color)
    screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))
    buttons[name] = rect

def draw_value_row(screen, px, y, minus_name, plus_name, value_text, font, buttons, mouse_pos, value_color):
    minus_rect = pygame.Rect(px + 15, y, 50, 40)
    plus_rect = pygame.Rect(px + PANEL_WIDTH - 65, y, 50, 40)
    val_rect = pygame.Rect(px + 70, y, PANEL_WIDTH - 145, 40)
    draw_button(screen, minus_rect, "-", False, minus_rect.collidepoint(mouse_pos), font, buttons, minus_name)
    draw_button(screen, plus_rect, "+", False, plus_rect.collidepoint(mouse_pos), font, buttons, plus_name)
    pygame.draw.rect(screen, (30, 30, 55), val_rect, border_radius=8)
    txt = font.render(value_text, True, value_color)
    screen.blit(txt, (val_rect.centerx - txt.get_width() // 2, val_rect.centery - txt.get_height() // 2))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pizza Snake Worker")
    clock = pygame.time.Clock()
    
    fonts = (
        pygame.font.SysFont("segoeui", 30, bold=True),
        pygame.font.SysFont("segoeui", 22, bold=True),
        pygame.font.SysFont("segoeui", 18),
        pygame.font.SysFont("segoeui", 14),
    )
    font_big, font_med, font, font_sm = fonts

    game = PizzaSnakeGame()
    buttons = {}
    running = True

    while running:
        dt = clock.tick(120)
        cell_size = BOARD_SIZE // game.grid_size
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
            
            if event.type == pygame.KEYDOWN:
                # --- SPACE STRĀDĀ VISUR ---
                if event.key == pygame.K_SPACE:
                    if game.state == "menu":
                        if len(game.username) == 0: game.username = "Speletajs"
                        game.start()
                    elif game.state == "playing":
                        game.state = "paused"
                    elif game.state == "paused":
                        game.state = "playing"
                    elif game.state == "gameover":
                        game.start()
                
                elif event.key == pygame.K_r and game.state == "gameover":
                    game.state = "menu"
                    game.username = ""
                
                elif game.state == "menu":
                    if event.key == pygame.K_RETURN:
                        if len(game.username) == 0: game.username = "Speletajs"
                        game.start()
                    elif event.key == pygame.K_BACKSPACE:
                        game.username = game.username[:-1]
                    elif event.unicode.isprintable() and len(game.username) < 12:
                        game.username += event.unicode
                        
                elif game.state == "playing":
                    if event.key in (pygame.K_UP, pygame.K_w): game.change_direction((0, -1))
                    elif event.key in (pygame.K_DOWN, pygame.K_s): game.change_direction((0, 1))
                    elif event.key in (pygame.K_LEFT, pygame.K_a): game.change_direction((-1, 0))
                    elif event.key in (pygame.K_RIGHT, pygame.K_d): game.change_direction((1, 0))
                    
            # --- PELES KLIKŠĶI UZ POGĀM ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 'diff_0' in buttons and buttons['diff_0'].collidepoint(event.pos): game.difficulty_idx = 0
                elif 'diff_1' in buttons and buttons['diff_1'].collidepoint(event.pos): game.difficulty_idx = 1
                elif 'diff_2' in buttons and buttons['diff_2'].collidepoint(event.pos): game.difficulty_idx = 2
                elif 'pizza_minus' in buttons and buttons['pizza_minus'].collidepoint(event.pos): game.adjust_pizza_count(-1)
                elif 'pizza_plus' in buttons and buttons['pizza_plus'].collidepoint(event.pos): game.adjust_pizza_count(1)
                elif 'grid_minus' in buttons and buttons['grid_minus'].collidepoint(event.pos): game.change_grid_size(-1)
                elif 'grid_plus' in buttons and buttons['grid_plus'].collidepoint(event.pos): game.change_grid_size(1)
                elif 'start' in buttons and buttons['start'].collidepoint(event.pos): game.start()

        game.update(dt)
        screen.fill(BG)
        buttons.clear()

        if game.state == "menu":
            title = font_big.render("PIZZA SNAKE WORKER", True, ACCENT)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
            inst = font.render("Ievadi vārdu un spied ENTER vai SPACE:", True, TEXT_LIGHT)
            screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT//2 - 40))
            
            name_box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2, 300, 50)
            pygame.draw.rect(screen, (30, 30, 55), name_box, border_radius=8)
            pygame.draw.rect(screen, ACCENT, name_box, 2, border_radius=8)
            name_txt = font_med.render(game.username + "_", True, TEXT_LIGHT)
            screen.blit(name_txt, (WIDTH//2 - name_txt.get_width()//2, HEIGHT//2 + 10))

        else:
            ox, oy = 0, 0
            if game.shake > 0:
                shake_int = int(game.shake)
                ox = random.randint(-shake_int, shake_int)
                oy = random.randint(-shake_int, shake_int)
                game.shake -= dt * 0.05

            pygame.draw.rect(screen, BOARD_BG, pygame.Rect(ox, oy, BOARD_SIZE, BOARD_SIZE))
            for i in range(game.grid_size + 1):
                pygame.draw.line(screen, GRID_LINE, (ox + i * cell_size, oy), (ox + i * cell_size, oy + BOARD_SIZE))
                pygame.draw.line(screen, GRID_LINE, (ox, oy + i * cell_size), (ox + BOARD_SIZE, oy + i * cell_size))
            pygame.draw.rect(screen, GRID_LINE, pygame.Rect(ox, oy, BOARD_SIZE, BOARD_SIZE), 2)

            # --- PICAS AR BILDĒM ---
            for p in game.pizzas:
                cx = p[0] * cell_size + cell_size // 2 + ox
                cy = p[1] * cell_size + cell_size // 2 + oy
                img_name = "hot.png" if p[2] == 'hot' else ("cheese.png" if p[2] == 'cheese' else "salami.png")
                img = load_and_scale_image(img_name, cell_size)
                if img:
                    screen.blit(img, img.get_rect(center=(cx, cy)))
                else:
                    color = (230, 57, 70) if p[2] == 'hot' else ((244, 196, 48) if p[2] == 'cheese' else (210, 80, 40))
                    pygame.draw.circle(screen, color, (cx, cy), int(cell_size * 0.42))

            for e in game.effects:
                if 'delay' in e and e['delay'] > 0: continue
                if e['type'] == 'flash':
                    surf = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                    surf.fill((255, 150, 50, int(100 * e['life'])))
                    screen.blit(surf, (ox, oy))
                elif e['type'] == 'shockwave':
                    r = int(e['radius'] * cell_size)
                    if r > 0:
                        surf = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (255, 255, 255, int(255 * e['life'])), (int(e['x']*cell_size+cell_size/2+ox), int(e['y']*cell_size+cell_size/2+oy)), r, width=max(2, int(cell_size * 0.4)))
                        screen.blit(surf, (ox, oy))
                elif e['type'] == 'fire_ring':
                    r = int(e['radius'] * cell_size)
                    if r > 0:
                        surf = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (255, 100, 0, int(255 * e['life'])), (int(e['x']*cell_size+cell_size/2+ox), int(e['y']*cell_size+cell_size/2+oy)), r, width=max(2, int(cell_size * 0.25)))
                        screen.blit(surf, (ox, oy))
                elif e['type'] == 'particle':
                    r = int(e['radius'] * e['life'])
                    if r > 0:
                        surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (*e['color'], int(255 * e['life'])), (r, r), r)
                        screen.blit(surf, (int(e['x'] * cell_size / 20 + ox), int(e['y'] * cell_size / 20 + oy)))
                elif e['type'] == 'pizza_burst':
                    r = int(cell_size * (0.4 + (1.0 - e['life']) * 0.6))
                    if r > 0:
                        surf = pygame.Surface((r*2+8, r*2+8), pygame.SRCALPHA)
                        pygame.draw.circle(surf, (255, 100, 0, int(255 * e['life'])), (r+4, r+4), r+2)
                        pygame.draw.circle(surf, (255, 200, 0, int(255 * e['life'])), (r+4, r+4), r)
                        pygame.draw.circle(surf, (255, 255, 200, int(255 * e['life'])), (r+4, r+4), max(1, r//2))
                        screen.blit(surf, (int(e['x']*cell_size+cell_size/2+ox) - r - 4, int(e['y']*cell_size+cell_size/2+oy) - r - 4))
                elif e['type'] == 'text':
                    txt = font_med.render(e['text'], True, e.get('color', (255, 215, 0)))
                    txt.set_alpha(int(255 * e['life']))
                    screen.blit(txt, txt.get_rect(center=(int(e['x']*cell_size+cell_size/2+ox), int(e['y']*cell_size+cell_size/2+oy - (1.5 - e['life'])*40))))

            t_interp = min(1.0, max(0.0, game.accumulated_time / DIFFICULTIES[game.difficulty_idx]['speed'])) if game.state == "playing" else 1.0
            draw_snake(screen, game, cell_size, t_interp, ox, oy)

            # --- PANELIS ---
            pygame.draw.rect(screen, PANEL_BG, pygame.Rect(BOARD_SIZE, 0, PANEL_WIDTH, HEIGHT))
            y = 20
            title = font_big.render("PIZZA SNAKE", True, ACCENT)
            screen.blit(title, (BOARD_SIZE + PANEL_WIDTH // 2 - title.get_width() // 2, y))
            y += 55

            stats = [("Punkti", str(game.score)), ("Garums", str(len(game.snake))), ("Rekords", str(max(game.highscore, game.score)))]
            for label, val in stats:
                pygame.draw.rect(screen, (30, 30, 55), (BOARD_SIZE + 15, y, PANEL_WIDTH - 30, 36), border_radius=6)
                pygame.draw.rect(screen, ACCENT, (BOARD_SIZE + 15, y, 3, 36))
                screen.blit(font.render(label, True, TEXT_DIM), (BOARD_SIZE + 28, y + 9))
                v_surf = font_med.render(val, True, ACCENT)
                screen.blit(v_surf, (BOARD_SIZE + PANEL_WIDTH - 25 - v_surf.get_width(), y + 7))
                y += 46

            y += 10
            screen.blit(font_sm.render("LĪMENIS", True, TEXT_DIM), (BOARD_SIZE + 15, y))
            y += 22
            bw = (PANEL_WIDTH - 40) // 3
            for i, d in enumerate(DIFFICULTIES):
                rect = pygame.Rect(BOARD_SIZE + 15 + i * (bw + 5), y, bw, 34)
                draw_button(screen, rect, d['name'], game.difficulty_idx == i, rect.collidepoint(mouse_pos), font, buttons, f'diff_{i}')
            y += 50

            screen.blit(font_sm.render("PICAS UZ GRĪDAS", True, TEXT_DIM), (BOARD_SIZE + 15, y))
            y += 22
            draw_value_row(screen, BOARD_SIZE, y, 'pizza_minus', 'pizza_plus', str(game.pizza_count), font_med, buttons, mouse_pos, (244, 196, 48))
            y += 55

            screen.blit(font_sm.render("REŽĢIS (GRID)", True, TEXT_DIM), (BOARD_SIZE + 15, y))
            y += 22
            draw_value_row(screen, BOARD_SIZE, y, 'grid_minus', 'grid_plus', f"{game.grid_size}×{game.grid_size}", font_med, buttons, mouse_pos, ACCENT)
            y += 55

            rad = game.get_explode_radius()
            info = font_sm.render(f"💥 Sprādziens: {rad:.1f} šūnas", True, (255, 150, 80))
            screen.blit(info, (BOARD_SIZE + PANEL_WIDTH // 2 - info.get_width() // 2, y))
            y += 26

            if game.invincible_time > 0:
                inv = font_sm.render(f"🛡 IMUNITĀTE: {game.invincible_time/1000:.1f}s", True, SHIELD_COLOR)
                screen.blit(inv, (BOARD_SIZE + PANEL_WIDTH // 2 - inv.get_width() // 2, y))
            y += 26

            start_rect = pygame.Rect(BOARD_SIZE + 15, y, PANEL_WIDTH - 30, 46)
            hover = start_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (100, 240, 150) if hover else ACCENT, start_rect, border_radius=10)
            btn = font_med.render("START / RESTART", True, BTN_ACTIVE_TEXT)
            screen.blit(btn, (start_rect.centerx - btn.get_width() // 2, start_rect.centery - btn.get_height() // 2))
            buttons['start'] = start_rect
            y += 62

            for h in ["Bultas / WASD — kustība", "SPACE — pauze / sākt", "Salami: +1 garums", "Siera: +2 garums, 25p", "Karstā: sprādziens + IMUNITĀTE"]:
                t_surf = font_sm.render(h, True, TEXT_DIM)
                screen.blit(t_surf, (BOARD_SIZE + PANEL_WIDTH // 2 - t_surf.get_width() // 2, y))
                y += 20

            if game.state == "gameover":
                overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                overlay.fill((10, 10, 25, 210))
                screen.blit(overlay, (0, 0))
                t = font_big.render("GAME OVER", True, (220, 60, 60))
                s = font.render(f"Punkti: {game.score}  |  Rekords: {game.highscore}", True, TEXT_LIGHT)
                s2 = font_sm.render("Spied SPACE lai sāktu no jauna, vai R lai ietu uz izvēlni", True, TEXT_DIM)
                screen.blit(t, (BOARD_SIZE // 2 - t.get_width() // 2, BOARD_SIZE // 2 - 50))
                screen.blit(s, (BOARD_SIZE // 2 - s.get_width() // 2, BOARD_SIZE // 2 + 10))
                screen.blit(s2, (BOARD_SIZE // 2 - s2.get_width() // 2, BOARD_SIZE // 2 + 40))
                
            elif game.state == "paused":
                overlay = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
                overlay.fill((10, 10, 25, 210))
                screen.blit(overlay, (0, 0))
                t = font_big.render("PAUZE", True, ACCENT)
                s = font.render("Nospied SPACE, lai turpinātu", True, TEXT_LIGHT)
                screen.blit(t, (BOARD_SIZE // 2 - t.get_width() // 2, BOARD_SIZE // 2 - 30))
                screen.blit(s, (BOARD_SIZE // 2 - s.get_width() // 2, BOARD_SIZE // 2 + 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()