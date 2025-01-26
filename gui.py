# gui.py

import os
import time
import tkinter as tk
from board import Board
from agent import QLearningAgent

class SnakeGUI:
    def __init__(
        self,
        master,
        board_size=10,
        save_model_path=None,
        load_model_path=None,
        dontlearn=None,
        sessions=1,
    ):
        self.master = master
        
        self.master.title("Entraînement Snake AI")
        self.board = Board(size=board_size)
        self.agent = QLearningAgent(
            actions=["UP", "DOWN", "LEFT", "RIGHT"], verbose=False
        )

        # Définir le mode en fonction des arguments
        if dontlearn:
            self.agent.dontlearn()
            self.mode = "Dontlearn"
        elif load_model_path:
            self.agent.load_model(load_model_path)
            self.mode = "Game"
        elif save_model_path:
            self.mode = "Learning"
        else:
            self.mode = "Game"  # Par défaut

        self.sessions = sessions
        self.current_session = 0
        self.running = False
        self.step_mode = False
        self.manual_mode = False
        self.save_model_path = save_model_path
        self.load_model_path = load_model_path
        self.dontlearn = dontlearn
        self.cell_size = 25
        self.speed = 100

        # Initialiser l'interface utilisateur
        self._setup_ui(master, board_size)
        self.draw_board()
        self.master.bind("<Key>", self.manual_control)

        # Afficher le message initial
        self.update_status_label(
            f"Mode: {self.mode}\nAppuyez sur start pour démarrer:\n- {self.sessions} sessions {self.mode}."
        )

    def _setup_ui(self, master, board_size):
        # Label pour afficher le mode et les messages
        self.status_label = tk.Label(
            master,
            text="",
            font=("Arial", 12),
            justify="left",
            wraplength=400,
        )
        self.status_label.pack(pady=10, padx=10)
        
        # Canvas pour afficher le plateau de jeu
        self.canvas = tk.Canvas(
            master,
            width=board_size * self.cell_size,
            height=board_size * self.cell_size,
            bg="lightgray",
        )
        self.canvas.pack(padx=5, pady=10)

        # Frame pour les boutons de contrôle
        self.control_frame = tk.Frame(master)
        self.control_frame.pack()

        # Boutons de contrôle
        self.start_button = tk.Button(self.control_frame, text="-", command=self.decrease_speed)
        self.start_button.grid(row=0, column=0, padx=3, pady=10)

        self.start_button = tk.Button(self.control_frame, text="Start", command=self.start_training)
        self.start_button.grid(row=0, column=1, padx=0, pady=10)

        self.start_button = tk.Button(self.control_frame, text="+", command=self.increase_speed)
        self.start_button.grid(row=0, column=2, padx=3, pady=10)

        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause_training)
        self.pause_button.grid(row=0, column=3, padx=5)

        self.step_button = tk.Button(self.control_frame, text="Step", command=self.step_training)
        self.step_button.grid(row=0, column=4, padx=5)

        self.reset_button = tk.Button(self.control_frame, text="Reset", command=self.reset_board)
        self.reset_button.grid(row=0, column=5, padx=5)

        self.manual_button = tk.Button(self.control_frame, text="Manual", command=self.toggle_manual_mode)
        self.manual_button.grid(row=0, column=6, padx=5, pady=10)

        # Frame pour les labels (statistiques, Q-values, objets découverts)
        self.labels_frame = tk.Frame(master)
        self.labels_frame.pack(fill=tk.BOTH, expand=True)

        # Label pour les statistiques (à gauche)
        self.stats_label = tk.Label(
            self.labels_frame,
            text="\nStats:\nScore: 0\nSteps: 0\nMax Length: 3\n",
            font=("Arial", 11),
            justify="left",
        )
        self.stats_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Label pour les Q-values (au milieu)
        self.q_values_label = tk.Label(
            self.labels_frame,
            text="Q-values de l'état actuel:\nUP\t=> W : 0.00\nDOWN\t=> S : 0.00\nLEFT\t=> S : 0.00\nRIGHT\t=> S : 0.00",
            font=("Arial", 11),
            justify="left",
        )
        self.q_values_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Label pour l'action choisie (à droite)
        self.action_label = tk.Label(
            self.labels_frame,
            text="Action choisie: None",
            font=("Arial", 11),
            justify="left",
        )
        self.action_label.grid(row=1, column=1, padx=1, pady=5, sticky="w")

        # Label pour les objets découverts (à droite)
        self.objects_discovered_label = tk.Label(
            self.labels_frame,
            text="Objets découverts:",
            font=("Arial", 11),
            justify="left",
        )
        self.objects_discovered_label.grid(row=0, column=2, padx=10, pady=5, sticky="w")
            
    def increase_speed(self):
        """Augmente la vitesse en diminuant le délai."""
        self.step_mode = False
        self.speed = max(20, self.speed - 20)  # Limite minimale de 10 ms
        self.display_speed(f"Vitesse augmentée:\n{self.speed} ms par étape")

    def decrease_speed(self):
        """Diminue la vitesse en augmentant le délai."""
        self.step_mode = False
        self.speed = min(560, self.speed + 20)  # Limite maximale de 1000 ms
        self.display_speed(f"Vitesse diminuée:\n{self.speed} ms par étape")

    def update_status_label(self, message):
        """Met à jour le texte du label avec un message unique."""
        self.status_label.config(text=message)
        self.master.update()
        
    def display_speed(self, message):
        """Affiche temporairement un message de vitesse en bas de l'interface."""
        # Stocker le texte du message
        self.speed_message_text = message

        # Afficher le message
        if hasattr(self, "speed_message_id") and self.speed_message_id:
            self.canvas.delete(self.speed_message_id)
        self.speed_message_id = self.canvas.create_text(
            self.board.size * self.cell_size / 2,
            self.board.size * self.cell_size - 20,
            text=self.speed_message_text,
            font=("Arial", 12, "bold"),
            fill="black",
        )

        # Planifier la suppression du message après 2 secondes
        self.master.after(2000, self.clear_speed_message)

    def clear_speed_message(self):
        """Supprime le message de vitesse après un délai."""
        if hasattr(self, "speed_message_id") and self.speed_message_id:
            self.canvas.delete(self.speed_message_id)
            self.speed_message_id = None
        if hasattr(self, "speed_message_text"):
            del self.speed_message_text

    def display_game_over(self):
        """Affiche le message 'GAME OVER!' au centre de l'écran."""
        self.canvas.create_text(
            self.board.size * self.cell_size / 2,
            self.board.size * self.cell_size / 2,
            text=f"GAME OVER!\nSession {self.current_session + 1}/{self.sessions}",
            font=("Arial", 24, "bold"),
            fill="red",
        )
        self.canvas.update()

    def start_training(self):
        self.running = True
        self.step_mode = False
        self.manual_mode = False
        if self.current_session == 0:
            self.run_training_sessions()
        else:
            # print("step_mode ==> ", self.step_mode)
            self.run_game_session()

    def run_training_sessions(self):
        if self.current_session < self.sessions:
            # Afficher la progression de la session en cours
            # if self.save_model_path:
            self.update_status_label(
                f"Mode: {self.mode}\nSession {self.current_session + 1}/{self.sessions} est lancée."
            )
            self.board.reset()
            self.board.steps = 0
            self.running = True
            self.run_game_session()
        else:
            # Afficher le message de fin d'entraînement
            if self.dontlearn:
                self.update_status_label(
                    f"Mode: {self.mode}\nMode Dontlearn activé.\nAucun modèle sauvegardé."
                )
            elif self.save_model_path:
                self.update_status_label(
                    f"Mode: {self.mode}\nApprentissage terminé.\nModèle sauvegardé dans :\n- {self.save_model_path}"
                )
                self.agent.save_model(self.save_model_path)

    def run_game_session(self):
        if self.running or self.step_mode:
            state = self.board.get_state()
            action = self.agent.choose_action(str(state), training=True)
            direction_mapping = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1),}
            if action in direction_mapping:
                self.board.snake_dir = direction_mapping[action]

            result = self.board.update()
            reward = -1
            if result == "Ate Green Apple":
                reward = 20
            elif result == "Ate Red Apple":
                reward = -10
            elif result == "Game Over":
                reward = -100

            self.agent.handle_new_objects(str(state), action, reward)

            if result != "Game Over":
                next_state = self.board.get_state()
                self.agent.learn(str(state), action, reward, str(next_state))
                self.agent.decay_exploration()
                self.board.steps += 1

            # Mettre à jour les labels
            self.update_q_values_label(state)
            self.update_action_label(action)
            self.draw_board()
            self.update_stats_label()
            self.draw_discovered_objects()

            if result == "Game Over":
                self.display_game_over()
                self.running = False
                self.current_session += 1
                self.run_training_sessions()
                if self.current_session != self.sessions:
                    time.sleep(0.5)
            elif self.running:
                self.master.after(self.speed, self.run_game_session)
            else:
                self.running = False
                self.current_session += 1
                # self.run_training_sessions()

    def draw_board(self):
        self.canvas.delete("all")
        size = self.board.size
        for x in range(size):
            for y in range(size):
                color = "white"
                if (x, y) in self.board.green_apples:
                    color = "green"
                elif (x, y) == self.board.red_apple:
                    color = "red"
                elif (x, y) in self.board.snake:
                    color = "blue" if (x, y) == self.board.snake[0] else "cyan"
                self.canvas.create_rectangle(
                    y * self.cell_size,
                    x * self.cell_size,
                    (y + 1) * self.cell_size,
                    (x + 1) * self.cell_size,
                    fill=color,
                    outline="black",
                )

        if hasattr(self, "speed_message_text"):
            self.speed_message_id = self.canvas.create_text(
                self.board.size * self.cell_size / 2,
                self.board.size * self.cell_size - 20,
                text=self.speed_message_text,
                font=("Arial", 12, "bold"),
                fill="black",
            )

    def update_q_values_label(self, state):
        """Met à jour le label pour afficher les Q-values pour l'état actuel."""
        q_values = self.agent.get_q_values(str(state))
        directions = ["UP", "DOWN", "LEFT", "RIGHT"]
        state_mapping = {
            "UP": state[0],
            "DOWN": state[1],
            "LEFT": state[2],
            "RIGHT": state[3],
        }
        q_values_text = "Q-values de l'état actuel:\n"
        for action in directions:
            q_values_text += f"{action:<7}\t=> {state_mapping[action]} : {q_values[action]:.2f}\n"
        self.q_values_label.config(text=q_values_text)

    def update_action_label(self, action):
        """Met à jour le label pour afficher l'action choisie."""
        self.action_label.config(text=f"Action choisie: {action}")

    def update_stats_label(self):
        self.stats_label.config(
            text=f"\nStats:\nSteps: {self.board.steps}\nScore: {self.board.max_length}\nMax Length: {self.board.max_length_reached}\n"
        )

    def pause_training(self):
        self.running = False

    def step_training(self):
        self.running = False
        self.step_mode = True
        self.run_game_session()

    def reset_board(self):
        self.current_session = 0
        self.board.reset()
        self.board.steps = 0
        self.running = False
        self.step_mode = False
        self.manual_mode = False
        self.draw_board()
        self.update_stats_label()

    def toggle_manual_mode(self):
        self.manual_mode = not self.manual_mode
        self.running = False

    def manual_control(self, event):
        if not self.manual_mode:
            return
        key_to_direction = {
            "Up": (-1, 0),
            "Down": (1, 0),
            "Left": (0, -1),
            "Right": (0, 1),
        }
        if event.keysym in key_to_direction:
            self.board.snake_dir = key_to_direction[event.keysym]
            result = self.board.update()
            if result in ["Moved", "Ate Green Apple", "Ate Red Apple"]:
                self.board.steps += 1
            self.draw_board()
            self.update_stats_label()
            if result == "Game Over":
                self.display_game_over()
                self.manual_mode = False

    def on_close(self):
        if self.dontlearn:
            return
        elif self.save_model_path:
            self.agent.save_model(self.save_model_path)
        self.master.destroy()

    def draw_discovered_objects(self):
        if self.mode == "Dontlearn":
            self.objects_discovered_label.config(
                text="Objets découverts:\nMode Dontlearn.\nNe gérés pas\nles objets."
            )
        else:
            discovered_objects = self.agent.discovered_objects
            if discovered_objects:
                objects_text = ""
                for obj, reward in discovered_objects.items():
                    objects_text += f"{obj}: {reward}\n"
                self.objects_discovered_label.config(
                    text=f"Objets découverts:\n{objects_text}"
                )
            else:
                self.objects_discovered_label.config(
                    text="Aucun objet découvert pour l'instant."
                )
                
