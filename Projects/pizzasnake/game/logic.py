import random
import math
import json

# Konfigurācija
GRID_OPTIONS = [10, 15, 20, 25, 30]
EXPLOSION_SIZE_FACTOR = 0.15
INPUT_QUEUE_MAX = 3
INVINCIBILITY_MS = 600
HIGHSCORE_FILE = 'snake_highscore.json'

DIFFICULTIES = [
    {'name': 'Viegls', 'speed': 110, 'mult': 1},
    {'name': 'Vidējs', 'speed': 75,  'mult': 2},
    {'name': 'Grūts',  'speed': 50,  'mult': 3},
]

def load_highscore():
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            return json.load(f).get('high', 0)
    except Exception:
        return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump({'high': score}, f)
    except Exception:
        pass

class PizzaSnakeGame:
    def __init__(self):
        self.state = "menu" # menu, playing, paused, gameover
        self.username = ""
        self.highscore = load_highscore()
        
        self.grid_size = 25
        self.pizza_count = 3
        self.difficulty_idx = 1
        
        self.reset_game()

    def reset_game(self):
        self.score = 0
        cx, cy = self.grid_size // 2, self.grid_size // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.prev_snake = self.snake.copy()
        self.direction = (1, 0)
        self.input_queue = []
        self.pizzas = []
        self.effects = []
        self.shake = 0
        self.accumulated_time = 0
        self.invincible_time = 0
        self.game_over = False
        self.paused = False
        self._spawn_pizzas()

    def start(self):
        self.reset_game()
        self.state = "playing"

    def _random_empty_cell(self):
        snake_set = set(self.snake)
        pizza_set = set((p[0], p[1]) for p in self.pizzas)
        for _ in range(500):
            cell = (random.randrange(self.grid_size), random.randrange(self.grid_size))
            if cell not in snake_set and cell not in pizza_set:
                return cell
        return None

    def _spawn_pizzas(self):
        while len(self.pizzas) < self.pizza_count:
            cell = self._random_empty_cell()
            if cell is None: break
            p_type = random.choices(['salami', 'cheese', 'hot'], weights=[15, 3, 1], k=1)[0]
            self.pizzas.append((cell[0], cell[1], p_type))

    def adjust_pizza_count(self, amount):
        self.pizza_count = max(1, min(10, self.pizza_count + amount))
        while len(self.pizzas) > self.pizza_count: self.pizzas.pop()
        self._spawn_pizzas()

    def change_grid_size(self, amount):
        idx = GRID_OPTIONS.index(self.grid_size) if self.grid_size in GRID_OPTIONS else 3
        new_idx = max(0, min(len(GRID_OPTIONS) - 1, idx + amount))
        if new_idx != idx:
            self.grid_size = GRID_OPTIONS[new_idx]
            self.reset_game()

    def change_direction(self, new_dir):
        ref = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir[0] == -ref[0] and new_dir[1] == -ref[1]: return
        if new_dir == ref: return
        if len(self.input_queue) < INPUT_QUEUE_MAX:
            self.input_queue.append(new_dir)

    def get_explode_radius(self):
        return max(1.5, self.grid_size * EXPLOSION_SIZE_FACTOR)

    def update(self, dt):
        if self.state != "playing": return
        
        speed = DIFFICULTIES[self.difficulty_idx]['speed']
        
        if self.invincible_time > 0:
            self.invincible_time -= dt
            
        self.accumulated_time += dt
        while self.accumulated_time >= speed:
            self.accumulated_time -= speed
            self._tick()

    def _tick(self):
        self.prev_snake = self.snake.copy()
        if self.input_queue:
            self.direction = self.input_queue.pop(0)

        dx, dy = self.direction
        hx, hy = self.snake[0]
        new_head = (hx + dx, hy + dy)
        is_invincible = self.invincible_time > 0

        if not (0 <= new_head[0] < self.grid_size and 0 <= new_head[1] < self.grid_size):
            if is_invincible:
                new_head = (max(0, min(self.grid_size - 1, new_head[0])), max(0, min(self.grid_size - 1, new_head[1])))
            else:
                self._end_game()
                return

        pizza_idx = next((i for i, p in enumerate(self.pizzas) if p[0] == new_head[0] and p[1] == new_head[1]), -1)
        ate = pizza_idx != -1
        pizza_type = self.pizzas[pizza_idx][2] if ate else None

        body = self.snake if ate else self.snake[:-1]
        if new_head in body and not is_invincible:
            self._end_game()
            return

        self.snake.insert(0, new_head)

        if ate:
            mult = DIFFICULTIES[self.difficulty_idx]['mult']
            self.pizzas.pop(pizza_idx)
            
            if pizza_type == 'salami':
                self.score += 10 * mult
                self._spawn_pizzas()
            elif pizza_type == 'cheese':
                self.score += 25 * mult
                self.snake.append(self.snake[-1])
                if len(self.prev_snake) < len(self.snake): self.prev_snake.append(self.prev_snake[-1])
                self._spawn_pizzas()
            elif pizza_type == 'hot':
                self.score += 15 * mult
                r = self.get_explode_radius()
                exploded = []
                for p in self.pizzas[:]:
                    if math.hypot(p[0] - new_head[0], p[1] - new_head[1]) <= r:
                        exploded.append(p)
                        self.pizzas.remove(p)
                
                for ep in exploded:
                    self.effects.append({'type': 'pizza_burst', 'x': ep[0], 'y': ep[1], 'life': 1.0})
                
                if exploded:
                    self.score += len(exploded) * 10 * mult
                    self.effects.append({'type': 'text', 'x': new_head[0], 'y': new_head[1], 'text': f"+{len(exploded)*10*mult}", 'life': 1.5})
                
                self.effects.append({'type': 'flash', 'life': 1.0})
                self.effects.append({'type': 'shockwave', 'x': new_head[0], 'y': new_head[1], 'radius': 0.1, 'max_radius': r, 'life': 1.0})
                for i in range(3):
                    self.effects.append({'type': 'fire_ring', 'x': new_head[0], 'y': new_head[1], 'radius': 0.1, 'max_radius': r * (1.0 + i*0.15), 'life': 1.0, 'delay': i * 0.1})
                
                for _ in range(max(30, int(r * 15))):
                    angle = random.uniform(0, math.pi * 2)
                    p_speed = random.uniform(2.0, 6.0) * (1.5 + r * 0.5)
                    self.effects.append({
                        'type': 'particle', 'x': new_head[0] * 20 + 10, 'y': new_head[1] * 20 + 10,
                        'vx': math.cos(angle) * p_speed, 'vy': math.sin(angle) * p_speed,
                        'radius': random.uniform(3, 8), 'life': 1.0,
                        'color': random.choice([(255, 220, 0), (255, 100, 0), (255, 50, 0), (200, 0, 0)])
                    })
                self.invincible_time = INVINCIBILITY_MS
                self.effects.append({'type': 'text', 'x': new_head[0], 'y': new_head[1] - 1, 'text': "IMUNITĀTE!", 'life': 1.5, 'color': (80, 200, 255)})
                self.shake = int(5 + r * 1.5)
                if len(self.pizzas) == 0: self._spawn_pizzas()
                
            self._check_level_up()
        else:
            self.snake.pop()

        for e in self.effects[:]:
            e['life'] -= 0.03
            if 'delay' in e and e['delay'] > 0:
                e['delay'] -= 0.03; continue
            if e['type'] in ('shockwave', 'fire_ring'):
                e['radius'] += 0.4 if e['type'] == 'shockwave' else 0.25
                if e['radius'] > e['max_radius']: e['radius'] = e['max_radius']
            elif e['type'] == 'particle':
                e['x'] += e['vx']; e['y'] += e['vy']; e['vy'] += 0.2; e['vx'] *= 0.98
            if e['life'] <= 0: self.effects.remove(e)

    def _check_level_up(self):
        if self.score >= 200 and self.difficulty_idx == 1:
            self.difficulty_idx = 2
            self.grid_size = 20
            self.reset_game()
        elif self.score >= 500 and self.difficulty_idx == 2:
            self.difficulty_idx = 3
            self.grid_size = 15
            self.reset_game()

    def _end_game(self):
        self.game_over = True
        self.state = "gameover"
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)