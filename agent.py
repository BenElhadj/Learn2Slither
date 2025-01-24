# agent.py
import random
import json
import ast


class QLearningAgent:
    def __init__(
        self,
        actions,
        learning_rate=0.7,
        discount_factor=0.995,
        exploration_rate=0.3,
        exploration_decay=0.99,
        verbose=False,
    ):
        self.actions = actions
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.q_table = {}
        self.discovered_objects = {}
        self.verbose = verbose
        self.steps = 0
        self.learning_enabled = True

    def dontlearn(self):
        """Désactive l'apprentissage et force l'agent à jouer de manière aléatoire."""
        self.learning_enabled = False
        self.exploration_rate = 1.0  # Exploration maximale (choix aléatoire)

    def choose_action(self, state, training=True):
        if not self.learning_enabled:
            # Si l'apprentissage est désactivé, jouer de manière aléatoire
            return random.choice(self.actions)
        objects = ast.literal_eval(state)
        unknown_objects = [obj for obj in objects if obj not in self.discovered_objects]

        if unknown_objects:
            chosen_object = random.choice(unknown_objects)
            action_index = objects.index(chosen_object)
            self.steps += 1  # Incrémentation du compteur
            return self.actions[action_index]

        known_rewards = [self.discovered_objects[obj] for obj in objects]
        max_reward = max(known_rewards)
        best_actions = [
            self.actions[i]
            for i, reward in enumerate(known_rewards)
            if reward == max_reward
        ]

        self.steps += 1  # Incrémentation du compteur
        return random.choice(best_actions)

    def learn(self, state, action, reward, next_state):
        if not self.learning_enabled:
            return 
        obj = ast.literal_eval(state)[self.actions.index(action)]
        self.discovered_objects[obj] = max(
            self.discovered_objects.get(obj, float("-inf")), reward
        )

        q_values = self.q_table.setdefault(
            state, {action: 0 for action in self.actions}
        )
        next_q_values = self.q_table.get(
            next_state, {action: 0 for action in self.actions}
        )
        best_next_action = max(next_q_values, key=next_q_values.get)
        td_target = reward + self.discount_factor * next_q_values[best_next_action]
        td_error = td_target - q_values[action]
        q_values[action] += self.learning_rate * td_error

    def handle_new_objects(self, state, action, reward):
        if not self.learning_enabled:
            return  # Ne rien faire en mode Dontlearn
        obj = ast.literal_eval(state)[self.actions.index(action)]
        if obj not in self.discovered_objects:
            self.discovered_objects[obj] = reward
            if self.verbose:
                print(f"Nouveau objet découvert : {obj} avec récompense {reward}.")
        elif reward < self.discovered_objects[obj]:
            self.discovered_objects[obj] = reward
            if self.verbose:
                print(f"Récompense mise à jour pour l'objet {obj} : {reward}.")

    def save_model(self, filepath):
        with open(filepath, "w") as f:
            json.dump(
                {
                    "q_table": self.q_table,
                    "discovered_objects": self.discovered_objects,
                },
                f,
            )

    def load_model(self, filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            self.q_table = data.get("q_table", {})
            self.discovered_objects = data.get("discovered_objects", {})

    def decay_exploration(self, min_rate=0.01):
        self.exploration_rate = max(
            min_rate, self.exploration_rate * self.exploration_decay
        )

    def get_q_values(self, state):
        return self.q_table.get(state, {action: 0 for action in self.actions})