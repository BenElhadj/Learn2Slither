# gui.py
import tkinter as tk
from board import Board
from agent import QLearningAgent

class SnakeGUI:
    def __init__(self, master, board_size=10, save_model_path=None, load_model_path=None, sessions=1, dontlearn=None):
        self.master = master
        self.master.title("Entraînement Snake AI")
        self.board = Board(size=board_size, initial_score=1000)
        self.agent = QLearningAgent(actions=["UP", "DOWN", "LEFT", "RIGHT"], verbose=False)
        if load_model_path:
            self.agent.load_model(load_model_path)        
        if dontlearn:
            self.agent.dontlearn()

        self.running = False
        self.step_mode = False
        self.manual_mode = False
        self.save_model_path = save_model_path
        
        self.sessions = sessions
        self.dontlearn = dontlearn
        self.current_session = 0
        self.cell_size = 25
        self._setup_ui(master, board_size)
        self.draw_board()
        self.master.bind("<Key>", self.manual_control)
        if save_model_path:
            self.update_status_label(f"Appuyez sur start pour démarrer:\n- {self.sessions} sessions d'apprentissage.")

    def _setup_ui(self, master, board_size):

        self.canvas = tk.Canvas(master, width=board_size * self.cell_size, height=board_size * self.cell_size, bg="lightgray")
        self.canvas.pack(padx=5, pady=10)
        self.control_frame = tk.Frame(master)
        self.control_frame.pack()    
        self.start_button = tk.Button(self.control_frame, text="Start", command=self.start_training)
        self.start_button.grid(row=0, column=0, padx=5, pady=10)
        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause_training)
        self.pause_button.grid(row=0, column=1, padx=5)
        self.step_button = tk.Button(self.control_frame, text="Step", command=self.step_training)
        self.step_button.grid(row=0, column=2, padx=5)
        self.reset_button = tk.Button(self.control_frame, text="Reset", command=self.reset_board)
        self.reset_button.grid(row=0, column=3, padx=5)
        self.manual_button = tk.Button(self.control_frame, text="Manual", command=self.toggle_manual_mode)
        self.manual_button.grid(row=0, column=4, padx=5, pady=10)
        
        if self.save_model_path:
            self.status_label = tk.Label(self.master, text="", anchor="w", justify="left", wraplength=400, font=("Arial", 12))
            self.status_label.pack(pady=10, padx=10)
        
        self.stats_label = tk.Label(master, text="\nStats:\nScore: 0\nSteps: 0\nMax Length: 3\n", font=("Arial", 11), justify="left")
        self.stats_label.pack(side="left", padx=20)
        self.objects_discovered_label = tk.Label(master, text="Objets découverts:", font=("Arial", 11), justify="left")
        self.objects_discovered_label.pack(side="left", padx=20)
        
    def update_status_label(self, message):
        """Met à jour le texte du label avec un message unique."""
        self.status_label.config(text=message)  # Met à jour le texte affiché
        self.master.update()  # Rafraîchit l'interface graphique

    def start_training(self):
        self.running = True
        self.step_mode = False
        self.manual_mode = False
        self.current_session = 0

        # Met à jour le label avec le message initial
        self.run_training_sessions()

    def run_training_sessions(self):
        if self.current_session < self.sessions:
            # Afficher la progression de la session en cours
            if self.save_model_path:
                self.update_status_label(f"Session {self.current_session + 1}/{self.sessions} terminée.")
            self.board.reset()
            self.board.steps = 0
            self.running = True
            self.run_game_session()  # Lance une session de jeu
        else:
            # Afficher le message de fin d'entraînement
            if self.save_model_path:
                self.update_status_label(f"Apprentissage terminé.\nModèle sauvegardé dans :\n- {self.save_model_path}")
            if self.save_model_path:
                self.agent.save_model(self.save_model_path)

    def run_game_session(self):
        if self.running or self.step_mode:
            state = self.board.get_state()
            action = self.agent.choose_action(str(state), training=True)
            direction_mapping = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
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

            self.draw_board()
            self.update_stats_label()
            self.draw_discovered_objects()

            if result != "Game Over" and self.running:
                self.master.after(100, self.run_game_session)
            else:
                self.running = False
                self.current_session += 1
                self.run_training_sessions()

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
                    y * self.cell_size, x * self.cell_size,
                    (y + 1) * self.cell_size, (x + 1) * self.cell_size,
                    fill=color, outline="black"
                )

    def update_stats_label(self):
        self.stats_label.config(
            text=f"\nStats:\nScore: {self.board.score}\nSteps: {self.board.steps}\nMax Length: {self.board.max_length}\n"
        )

    def pause_training(self):
        self.running = False

    def step_training(self):
        self.running = False
        self.step_mode = True
        self.run_game()

    def reset_board(self):
        self.board.reset()
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
                self.manual_mode = False

    def run_game(self):
        if self.running or self.step_mode:
            state = self.board.get_state()
            action = self.agent.choose_action(str(state), training=True)
            direction_mapping = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
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

            self.draw_board()
            self.update_stats_label()
            self.draw_discovered_objects()

            if result != "Game Over" and self.running:
                self.master.after(100, self.run_game)
            else:
                self.running = False

    def on_close(self):
        if self.save_model_path:
            self.agent.save_model(self.save_model_path)
        self.master.destroy()

    def draw_discovered_objects(self):
        discovered_objects = self.agent.discovered_objects
        if discovered_objects:
            objects_text = ""
            for obj, reward in discovered_objects.items():
                objects_text += f"{obj}: {reward}\n"
            self.objects_discovered_label.config(text=f"Objets découverts:\n{objects_text}")
        else:
            self.objects_discovered_label.config(text="Aucun objet découvert pour l'instant.")

