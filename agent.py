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
        self.position_history = []  # Historique des positions du serpent
        self.current_position = (0, 0)  # Position actuelle supposée (initialisée à (0, 0))
        self.history_length = 3  # Longueur initiale de l'historique
        self.board_size = (0, 0)  # Taille du plateau (initialisée à (0, 0))
        self.wall_obj = 0  # Symbole représentant les murs (initialement inconnu)
        self.wall_up = False
        self.wall_left = False
        self.max_x, self.max_y = self.board_size


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
            action = self.actions[action_index]
        else:
            known_rewards = [self.discovered_objects[obj] for obj in objects]
            max_reward = max(known_rewards)
            best_actions = [
                self.actions[i]
                for i, reward in enumerate(known_rewards)
                if reward == max_reward
            ]
            action = random.choice(best_actions)
            self.steps += 1  # Incrémentation du compteur

        # Mettre à jour la position en fonction de l'action choisie
        self.update_position(action, state)
        return action

    def update_position(self, action, state):
        """Met à jour la position actuelle en fonction de l'action choisie."""
        x, y = self.current_position
        if action == "UP":
            x -= 1
        elif action == "DOWN":
            x += 1
        elif action == "LEFT":
            y -= 1
        elif action == "RIGHT":
            y += 1
        print(f"Position actuelle : {self.current_position}")

        # Enregistrer la nouvelle position dans l'historique
        self.current_position = (x, y)
        self.position_history.append(self.current_position)

        # Garder uniquement les `history_length` dernières positions
        if len(self.position_history) > self.history_length:
            self.position_history.pop(0)

        # Détecter les murs et déduire la taille du plateau
        self.detect_board_size(state)

        # Ajuster les positions si elles dépassent les limites du plateau
        self.adjust_positions_to_board_limits()

    def detect_walls(self, state):
        """Détecte les murs et déduit la taille du plateau."""
        objects = ast.literal_eval(state)
        obj_up, _, obj_left, _ = objects[:4]

        # Récupérer les récompenses avec une valeur par défaut
        reward_up = self.discovered_objects.get(obj_up, 0)
        reward_left = self.discovered_objects.get(obj_left, 0)
        reward_wall_obj = self.discovered_objects.get(self.wall_obj, 0)
        
        # Initialiser ou mettre à jour le symbole du mur
        if self.wall_obj is None:
            if reward_up < reward_left:
                self.wall_obj = obj_up
            else:
                self.wall_obj = obj_left
        else:
            if reward_up < reward_wall_obj:
                self.wall_obj = obj_up
            if reward_left < reward_wall_obj:
                self.wall_obj = obj_left
      

    def detect_board_size(self, state):
        """Détecte les murs et déduit la taille du plateau."""
        objects = ast.literal_eval(state)
        obj_up, obj_down, obj_left, obj_right = objects[:4]
        # print(f"objects ======> {objects}")
        # self.max_x, self.max_y = self.board_size
        # print(f"obj_up -------> {obj_up}")
        # print(f"obj_down -----> {obj_down}")
        # print(f"obj_left -----> {obj_left}")
        # print(f"obj_right ----> {obj_right}")

        # Initialiser les variables pour détecter les murs

        
        self.detect_walls(state)
        
        if self.wall_obj is None:
            return

        # Détecter les murs en haut et à gauche
        if obj_up == self.wall_obj:
            if self.current_position[0] < 0:
                self.current_position = (abs(self.current_position[0]) * 2, self.current_position[1])
            self.current_position = (1, self.current_position[1])  # Réinitialiser x à 0
            self.wall_up = True
            # print(f"obj_up    {obj_up} | board_size ==> {self.board_size} | current_position ==> {self.current_position} | self.wall_up ====> {self.wall_up}")

        if obj_left == self.wall_obj:
            if self.current_position[1] < 0:
                self.current_position = (self.current_position[0], abs(self.current_position[1]) * 2)
            # self.current_position = ((self.current_position[0] + 1), 0)  # Réinitialiser y à 0
            self.current_position = (self.current_position[0], 1)
            self.wall_left = True
            # print(f"obj_left  {obj_left} | board_size ==> {self.board_size} | current_position ==> {self.current_position} | self.wall_left ==> {self.wall_left}")

        # Détecter les murs en bas et à droite et calcul des dimensions du plateau
        if obj_down == self.wall_obj and self.wall_up:  # Mur en bas
            self.max_x = self.current_position[0] + 1 if self.current_position[0] + 1 > self.max_x else self.max_x
            # self.board_size = (self.current_position[0] + 1 if self.current_position[0] + 1 > self.board_size[0] else self.board_size[0], self.board_size[1])
            self.wall_up = False
            print(f"obj_down  {obj_down} | board_size ==> {self.board_size} | current_position ==> {self.current_position} | self.wall_up ====> {self.wall_up}")

        if obj_right == self.wall_obj and self.wall_left:  # Mur à droite
            self.max_y = self.current_position[1] + 1 if self.current_position[1] + 1 > self.max_y else self.max_y
            # self.board_size = (self.board_size[0], self.current_position[1] + 1 if self.current_position[1] + 1 > self.board_size[1] else self.board_size[1])
            self.wall_left = False
            print(f"obj_right {obj_right} | board_size ==> {self.board_size} | current_position ==> {self.current_position} | self.wall_left ==> {self.wall_left}")
        # self.board_size = (self.max_x, self.max_y)
        print(f"(self.max_x, self.max_y) ========= {(self.max_x, self.max_y)}")
        self.discovered_objects["Board_Size"] = (self.max_x, self.max_y)


    def adjust_positions_to_board_limits(self):
        """Ajuste les positions si elles dépassent les limites du plateau."""
        if self.board_size == (0, 0):
            return  # La taille du plateau est inconnue

        max_x, max_y = self.board_size
        new_position_history = []
        for (x, y) in self.position_history:
            # Ajuster les coordonnées pour qu'elles restent dans les limites du plateau
            x = max(0, min(x, max_x - 1))
            y = max(0, min(y, max_y - 1))
            new_position_history.append((x, y))

        self.position_history = new_position_history
        self.current_position = (
            max(0, min(self.current_position[0], max_x - 1)),
            max(0, min(self.current_position[1], max_y - 1)),
        )


    def adjust_history_length(self, reward):
        """Ajuste la longueur de l'historique en fonction de la récompense."""
        if reward > 0:
            # Augmenter la longueur de l'historique de 1 en cas de récompense positive
            self.history_length += 1
        elif reward < -1:
            # Diminuer la longueur de l'historique de 1 en cas de récompense négative supérieure à -1
            self.history_length = max(1, self.history_length - 1)

    def reset_history(self):
        """Réinitialise l'historique des positions et sa longueur."""
        self.position_history = []
        self.history_length = 3  # Réinitialiser la longueur de l'historique à 3


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

        # Ajuster la longueur de l'historique en fonction de la récompense
        self.adjust_history_length(reward)

    def handle_new_objects(self, state, action, reward):
        if not self.learning_enabled:
            return  # Ne rien faire en mode Dontlearn

        obj = ast.literal_eval(state)[self.actions.index(action)]
        previous_reward = self.discovered_objects.get(obj, "Inconnu")

        # Ajouter ou mettre à jour l'objet dans discovered_objects
        if obj not in self.discovered_objects or reward < self.discovered_objects[obj]:
            self.discovered_objects[obj] = reward
            if self.verbose:
                print(
                    f"Objet {obj} mis à jour : Ancienne récompense = {previous_reward}, Nouvelle récompense = {reward}"
                )

    def save_model(self, filepath):
        with open(filepath, "w") as f:
            json.dump(
                {
                    "q_table": self.q_table,
                    "discovered_objects": self.discovered_objects,
                    # "position_history": self.position_history,  # Sauvegarder l'historique des positions
                    # "history_length": self.history_length,  # Sauvegarder la longueur de l'historique
                    # "board_size": self.board_size,  # Sauvegarder la taille du plateau
                    "wall_obj": self.wall_obj, # Sauvegarder l'objet mur
                },
                f,
            )

    def load_model(self, filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            self.q_table = data.get("q_table", {})
            self.discovered_objects = data.get("discovered_objects", {})
            # self.position_history = data.get("position_history", [])  # Charger l'historique des positions
            # self.history_length = data.get("history_length", 3)  # Charger la longueur de l'historique
            # self.board_size = data.get("board_size", (0, 0))  # Charger la taille du plateau
            self.wall_obj = data.get("wall_obj", '')  # Charger l'objet mur

    def decay_exploration(self, min_rate=0.01):
        self.exploration_rate = max(
            min_rate, self.exploration_rate * self.exploration_decay
        )

    def get_q_values(self, state):
        return self.q_table.get(state, {action: 0 for action in self.actions})

    def get_position_history(self):
        """Retourne l'historique des positions du serpent."""
        return self.position_history