# main.py
import argparse
from gui import SnakeGUI
from cli import COMMAND_LINE


def main():
    parser = argparse.ArgumentParser(
        description="Train or test a Snake AI using Q-learning."
    )
    parser.add_argument(
        "-visual", action="store_true", help="Run graphical mode"
    )
    parser.add_argument(
        "-sessions",
        type=int,
        default=10,
        help="Number of training sessions",
    )
    parser.add_argument(
        "-save", type=str, help="Path to save the trained model"
    )
    parser.add_argument("-load", type=str, help="Path to load a trained model")
    parser.add_argument(
        "-dontlearn",
        action="store_true",
        help="Disable learning for evaluation",
    )
    parser.add_argument(
        "-size",
        type=int,
        default=10,
        help="Size of the board (N x N)",
    )
    parser.add_argument(
        "-green",
        type=int,
        default=2,
        help="Total number of the green appel",
    )
    parser.add_argument(
        "-red",
        type=int,
        default=1,
        help="Total number of the red appel",
    )
    args = parser.parse_args()

    if args.visual:
        import tkinter as tk

        root = tk.Tk()
        root.title("Snake AI Training")
        app = SnakeGUI(
            root,
            board_size=args.size,
            save_model_path=args.save,
            load_model_path=args.load,
            sessions=args.sessions,
            dontlearn=args.dontlearn,
            nb_r_app=args.red,
            nb_g_app=args.green,
        )
        app.board.steps = 0

        def update_stats_label():
            text = f"{app.board.steps}\nMax Length: {app.board.max_length}\n"
            app.stats_label.config(
                text=f"\nStats:\nScore: {app.board.score}\nSteps: {text}"
            )

        def run_game():
            if app.running:
                state = app.board.get_state()
                action = app.agent.choose_action(str(state), training=True)
                direction_mapping = {
                    "UP": (-1, 0),
                    "DOWN": (1, 0),
                    "LEFT": (0, -1),
                    "RIGHT": (0, 1),
                }
                if action in direction_mapping:
                    app.board.snake_dir = direction_mapping[action]
                result = app.board.update()
                if result in ["Ate Green Apple", "Ate Red Apple", "Moved"]:
                    app.board.steps += 1
                update_stats_label()
                if result not in ["Game Over", None]:
                    app.master.after(100, run_game)
                else:
                    app.running = False

        app.start_training = lambda: [
            setattr(app, "running", True),
            run_game(),
        ]
        root.mainloop()
    else:
        COMMAND_LINE.run_command_line_mode(
            sessions=args.sessions,
            save_model=args.save,
            load_model=args.load,
            visual=True,
            board_size=args.size,
            dontlearn=args.dontlearn,
            nb_r_app=args.red,
            nb_g_app=args.green,
        )


if __name__ == "__main__":
    main()
