# agent.py
import random
import json
import ast

class QLearningAgent:
    def __init__(self, actions, board_size=10, learning_rate=0.3, discount_factor=0.995, exploration_rate=1.0, exploration_decay=0.99, verbose=False):
        self.actions = actions
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.q_table = {}
        self.discovered_objects = {}
        self.verbose = verbose
        self.board_size = board_size
        self.visited_cells = set()
        self.steps = 0

    def choose_action(self, state, training=True):
        objects = ast.literal_eval(state)
        unknown_objects = [obj for obj in objects if obj not in self.discovered_objects]

        if unknown_objects:
            chosen_object = random.choice(unknown_objects)
            action_index = objects.index(chosen_object)
            self.steps += 1  # Incrémentation du compteur
            return self.actions[action_index]

        known_rewards = [self.discovered_objects[obj] for obj in objects]
        max_reward = max(known_rewards)
        best_actions = [self.actions[i] for i, reward in enumerate(known_rewards) if reward == max_reward]

        self.steps += 1  # Incrémentation du compteur
        return random.choice(best_actions)


    def learn(self, state, action, reward, next_state):
        obj = ast.literal_eval(state)[self.actions.index(action)]
        self.discovered_objects[obj] = max(self.discovered_objects.get(obj, float('-inf')), reward)

        q_values = self.q_table.setdefault(state, {action: 0 for action in self.actions})
        next_q_values = self.q_table.get(next_state, {action: 0 for action in self.actions})
        best_next_action = max(next_q_values, key=next_q_values.get)
        td_target = reward + self.discount_factor * next_q_values[best_next_action]
        td_error = td_target - q_values[action]
        q_values[action] += self.learning_rate * td_error

    def handle_new_objects(self, state, action, reward):
        obj = ast.literal_eval(state)[self.actions.index(action)]
        if obj not in self.discovered_objects:
            self.discovered_objects[obj] = reward
            if self.verbose:
                print(f"Nouveau objet découvert : {obj} avec récompense {reward}.")
        elif reward < self.discovered_objects[obj]:
            self.discovered_objects[obj] = reward
            if self.verbose:
                print(f"Récompense mise à jour pour l'objet {obj} : {reward}.")

    def avoid_loops(self, head_position):
        self.visited_cells.add(head_position)
        if len(self.visited_cells) == self.board_size * self.board_size:
            self.visited_cells.clear()
        return head_position in self.visited_cells

    def save_model(self, filepath):
        with open(filepath, 'w') as f:
            json.dump({"q_table": self.q_table, "discovered_objects": self.discovered_objects}, f)

    def load_model(self, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.q_table = data.get("q_table", {})
            self.discovered_objects = data.get("discovered_objects", {})

    def decay_exploration(self, min_rate=0.01):
        self.exploration_rate = max(min_rate, self.exploration_rate * self.exploration_decay)

    def display_discovered_objects(self):
        print("Objets découverts :")
        for obj, reward in self.discovered_objects.items():
            print(f"  {obj}: {reward}")

    def get_q_values(self, state):
        return self.q_table.get(state, {action: 0 for action in self.actions})


