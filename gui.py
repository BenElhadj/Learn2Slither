# gui.py

import os
import time
import tkinter as tk
from board import Board
from agent import QLearningAgent
from tkinter import filedialog, messagebox


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

        self.speed = 100
        self.running = False
        self.sessions = sessions
        self.step_mode = False
        self.cell_size = 25
        self.dontlearn = dontlearn
        self.manual_mode = False
        self.length_history = []
        self.current_session = 0
        self.save_model_path = save_model_path
        self.load_model_path = load_model_path
        self.show_spectrum = False
        self._setup_ui(master, board_size)
        self.draw_board()
        self.master.bind("<Key>", self.manual_control)

        # Afficher le message initial
        Mode_text = f"\n- {self.sessions} sessions {self.mode}."
        self.update_status_label(
            f"Mode: {self.mode}\nAppuyez sur start pour démarrer:{Mode_text}"
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
        self.status_label.bind(
            "<Button-1>", lambda event: self.open_settings_window()
        )

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
        self.start_button = tk.Button(
            self.control_frame, text="-", command=self.decrease_speed
        )
        self.start_button.grid(row=0, column=0, padx=3, pady=10)

        self.start_button = tk.Button(
            self.control_frame, text="Start", command=self.start_training
        )
        self.start_button.grid(row=0, column=1, padx=0, pady=10)

        self.start_button = tk.Button(
            self.control_frame, text="+", command=self.increase_speed
        )
        self.start_button.grid(row=0, column=2, padx=3, pady=10)

        self.pause_button = tk.Button(
            self.control_frame, text="Pause", command=self.pause_training
        )
        self.pause_button.grid(row=0, column=3, padx=5)

        self.step_button = tk.Button(
            self.control_frame, text="Step", command=self.step_training
        )
        self.step_button.grid(row=0, column=4, padx=5)

        self.reset_button = tk.Button(
            self.control_frame, text="Reset", command=self.reset_board
        )
        self.reset_button.grid(row=0, column=5, padx=5)

        self.manual_button = tk.Button(
            self.control_frame, text="Manual", command=self.toggle_manual_mode
        )
        self.manual_button.grid(row=0, column=6, padx=5, pady=10)

        self.show_spectrum_btn = tk.Button(
            self.control_frame,
            text="Spectre OFF",
            command=self.spectrum_display,
        )
        self.show_spectrum_btn.grid(row=0, column=7, padx=5, pady=10)

        # Frame pour les labels (statistiques, Q-values, objets découverts)
        self.labels_frame = tk.Frame(master)
        self.labels_frame.pack(fill=tk.BOTH, expand=True)

        # Label pour les statistiques (à gauche)
        self.stats_label = tk.Label(
            self.labels_frame,
            text="\nStats:\nScore: 0\nSteps: 0\nMax Length: 3\nLength History",
            font=("Arial", 11),
            justify="left",
            cursor="hand2",
        )
        self.stats_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        # Liens d'événement de clic pour Length History
        self.stats_label.bind("<Button-1>", self.show_length_history)

        # Label pour les Q-values (au milieu)
        q_val_txt = "DOWN\t=> S : 0.00\nLEFT\t=> S : 0.00\nRIGHT\t=> S : 0.00"
        self.q_values_label = tk.Label(
            self.labels_frame,
            text=f"Q-values de l'état actuel:\nUP\t=> W : 0.00\n{q_val_txt}",
            font=("Arial", 11),
            justify="left",
        )
        self.q_values_label.grid(row=0, column=1, padx=10, pady=0, sticky="w")

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
        self.objects_discovered_label.grid(
            row=0, column=2, padx=10, pady=5, sticky="w"
        )

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

    def spectrum_display(self):
        self.show_spectrum = not self.show_spectrum
        if self.show_spectrum:
            self.show_spectrum_btn.config(text="Spectre ON ")
        else:
            self.show_spectrum_btn.config(text="Spectre OFF")
        self.draw_board()

    def display_speed(self, message):
        """
        Affiche temporairement un message de vitesse en bas de l'interface.
        """
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
            text=(
                f"GAME OVER!\nSession {self.current_session + 1}/"
                f"{self.sessions}\nScore: {self.board.max_length}"
            ),
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
            mode_txt = f"Mode: {self.mode}\nSession {self.current_session + 1}"
            self.update_status_label(f"{mode_txt}/{self.sessions} est lancée.")
            self.board.reset()
            self.board.steps = 0
            self.running = True
            self.run_game_session()
        else:
            # Afficher le message de fin d'entraînement
            if self.dontlearn:
                dontlearn_txt = "Mode Dontlearn activé.\nAucun modèle"
                self.update_status_label(
                    f"Mode: {self.mode}\n{dontlearn_txt} sauvegardé."
                )
            elif self.save_model_path:
                path_txt = "Apprentissage terminé.\nModèle sauvegardé dans :\n"
                self.update_status_label(
                    f"Mode: {self.mode}\n{path_txt}- {self.save_model_path}"
                )
                self.agent.save_model(self.save_model_path)

    def open_settings_window(self):
        # Créer une nouvelle fenêtre modale
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Paramètres du mode")
        settings_window.geometry("350x300")

        # Variables pour stocker les valeurs modifiables
        self.mode_var = tk.StringVar(value=self.mode)  # Variable pour le mode
        self.sessions_var = tk.IntVar(value=self.sessions)
        self.save_model_path_var = tk.StringVar(
            value=self.save_model_path or ""
        )
        self.load_model_path_var = tk.StringVar(
            value=self.load_model_path or ""
        )
        self.board_size_var = tk.IntVar(value=self.board.size)

        # Ajouter un menu déroulant pour sélectionner le mode
        tk.Label(settings_window, text="Mode:").pack(pady=5)
        mode_menu = tk.OptionMenu(
            settings_window, self.mode_var, "Learning", "Game", "Dontlearn"
        )
        mode_menu.pack()

        # Frame pour contenir les champs dynamiques
        self.settings_frame = tk.Frame(settings_window)
        self.settings_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Fonction pour mettre à jour les champs selon le mode sélectionné
        def update_fields(*args):
            # Effacer les champs précédents
            for widget in self.settings_frame.winfo_children():
                widget.destroy()

            # Afficher les champs en fonction du mode sélectionné
            if self.mode_var.get() == "Learning":
                # Frame pour le chemin de fichier et le bouton "Parcourir"
                file_frame = tk.Frame(self.settings_frame)
                file_frame.pack(pady=5, fill=tk.X)

                tk.Label(file_frame, text="Enregistrer les poids dans:").pack(
                    padx=5
                )
                entry_button_frame = tk.Frame(file_frame)
                entry_button_frame.pack(pady=5)
                tk.Entry(
                    entry_button_frame,
                    textvariable=self.save_model_path_var,
                    width=20,
                ).pack(side=tk.LEFT, padx=5)
                tk.Button(
                    entry_button_frame,
                    text="Parcourir...",
                    command=self.choose_save_path,
                ).pack(side=tk.LEFT)

                # Spinbox pour le nombre de sessions
                tk.Label(
                    self.settings_frame,
                    text="Nombre de sessions d'entraînement:",
                ).pack(pady=5)
                tk.Spinbox(
                    self.settings_frame,
                    from_=1,
                    to=1000,
                    textvariable=self.sessions_var,
                ).pack()

            elif self.mode_var.get() == "Game":
                # Frame pour le chemin de fichier et le bouton "Parcourir"
                file_frame = tk.Frame(self.settings_frame)
                file_frame.pack(pady=5, fill=tk.X)

                tk.Label(file_frame, text="Ouvrir le fichier des poids:").pack(
                    padx=5
                )
                entry_button_frame = tk.Frame(file_frame)
                entry_button_frame.pack(pady=5)
                tk.Entry(
                    entry_button_frame,
                    textvariable=self.load_model_path_var,
                    width=20,
                ).pack(side=tk.LEFT, padx=5)
                tk.Button(
                    entry_button_frame,
                    text="Parcourir...",
                    command=self.choose_load_path,
                ).pack(side=tk.LEFT)

                # Spinbox pour le nombre de sessions
                tk.Label(
                    self.settings_frame, text="Nombre de sessions de jeu:"
                ).pack(pady=5)
                tk.Spinbox(
                    self.settings_frame,
                    from_=1,
                    to=1000,
                    textvariable=self.sessions_var,
                ).pack()

            elif self.mode_var.get() == "Dontlearn":
                # Spinbox pour le nombre de sessions
                tk.Label(
                    self.settings_frame, text="Nombre de sessions de jeu:"
                ).pack(pady=5)
                tk.Spinbox(
                    self.settings_frame,
                    from_=1,
                    to=1000,
                    textvariable=self.sessions_var,
                ).pack()

            # Ajouter un champ pour modifier la taille du plateau
            tk.Label(
                self.settings_frame, text="Taille du plateau (8-100):"
            ).pack(pady=5)
            tk.Spinbox(
                self.settings_frame,
                from_=8,
                to=50,
                textvariable=self.board_size_var,
            ).pack()

        # Lier la mise à jour des champs au changement de mode
        self.mode_var.trace_add("write", update_fields)

        # Appeler update_fields une fois pour afficher les champs initiaux
        update_fields()

        # Bouton pour valider les modifications
        tk.Button(
            settings_window,
            text="Valider",
            command=lambda: self.apply_settings(settings_window),
        ).pack(pady=10)

    def choose_save_path(self):
        # Obtenir le chemin du dossier du projet
        project_dir = os.path.dirname(os.path.abspath(__file__))

        # Ouvrir l'explorateur pour choisir un emplacement de sauvegarde
        file_path = filedialog.asksaveasfilename(
            initialdir=project_dir,
            defaultextension="",
            filetypes=[
                ("Tous les fichiers", "*.*"),
                ("Fichiers JSON", "*.json"),
            ],
            title="Enregistrer les poids dans",
        )
        if file_path:
            self.save_model_path_var.set(file_path)

    def choose_load_path(self):
        # Obtenir le chemin du dossier du projet
        project_dir = os.path.dirname(os.path.abspath(__file__))

        # Ouvrir l'explorateur de fichiers pour choisir un fichier de poids
        file_path = filedialog.askopenfilename(
            initialdir=project_dir,
            filetypes=[
                ("Tous les fichiers", "*.*"),
                ("Fichiers JSON", "*.json"),
            ],
            title="Ouvrir le fichier des poids",
        )
        if file_path:
            self.load_model_path_var.set(file_path)

    def apply_settings(self, settings_window):
        # Valider la taille du plateau
        try:
            new_board_size = int(self.board_size_var.get())
            if new_board_size < 8 or new_board_size > 100:
                raise ValueError(
                    "La taille du plateau doit être entre 8 et 100."
                )
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))
            return

        # reset all
        self.reset_board()
        self.agent.q_table = {}
        self.agent.discovered_objects = {}
        self.agent.wall_obj = ""
        self.agent.board_size = (0, 0)
        self.agent.score_rate = 2e-05
        self.agent.heatmap_rate = -0.5
        self.agent.learning_rate = 0.007
        self.agent.discount_factor = 0.00995
        self.agent.exploration_rate = 0.2
        self.agent.exploration_decay = 0.0999
        self.agent.current_position = (0, 0)
        self.draw_discovered_objects()

        # Mettre à jour les paramètres en fonction des valeurs saisies
        new_mode = self.mode_var.get()
        self.sessions = self.sessions_var.get()
        self.save_model_path = (
            self.save_model_path_var.get()
            if self.save_model_path_var.get()
            else None
        )
        self.load_model_path = (
            self.load_model_path_var.get()
            if self.load_model_path_var.get()
            else None
        )

        # Mettre à jour la taille du plateau si elle a changé
        if new_board_size != self.board.size:
            self.board = Board(size=new_board_size)
            self.cell_size = 25  # Réinitialiser la taille des cellules
            self.canvas.config(
                width=new_board_size * self.cell_size,
                height=new_board_size * self.cell_size,
            )
            self.draw_board()

        # Mettre à jour le mode
        if new_mode != self.mode:
            self.mode = new_mode
            if self.mode == "Dontlearn":
                self.agent.dontlearn()
            elif self.mode == "Game" and self.load_model_path:
                self.agent.load_model(self.load_model_path)
            elif self.mode == "Learning":
                self.agent.dontlearn_enabled = True
        # Mettre à jour le texte du status_label
        self.update_status_label(
            f"Mode: {self.mode}\nAppuyez sur start pour démarrer:\n",
            f"- {self.sessions} sessions {self.mode}."
        )

        # Fermer la fenêtre modale
        settings_window.destroy()

    def run_game_session(self):
        if self.running or self.step_mode:
            state = self.board.get_state()
            action = self.agent.choose_action(str(state), training=True)
            direction_mapping = {
                "UP": (-1, 0),
                "DOWN": (1, 0),
                "LEFT": (0, -1),
                "RIGHT": (0, 1),
            }
            if action in direction_mapping:
                self.board.snake_dir = direction_mapping[action]

            result = self.board.update()
            reward = -1
            if result == "Ate Green Apple":
                reward = 20
            elif result == "Ate Red Apple":
                reward = -10
            elif result == "Hit Snake Body":
                reward = -50
            elif result == "Game Over":
                reward = -100

            self.agent.handle_new_objects(str(state), action, reward)

            if result != "Game Over" and result != "Hit Snake Body":
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

            if result == "Game Over" or result == "Hit Snake Body":
                self.length_history.append(self.board.max_length)
                self.display_game_over()
                self.running = False
                self.current_session += 1
                self.agent.reset_history()
                self.run_training_sessions()
                if self.current_session != self.sessions:
                    time.sleep(2)
                    # time.sleep(0.5)

            elif self.running:
                self.master.after(self.speed, self.run_game_session)

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
        if self.show_spectrum:
            self.draw_position_history()

        if hasattr(self, "speed_message_text"):
            self.speed_message_id = self.canvas.create_text(
                self.board.size * self.cell_size / 2,
                self.board.size * self.cell_size - 20,
                text=self.speed_message_text,
                font=("Arial", 12, "bold"),
                fill="black",
            )

    def draw_position_history(self):
        """Dessine l'historique des positions du serpent sur le canvas."""
        position_history = self.agent.get_position_history()
        for position in position_history:
            x, y = position
            self.canvas.create_oval(
                y * self.cell_size + self.cell_size // 4,
                x * self.cell_size + self.cell_size // 4,
                (y + 1) * self.cell_size - self.cell_size // 4,
                (x + 1) * self.cell_size - self.cell_size // 4,
                fill="gray",
                outline="gray",
                # font=("Arial", 7, "bold"),
            )

    def update_q_values_label(self, state):
        """
        Met à jour le label pour afficher les Q-values pour l'état actuel.
        """
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
            q_values_text += (
                f"{action:<7}\t=> {state_mapping[action]}"
                f" : {q_values[action]:.2f}\n"
            )
        self.q_values_label.config(text=q_values_text)

    def update_action_label(self, action):
        """Met à jour le label pour afficher l'action choisie."""
        self.action_label.config(text=f"Action choisie: {action}")

    def update_stats_label(self):
        stats_text = (
            f"\nStats:\nSteps: {self.board.steps}\n"
            f"Score: {self.board.max_length}\n"
            f"Max Length: {self.board.max_length_reached}\n"
            f"Length History"
        )
        self.stats_label.config(text=stats_text)

    def show_length_history(self, event=None):
        # Créer une nouvelle fenêtre pour afficher l'historique des longueurs
        history_window = tk.Toplevel(self.master)
        history_window.title("Length History")
        # Créer un widget Text pour afficher les longueurs
        history_text = tk.Text(
            history_window, wrap=tk.WORD, width=40, height=20
        )
        history_text.pack(padx=10, pady=10)
        # Ajouter les longueurs à la fenêtre
        for i, length in enumerate(self.length_history, start=1):
            history_text.insert(
                tk.END, f"Session {i}: Max Length = {length}\n"
            )
        # Empêcher l'utilisateur de modifier le texte
        history_text.config(state=tk.DISABLED)

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
        self.agent.reset_history()

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
            if result == "Game Over" or result == "Hit Snake Body":
                self.display_game_over()
                self.manual_mode = False

    def on_close(self):
        if self.dontlearn:
            return
        elif self.save_model_path:
            self.agent.save_model(self.save_model_path)
        self.master.destroy()

    def draw_discovered_objects(self):
        """
        Affiche les objets découverts dans l'interface graphique,
        avec la mention '-Wall' pour le mur.
        """
        if self.mode == "Dontlearn":
            text = "Ne gère pas les objets."
            self.objects_discovered_label.config(
                text=f"Objets découverts:\nMode Dontlearn.\n{text}"
            )
        else:
            discovered_objects = self.agent.discovered_objects
            if discovered_objects:
                objects_text = ""
                obj_text = "Objets découverts:\nboard_size:"
                for obj, reward in discovered_objects.items():
                    if obj == self.agent.wall_obj:
                        objects_text += f"'{obj}': {reward} '-Wall'\n"
                    else:
                        objects_text += f"'{obj}': {reward}\n"
                self.objects_discovered_label.config(
                    text=f"{obj_text} {self.agent.board_size}\n{objects_text}"
                )
            else:
                self.objects_discovered_label.config(
                    text="Objets découverts:\nAucun objet pour l'instant."
                )


