# gui.py

import os
import time
from board import Board
from agent import QLearningAgent


class COMMAND_LINE:
    @staticmethod
    def run_command_line_mode(
        sessions,
        save_model=None,
        load_model=None,
        visual=False,
        dontlearn=None,
        board_size=10,
        total_red_apples=1,
        total_green_apples=2,
    ):

        board = Board(size=board_size, total_red_apples=total_red_apples ,total_green_apples=total_green_apples)
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
                    elif (i, j) in board.red_apples:
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
