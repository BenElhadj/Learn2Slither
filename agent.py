# agent.py
import random
import json
import ast

class QLearningAgent:
    def __init__(
        self,
        actions,
        score_rate=2e-05,#0.00002,
        heatmap_rate=-0.5,
        learning_rate=0.007,
        discount_factor=0.00995,
        min_exploration=0.01,
        exploration_rate=0.2,
        exploration_decay=0.0999,
        verbose=False,
    ):
        self.actions = actions
        self.score_rate = score_rate
        self.heatmap_rate = heatmap_rate
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.min_exploration = min_exploration
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.q_table = {}
        self.discovered_objects = {}
        self.verbose = verbose
        self.steps = 0
        self.dontlearn_enabled = True
        self.position_history = []
        self.current_position = (0, 0)
        self.history_length = 3
        self.board_size = (0, 0)
        
        self.wall_obj = ""
        self.wall_up = False
        self.wall_left = False
        self.max_x, self.max_y = self.board_size
        self.locked_x = 0
        self.locked_y = 0
        self.mini_size = (7, 7)


    def dontlearn(self):
        """Désactive l'apprentissage et force l'agent à jouer de manière aléatoire."""
        self.dontlearn_enabled = False
        self.exploration_rate = 1.0


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

        # Enregistrer la nouvelle position dans l'historique
        self.current_position = (x, y)
        self.position_history.append(self.current_position)

        # Garder uniquement les `history_length` dernières positions
        if len(self.position_history) > self.history_length:
            self.position_history.pop(0)

        # Détecter les murs et déduire la taille du plateau
        self.detect_board(state)
        # Ajuster les positions si elles dépassent les limites du plateau
        self.adjust_positions(state)
        

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


    def detect_board(self, state):
        """Détecte les murs et déduit la taille du plateau."""
            
        if self.board_size[0] > self.mini_size[0] and self.board_size[1] > self.mini_size[1]:
            return

        self.detect_walls(state)
        
        if self.wall_obj is None:
            return

        objects = ast.literal_eval(state)
        obj_up, obj_down, obj_left, obj_right = objects[:4]

        # Détecter les murs en haut
        if obj_up == self.wall_obj:
            self.current_position = (1, self.current_position[1])
            self.wall_up = True
        if obj_up != self.wall_obj and self.current_position[0] <= 0:
            self.current_position = (1, self.current_position[1])

        # Détecter les murs à gauche
        if obj_left == self.wall_obj:
            self.current_position = (self.current_position[0], 1)
            self.wall_left = True
        if obj_left != self.wall_obj and self.current_position[1] < 0:
            self.current_position = (self.current_position[0], 1)

        # Détecter les murs en bas et calcul des dimensions x du plateau
        if self.locked_x < 3 and obj_down == self.wall_obj and self.wall_up:
            if self.current_position[0] + 1 > self.mini_size[0]:
                if self.max_x == self.current_position[0] + 1:
                    self.locked_x += 1
                self.max_x = self.current_position[0] + 1
                self.wall_up = False
        elif self.locked_x >= 3 and obj_down == self.wall_obj:
            self.current_position = (self.max_x -2, self.current_position[1])
            
        # Détecter les murs à droite et calcul des dimensions y du plateau
        if  self.locked_y < 3 and obj_right == self.wall_obj and self.wall_left:
            if self.current_position[1] + 1 > self.mini_size[1]:     
                if self.max_y == self.current_position[1] + 1:
                    self.locked_y += 1
                self.max_y = self.current_position[1] + 1
                self.wall_left = False
        elif self.locked_y >= 3 and obj_right == self.wall_obj:
            self.current_position = (self.current_position[0], self.max_y -2)

        if self.locked_x >= 3 and self.max_x > 0 and self.board_size[0] != self.max_x:
            self.board_size = (self.max_x, self.board_size[1])

        if self.locked_y >= 3 and self.max_y > 0 and self.board_size[1] != self.max_y:
            self.board_size = (self.board_size[0], self.max_y)


    def adjust_positions(self, state):
        """Ajuste les positions du serpent après stabilisation du plateau et recentre le spectre définitivement."""

        # Si la taille du plateau n'est pas encore stabilisée, ne rien faire
        if self.board_size[0] <= self.mini_size[0] or self.board_size[1] <= self.mini_size[1]:
            return  

        max_x, max_y = self.board_size
        objects = ast.literal_eval(state)
        obj_up, obj_down, obj_left, obj_right = objects[:4]

        # Vérification et ajustement de `current_position` 
        new_x, new_y = self.current_position  # Initialiser les nouvelles coordonnées

        if obj_up == self.wall_obj:
            new_x = 1  # Fixer la limite haute définitive
        elif self.current_position[0] < 1:  
            new_x = 0  # Empêcher tout décalage vers le négatif après stabilisation

        if obj_left == self.wall_obj:
            new_y = 1  # Fixer la limite gauche définitive
        elif self.current_position[1] < 1:  
            new_y = 0  # Empêcher tout décalage vers le négatif après stabilisation

        if obj_down == self.wall_obj:
            new_x = max_x - 2  # Fixer la limite basse définitive
        elif self.current_position[0] > max_x - 2:  
            new_x = max_x - 1

        if obj_right == self.wall_obj:
            new_y = max_y - 2  # Fixer la limite droite définitive
        elif self.current_position[1] > max_x - 2:  
            new_y = max_y - 1

        # Calcul du décalage unique
        dx, dy = new_x - self.current_position[0], new_y - self.current_position[1]

        if dx != 0 or dy != 0:
            # Appliquer le décalage unique à tout l'historique du spectre
            self.position_history = [(x + dx, y + dy) for x, y in self.position_history]

        # Mise à jour finale de `current_position`
        self.current_position = (new_x, new_y)

        # Assurer que tout reste dans les limites
        self.position_history = [
            (max(0, min(x, max_x - 1)), max(0, min(y, max_y - 1)))
            for x, y in self.position_history
        ]
        self.current_position = (
            max(0, min(self.current_position[0], max_x - 1)),
            max(0, min(self.current_position[1], max_y - 1))
        )


    def adjust_history_length(self, reward):
        # print(f"self.history_length ===> {self.history_length}")
        """Ajuste la longueur de l'historique en fonction de la récompense."""
        if reward > 0:
            # Augmenter la longueur de l'historique de 1 en cas de récompense positive
            self.history_length += 1
        elif reward < -1:
            # Diminuer la longueur de l'historique de 1 en cas de récompense négative supérieure à -1
            self.history_length = max(0, self.history_length - 1)
            del self.position_history[0]      


    def reset_history(self):
        """Réinitialise l'historique des positions et sa longueur."""
        self.position_history = []
        self.history_length = 3  # Réinitialiser la longueur de l'historique à 3
        self.wall_up = False
        self.wall_left = False


    def learn(self, state, action, reward, next_state):
        if not self.dontlearn_enabled:
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
        q_values[action] += self.learning_rate * td_error * (1 - self.exploration_rate)

        self.adjust_history_length(reward)


    def handle_new_objects(self, state, action, reward):
        if not self.dontlearn_enabled:
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
                    "wall_obj": self.wall_obj, # Sauvegarder l'objet mur
                    "board_size": self.board_size,  # Sauvegarder la taille du plateau
                    "score_rate": self.score_rate,
                    "heatmap_rate": self.heatmap_rate,
                    "learning_rate": self.learning_rate,
                    "discount_factor": self.discount_factor,
                    "exploration_rate": self.exploration_rate,
                    "exploration_decay": self.exploration_decay,
                },
                f,
            )


    def load_model(self, filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            self.q_table = data.get("q_table", {})
            self.discovered_objects = data.get("discovered_objects", {})
            self.wall_obj = data.get("wall_obj", '')  # Charger l'objet mur
            self.board_size = (data.get("board_size", (0, 0))[0], data.get("board_size", (0, 0))[1])  # Charger la taille du plateau
            self.score_rate = float(data.get("score_rate", ''))
            self.heatmap_rate = float(data.get("heatmap_rate", ''))
            self.learning_rate = float(data.get("learning_rate", ''))
            self.discount_factor = float(data.get("discount_factor", ''))
            self.exploration_rate = float(data.get("exploration_rate", ''))
            self.exploration_decay = float(data.get("exploration_decay", ''))


    def decay_exploration(self):
        """Diminue progressivement l'exploration pour éviter l'overfitting"""
        self.exploration_rate = max(self.min_exploration, self.exploration_rate * self.exploration_decay)

    def get_q_values(self, state):
        return self.q_table.get(state, {action: 0 for action in self.actions})


    def get_position_history(self):
        """Retourne l'historique des positions du serpent."""
        return self.position_history


    def compute_free_space(self, position):
        """Calcule l'espace libre autour d'une position donnée."""
        queue = [position]
        visited = set(queue)
        count = 0

        while queue:
            x, y = queue.pop(0)
            count += 1
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # UP, DOWN, LEFT, RIGHT
                new_pos = (x + dx, y + dy)
                if (
                    0 <= new_pos[0] < self.board_size[0]
                    and 0 <= new_pos[1] < self.board_size[1]
                    and new_pos not in visited
                    and new_pos not in self.position_history
                    and new_pos != self.wall_obj  # Évite le mur
                ):
                    queue.append(new_pos)
                    visited.add(new_pos)

        return count


    def compute_heatmap(self):
        """Crée une carte de chaleur indiquant les zones les plus visitées"""
        heatmap = {}
        for pos in self.position_history:
            heatmap[pos] = heatmap.get(pos, 0) + 1  # Plus un endroit est visité, plus il est chaud
        return heatmap

      
    def choose_action(self, state, training=True):
        if not self.dontlearn_enabled:
            return random.choice(self.actions)

        objects = ast.literal_eval(state)
        unknown_objects = [obj for obj in objects if obj not in self.discovered_objects]

        if unknown_objects:
            chosen_object = random.choice(unknown_objects)
            action_index = objects.index(chosen_object)
            action = self.actions[action_index]
        else:
            heatmap = self.compute_heatmap()
            best_actions = []
            action_scores = {}

            for i, obj in enumerate(objects):
                x, y = self.current_position
                if self.actions[i] == "UP":
                    x -= 1
                elif self.actions[i] == "DOWN":
                    x += 1
                elif self.actions[i] == "LEFT":
                    y -= 1
                elif self.actions[i] == "RIGHT":
                    y += 1

                # Évaluer l'action selon la récompense et l'espace libre
                reward = self.discovered_objects.get(obj, 0)
                free_space = self.compute_free_space((x, y))

                # Facteur de pénalité si la case a été trop visitée
                visit_penalty = heatmap.get((x, y), 0) * self.learning_rate

                # Score final basé sur la récompense, l'espace libre et la chaleur
                score = reward + free_space * self.score_rate + visit_penalty

                # Ajouter une pénalité si l'action mène à un piège
                if free_space < 2:  # Si l'espace libre est trop faible, pénaliser l'action
                    score -= 50

                action_scores[self.actions[i]] = score
            
            # Sélectionner les actions avec le score maximal
            max_score = max(action_scores.values())
            best_actions = [action for action, score in action_scores.items() if score == max_score]

            action = random.choice(best_actions)

        self.update_position(action, state)
        return action
