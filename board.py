# board.py
import random


class Board:
    def __init__(self, size=10, initial_score=1000):
        self.size = size
        self.grid = [["0" for _ in range(size)] for _ in range(size)]
        self.snake = self.initialize_snake()
        self.green_apples = []
        self.red_apple = None
        self.place_apples()
        self.snake_dir = self.random_or_advantageous_direction()
        self.score = initial_score
        self.steps = 0
        self.max_length = 3
        self.initial_score = initial_score
        self.max_length_reached = 3

    def initialize_snake(self):
        start_x = random.randint(1, self.size - 2)
        start_y = random.randint(1, self.size - 4)
        return [(start_x, start_y + i) for i in range(3)]

    def random_or_advantageous_direction(self):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        advantages = {d: self.evaluate_direction(d) for d in directions}
        if all(value == 0 for value in advantages.values()):
            return random.choice(directions)
        return max(advantages, key=advantages.get)

    def evaluate_direction(self, direction):
        head_x, head_y = self.snake[0]
        dx, dy = direction
        new_head = (head_x + dx, head_y + dy)

        if not (0 <= new_head[0] < self.size and 0 <= new_head[1] < self.size):
            return -100  # Mur
        if new_head in self.snake:
            return -50  # Corps du serpent
        if new_head in self.green_apples:
            return +20  # Pomme verte
        if new_head == self.red_apple:
            return -10  # Pomme rouge
        return 0  # Case vide

    def reset(self):
        self.snake = self.initialize_snake()
        self.snake_dir = self.random_or_advantageous_direction()
        self.score = self.initial_score
        self.steps = 0
        self.max_length = 3
        self.green_apples = []
        self.red_apple = None
        self.place_apples()

    def place_apples(self):
        self.green_apples = [self.random_empty_cell() for _ in range(2)]
        self.red_apple = self.random_empty_cell()

    def random_empty_cell(self):
        while True:
            x, y = random.randint(0, self.size - 1), random.randint(0, self.size - 1)
            if (
                (x, y) not in self.snake
                and (x, y) not in self.green_apples
                and (x, y) != self.red_apple
            ):
                return x, y

    def update(self):
        head_x, head_y = self.snake[0]
        dx, dy = self.snake_dir
        new_head = (head_x + dx, head_y + dy)

        if new_head in self.snake:
            return "Hit Snake Body"
        
        if not (0 <= new_head[0] < self.size and 0 <= new_head[1] < self.size):
            return "Game Over"

        if new_head in self.green_apples:
            self.snake.insert(0, new_head)
            self.green_apples.remove(new_head)
            self.green_apples.append(self.random_empty_cell())
            self.score += 20
            self.max_length = max(self.max_length, len(self.snake))
            self.max_length_reached = max(self.max_length_reached, len(self.snake))
            return "Ate Green Apple"
        elif new_head == self.red_apple:
            self.snake.pop()
            if len(self.snake) == 0:
                return "Game Over"
            self.red_apple = self.random_empty_cell()
            self.score -= 10
            return "Ate Red Apple"
        else:
            self.snake.insert(0, new_head)
            self.snake.pop()
            self.score -= 1
            if self.score <= 0:
                return "Game Over"
            return "Moved"

    def render(self):
        self.grid = [["0" for _ in range(self.size)] for _ in range(self.size)]
        for gx, gy in self.green_apples:
            self.grid[gx][gy] = "G"
        rx, ry = self.red_apple
        self.grid[rx][ry] = "R"
        for i, (x, y) in enumerate(self.snake):
            self.grid[x][y] = "H" if i == 0 else "S"
        for row in self.grid:
            print(" ".join(row))
        print()

    def get_state(self):
        head_x, head_y = self.snake[0]
        state = (
            self.cell_info(head_x - 1, head_y),
            self.cell_info(head_x + 1, head_y),
            self.cell_info(head_x, head_y - 1),
            self.cell_info(head_x, head_y + 1),
        )
        return state

    def cell_info(self, x, y):
        if not (0 <= x < self.size and 0 <= y < self.size):
            return "W"
        if (x, y) in self.snake:
            return "S"
        if (x, y) in self.green_apples:
            return "G"
        if (x, y) == self.red_apple:
            return "R"
        return "0"