class COMMAND_LINE:
    @staticmethod
    def run_command_line_mode(
        sessions,
        save_model=None,
        load_model=None,
        visual=False,
        dontlearn=None,
        board_size=10,
    ):

        board = Board(size=board_size)
        agent = QLearningAgent(actions=["UP", "DOWN", "LEFT", "RIGHT"])
        length_history = []  # Initialiser l'historique des longueurs

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
            text = f"Steps : {steps} | Max Length :"
            print(f"{text} {max_length} | Score : {score}\n")

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
                print(
                    f"  {action:<7} => {state_mapping[action]}",
                    f" : {q_values[action]:.2f}",
                )

        def display_objects_discovered():
            discovered = agent.discovered_objects
            print(f"\nObjets découverts :\nboard_size: {agent.board_size}")
            if dontlearn:
                print("  Mode Dontlearn activé. Ne gère pas les objets.")
            elif discovered:
                # Convertir les objets découverts en liste (objet, récompense)
                items = list(discovered.items())
                # Afficher les objets en 3 colonnes
                for i in range(0, len(items), 3):
                    line = items[i: i + 3]
                    formatted_line = " | ".join(
                        (
                            f"{obj:2}-Wall ==> {reward:3}"
                            if obj == agent.wall_obj
                            else f"{obj:7} ==> {reward:4}"
                        )
                        for obj, reward in line
                        if isinstance(obj, str)
                        and isinstance(reward, (int, float))
                    )
                    print(formatted_line)
            else:
                print("  Aucun objet découvert pour l'instant.")

        def display_length_history(length_history):
            print("\nLength History:")
            for i in range(0, len(length_history), 2):
                line = length_history[i: i + 2]
                formatted_line = " | ".join(
                    f"Length session {i + j + 1:4} ==> {length:3}"
                    for j, length in enumerate(line)
                )
                print(formatted_line)

        length_history = []  # Initialiser l'historique des longueurs

        for session in range(1, sessions + 1):
            board.reset()
            agent.reset_history()
            board.steps = 0
            print(f"Session {session}/{sessions} en cours...")
            while True:
                clear_screen()
                display_session_info(
                    session,
                    board.steps,
                    board.max_length_reached,
                    board.max_length,
                )
                display_board()

                # Choisir une action et mettre à jour l'état
                state = board.get_state()
                action = agent.choose_action(
                    str(state), training=not dontlearn
                )
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
                    "Hit Snake Body": -50,
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

                if result == "Game Over" or result == "Hit Snake Body":
                    length_history.append(board.max_length)
                    print(
                        f"\nGame Over!   ==> {session} Session terminée avec",
                        f"un score: {board.max_length}\n",
                        end="",
                    )
                    display_length_history(length_history)
                    if session != sessions:
                        time.sleep(2)
                        # time.sleep(0.5)

                    break
                else:
                    board.steps += 1

        if save_model:
            if dontlearn:
                print("\nMode Dontlearn activé. Aucun modèle sauvegardé.")
            else:
                agent.save_model(save_model)
                print(f"\nModèle sauvegardé dans : {save_model}")