class COMMAND_LINE:
    @staticmethod
    def run_command_line_mode(
        sessions, save_model=None, load_model=None, visual=False, dontlearn=None, board_size=10
    ):

        board = Board(size=board_size)
        agent = QLearningAgent(actions=["UP", "DOWN", "LEFT", "RIGHT"])

        if load_model:
            agent.load_model(load_model)
            print(f"Modèle chargé depuis : {load_model}")
            mode = "Game"
        else:
            mode = "Learning"

        if dontlearn:
            agent.dontlearn()

        # Initialisation : Effacer l'écran
        os.system("cls" if os.name == "nt" else "clear")

        def clear_screen():
            os.system("cls" if os.name == "nt" else "clear")

        def display_session_info(session, steps, max_length, score):
            print(f"Mode : {mode} | Session : {session}/{sessions}")
            print(f"Steps : {steps} | Max Length : {max_length} | Score : {score}\n")

        def display_board():
            print("Carte actuelle :")
            print("w " * (board.size + 2))
            for i in range(board.size):
                row = ["w"]
                for j in range(board.size):
                    if (i, j) in board.snake:
                        row.append("H" if (i, j) == board.snake[0] else "S")
                    elif (i, j) in board.green_apples:
                        row.append("G")
                    elif (i, j) == board.red_apple:
                        row.append("R")
                    else:
                        row.append("0")
                row.append("w")
                print(" ".join(row))
            print("w " * (board.size + 2))

        def display_q_values(state):
            print("\nQ-values pour l'état actuel:")
            q_values = agent.get_q_values(str(state))
            directions = ["UP", "DOWN", "LEFT", "RIGHT"]
            state_mapping = {
                "UP": state[0],
                "DOWN": state[1],
                "LEFT": state[2],
                "RIGHT": state[3],
            }
            for action in directions:
                print(f"  {action:<7} => {state_mapping[action]} : {q_values[action]:.2f}")

        def display_objects_discovered():
            discovered = agent.discovered_objects
            print("\nObjets découverts :")
            if dontlearn:
                print("  Mode Dontlearn activé. Ne gère pas les objets.")
            elif discovered:
                # Convertir les objets découverts en une liste de tuples (objet, récompense)
                items = list(discovered.items())
                # Afficher les objets en 3 colonnes
                for i in range(0, len(items), 3):
                    line = items[i:i+3]
                    formatted_line = " | ".join(f"{obj:2} ==> {reward:5}" for obj, reward in line)
                    print(formatted_line)
            else:
                print("  Aucun objet découvert pour l'instant.")

        for session in range(1, sessions + 1):
            board.reset()
            board.steps = 0
            print(f"Session {session}/{sessions} en cours...")
            while True:
                clear_screen()
                display_session_info(session, board.steps, board.max_length_reached, board.max_length)
                display_board()

                # Choisir une action et mettre à jour l'état
                state = board.get_state()
                action = agent.choose_action(str(state), training=not dontlearn)
                board.snake_dir = {
                    "UP": (-1, 0),
                    "DOWN": (1, 0),
                    "LEFT": (0, -1),
                    "RIGHT": (0, 1),
                }[action]
                result = board.update()

                # Récompenser l'agent
                reward = {
                    "Ate Green Apple": 20,
                    "Ate Red Apple": -10,
                    "Game Over": -100,
                }.get(result, -1)

                if not dontlearn:
                    next_state = board.get_state()
                    agent.learn(str(state), action, reward, str(next_state))
                    agent.decay_exploration()

                # Afficher les Q-values et objets découverts
                display_q_values(state)
                print(f"\nAction choisie : {action}")
                display_objects_discovered()

                if result == "Game Over":
                    print(f"\nGame Over!   ==> {session} Session terminée.", end="")
                    if session != sessions:
                        # time.sleep(2)
                        time.sleep(0.5)
                        
                    break
                else :
                    board.steps += 1

        if save_model:
            if dontlearn:
                print("\nMode Dontlearn activé. Aucun modèle sauvegardé.")
            else:
                agent.save_model(save_model)
                print(f"\nModèle sauvegardé dans : {save_model}")
                