class COMMAND_LINE:
    @staticmethod
    def run_command_line_mode(sessions, save_model=None, load_model=None, visual=False, dontlearn=None):
        board = Board()
        agent = QLearningAgent(actions=["UP", "DOWN", "LEFT", "RIGHT"])

        if load_model:
            agent.load_model(load_model)
            print(f"Modèle chargé depuis : {load_model}")
        
        if dontlearn:
            agent.dontlearn()
            print(f"Pas de modèle à chargé dans ce mode")

        for session in range(sessions):
            board.reset()
            board.steps = 0
            print(f"\nSession {session + 1}/{sessions} commencée.\n")
            
            while True:
                state = board.get_state()
                q_values = agent.get_q_values(str(state))
                print("\nCarte actuelle :")
                print("w " * (board.size + 2))
                for i in range(board.size):
                    row = ["w"]
                    for j in range(board.size):
                        if (i, j) in board.snake:
                            if (i, j) == board.snake[0]:
                                row.append('H')
                            else:
                                row.append('S')
                        elif (i, j) in board.green_apples:
                            row.append('G')
                        elif (i, j) == board.red_apple:
                            row.append('R')
                        else:
                            row.append('0')
                    row.append("w")
                    print(" ".join(row))
                print("w " * (board.size + 2))
                print("\nQ-values pour l'état actuel:")
                directions = ["UP", "DOWN", "LEFT", "RIGHT"]
                state_mapping = {
                    "UP": state[0],
                    "DOWN": state[1],
                    "LEFT": state[2],
                    "RIGHT": state[3]
                }
                for action in directions:
                    print(f"  {action:<7} => {state_mapping[action]} : {q_values[action]:.2f}")

                action = agent.choose_action(str(state), training=True)
                print(f"\nAction choisie : {action}\n")
                agent.display_discovered_objects()

                direction_mapping = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
                if action in direction_mapping:
                    board.snake_dir = direction_mapping[action]

                result = board.update()
                reward = -1
                if result == "Ate Green Apple":
                    reward = 20
                elif result == "Ate Red Apple":
                    reward = -10
                elif result == "Game Over":
                    reward = -100

                agent.handle_new_objects(str(state), action, reward)

                if result != "Game Over":
                    next_state = board.get_state()
                    agent.learn(str(state), action, reward, str(next_state))
                    agent.decay_exploration()
                    board.steps += 1
                else:
                    break
            print(f"Session terminée. Score: {board.score}, Steps: {board.steps}, Max Length: {board.max_length}")

        if save_model:
            print("Sauvegarde en cours...")
            agent.save_model(save_model)
            print(f"Modèle sauvegardé dans : {save_model}")
