import tkinter as tk
from tkinter import messagebox
import random
import threading
import time
from collections import deque

class NPuzzle:
    def __init__(self, N, board=None):
        self.N = N
        self.size = int(N ** 0.5)
        self.board = list(range(1, N)) + [0] if board is None else board[:]

    def is_goal_state(self):
        return self.board == list(range(1, self.N)) + [0]

    def heuristic(self):
        distance = 0
        for i in range(self.N):
            if self.board[i] != 0:
                target_x, target_y = divmod(self.board[i] - 1, self.size)
                current_x, current_y = divmod(i, self.size)
                distance += abs(target_x - current_x) + abs(target_y - current_y)
        return distance

    def next_states(self):
        empty_index = self.board.index(0)
        empty_x, empty_y = divmod(empty_index, self.size)
        next_states = []
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in moves:
            nx, ny = empty_x + dx, empty_y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                new_board = self.board[:]
                swap_index = nx * self.size + ny
                new_board[empty_index], new_board[swap_index] = new_board[swap_index], new_board[empty_index]
                next_states.append(NPuzzle(self.N, new_board))

        return next_states

    def is_solvable(self):
        inversions = 0
        for i in range(self.N):
            for j in range(i + 1, self.N):
                if self.board[i] > 0 and self.board[j] > 0 and self.board[i] > self.board[j]:
                    inversions += 1
        return inversions % 2 == 0

    @staticmethod
    def generate_solvable_puzzle(N):
        size = int(N ** 0.5)
        initial_board = list(range(1, N)) + [0]

        while True:
            random.shuffle(initial_board)
            puzzle = NPuzzle(N, initial_board)
            if puzzle.is_solvable():
                return puzzle

class NPuzzleGUI:
    def __init__(self, root, N):
        self.root = root
        self.N = N
        self.npuzzle = NPuzzle.generate_solvable_puzzle(N)
        self.size = int(N ** 0.5)
        self.cell_size = 100
        self.state_counter = 0
        self.solution_found = False
        self.visited = set()
        self.scale = 1.0  # Initial scale for zoom

        self.canvas_frame = tk.Frame(root, bg="#0e0e0e")
        self.canvas_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.reset_button = tk.Button(self.canvas_frame, text="Reset", command=self.reset, font=("Arial", 12), bg="#0078D7", fg="white")
        self.reset_button.pack(pady=(0, 10))

        self.solve_button = tk.Button(self.canvas_frame, text="Solve", command=self.start_solving, font=("Arial", 12), bg="#0078D7", fg="white")
        self.solve_button.pack(pady=(0, 10))

        self.canvas = tk.Canvas(self.canvas_frame, width=self.size * self.cell_size, height=self.size * self.cell_size, bg="#1c1c1c")
        self.canvas.pack()

        # Frame to hold the tree canvas and scrollbars
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.tree_canvas = tk.Canvas(self.tree_frame, width=800, height=800, bg="#1e1e1e", scrollregion=(-2000, 0, 3000, 4000))
        self.tree_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add vertical and horizontal scrollbars
        self.v_scrollbar = tk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree_canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scrollbar = tk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree_canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree_canvas.config(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Bind zoom in (Ctrl+Z) and zoom out (Ctrl+x)
        root.bind("<Control-z>", self.zoom_in)
        root.bind("<Control-x>", self.zoom_out)

        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        for i in range(self.N):
            row, col = divmod(i, self.size)
            value = self.npuzzle.board[i]
            if value != 0:
                x0, y0 = col * self.cell_size, row * self.cell_size
                x1, y1 = x0 + self.cell_size, y0 + self.cell_size
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="#34eb98", outline="#252525")
                self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(value), font=("Arial", 24), fill="#0e0e0e")

    def reset(self):
        self.npuzzle = NPuzzle.generate_solvable_puzzle(self.N)
        self.visited = set()
        self.draw_board()
        self.tree_canvas.delete("all")
        self.state_counter = 0
        self.solution_found = False

    def start_solving(self):
        threading.Thread(target=self.solve_with_timeout).start()

    def solve_with_timeout(self):
        start_time = time.time()
        self.reset()
        self.solve_bfs(self.npuzzle)


    def solve_bfs(self, start_state):
        queue = deque([(start_state, [], 0)])  # (current state, path, depth)
        visited = set()
        visited.add(tuple(start_state.board))

        x_start, y_start = 400, 40  # Root position for the initial state
        node_x, node_y = x_start, y_start

        root_state_str = " ".join(str(x) if x != 0 else " " for x in start_state.board)
        self.tree_canvas.create_text(node_x, node_y, text=root_state_str, font=("Arial", 8), fill="#5A9")
        self.tree_canvas.create_text(node_x, node_y + 15, text=f"Heuristic: {start_state.heuristic()}", font=("Arial", 6), fill="#34eb98")

        while queue:
            state, path, depth = queue.popleft()
            self.npuzzle.board = state.board
            self.root.after(1, self.draw_board)

            if state.is_goal_state():
                self.solution_found = True
                self.display_solution_popup()
                return

            next_states = state.next_states()
            num_next_states = len(next_states)

            for i, next_state in enumerate(next_states):
                state_tuple = tuple(next_state.board)
                if state_tuple not in visited:
                    visited.add(state_tuple)
                    queue.append((next_state, path + [next_state], depth + 1))

                    offset = (i - num_next_states // 2) * 80
                    child_x = node_x + offset
                    child_y = node_y + (depth + 1) * 80

                    heuristic_value = next_state.heuristic()
                    state_str = " ".join(str(x) if x != 0 else " " for x in next_state.board)

                    self.state_counter += 1
                    node = self.tree_canvas.create_text(child_x, child_y, text=state_str, font=("Arial", 8), fill="#5A9")
                    self.tree_canvas.create_text(child_x, child_y + 15, text=f"Heuristic: {heuristic_value}", font=("Arial", 6), fill="#34eb98")
                    self.tree_canvas.create_line(node_x, node_y, child_x, child_y, fill="#34eb98", arrow=tk.LAST)

            node_x, node_y = x_start, y_start + (depth + 1) * 80

    def display_solution_popup(self):
        messagebox.showinfo("Puzzle Solved", "Congratulations! The puzzle is solved!")

    def zoom_in(self, event=None):
        self.scale *= 1.1
        self.apply_zoom()

    def zoom_out(self, event=None):
        self.scale /= 1.1
        self.apply_zoom()

    def apply_zoom(self):
        self.tree_canvas.scale("all", 0, 0, self.scale, self.scale)
        self.tree_canvas.config(scrollregion=self.tree_canvas.bbox("all"))

def main():
    root = tk.Tk()
    root.title("n-Puzzle Solver with Futuristic Interface")
    root.configure(bg="#0e0e0e")
    app = NPuzzleGUI(root, 9)
    root.mainloop()

if __name__ == "__main__":
    main()   
