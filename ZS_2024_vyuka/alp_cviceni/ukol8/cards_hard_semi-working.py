#!/usr/bin/env python3
import numpy as np
import os, sys
import logging
from PIL import Image, ImageDraw

LOGGING_ENABLED = False
SHOW_ENABLED = False

if LOGGING_ENABLED:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.CRITICAL)

class Card:
    def __init__(self, repr_string, my_card=False):
        self.is_my = my_card
        self.matrix = np.zeros((0, 0))    
        self.matrices = []
        self.position = (None, None)
        self.size = (None, None)
        self.rotation = 0
        self._parse_repr_string(repr_string)
        self.precompute_rotations()
        logging.info(self.matrices)

    def _parse_repr_string(self, init_string):
        """
        Parse BRUTE's card representation and update card
        """
        values = list(map(int, init_string.split()))
        if not self.is_my:
            posx, posy = values[0], values[1]
            rows, cols = values[2], values[3]
            self.position = (posx, posy)
            data = values[4:]
        else:
            rows, cols = values[0], values[1]
            data = values[2:]
        self.matrix = np.array(data).reshape((rows, cols))
        self.size = self.matrix.shape
        logging.info(f"Parsed new card: {self.is_my} - {self.size} - {self.position} - {self.create_repr_string()}") 

    def precompute_rotations(self):
        """
        Precompute all four rotations of the card's matrix to save time while trying to find best placement
        """
        base_matrix = self.matrix
        self.matrices = [base_matrix] + [np.rot90(base_matrix, k) for k in range(1, 4)]
        self.matrix = self.matrices[self.rotation]  # Set initial rotation matrix
        self.size = self.matrix.shape

    def create_repr_string(self):
        """
        Convert Card back to BRUTE's representation
        """
        rows, cols = self.size
        repr_string = f"{self.position[0]} {self.position[1]} {rows} {cols} " + " ".join(map(str, self.matrix.flatten()))
        return repr_string

    def rotate(self):
        """
        Update matrix by next rotation from pregenerated
        """
        self.rotation = (self.rotation + 1) % 4
        self.matrix = self.matrices[self.rotation]
        self.size = self.matrix.shape

    def set_best_rotation(self, rotation):
        # Manually set rotation that was evaluated as the best
        self.matrix = self.matrices[rotation]
        self.size = self.matrix.shape

    def __repr__(self):
        return f"Card(my={self.is_my}, size={self.size}, position={self.position}, rotation={self.rotation}, matrix=\n{self.matrix})"

class GameEnvironment:
    def __init__(self, size):
        self.rows = size[0]
        self.columns = size[1]
        self.game_matrix = np.full((self.rows, self.columns), -1)
        self.placed_cards = []
        self.available_cards = []

        self._colors = {
            0: "#ffffff",
            1: "#636940",
            2: "#59A96A",
            3: "#ffdd4a",
            4: "#fe9000",
            -2: "#a3d9ff",
            -1: "#cccccc"
        }

    def place_card(self, card):
        """
        Adds specific card to the given position on game_matrix.
        """
        row, col = card.position
        card_rows, card_cols = card.size

        if row + card_rows > self.rows or col + card_cols > self.columns:
            logging.info("Card does not fit within the game matrix at the specified position.")
            return True

        submatrix = self.game_matrix[row:row + card_rows, col:col + card_cols]

        # check overlaps
        card_mask = card.matrix >= 0
        overlap_mask = (submatrix != -1) & card_mask
        if np.any(overlap_mask):
            logging.info("Card overlap detected, not placing the card.")
            return True

        # place the card
        submatrix[card_mask] = card.matrix[card_mask]
        self.game_matrix[row:row + card_rows, col:col + card_cols] = submatrix
        logging.info(f"Card placed: {card}.")
        return False

    def refresh_game_matrix(self):
        """
        Clear game_matrix and place all placed_cards
        """
        self.game_matrix[:] = -1
        for card in self.placed_cards:
            self.place_card(card)

    def check_touch(self, row, col, card_rows, card_cols):
        """
        Check if card bounds are touching any existing cards at the edges
        """
        touch_positions = [
            (row - 1, col), (row + card_rows, col),  # nahore, dole
            (row, col - 1), (row, col + card_cols)  # vlevo, vpravo
        ]

        for r, c in touch_positions:
            if 0 <= r < self.rows and 0 <= c < self.columns and self.game_matrix[r, c] != -1:
                return True
        return False

    def game_step(self):
        """
        Place the best card from available_cards to position where isthe greatest number of connected components
        """
        def connected_components_size(matrix, start_row, start_col, target_value, visited, placed_mask, debug_path=None):
            """
            Calculate connected component size using flood fill method.
            - only paths outreaching card are taken in account
            """
            def debug_image(matrix, visited, placed_mask, current_cell, step, debug_path):
                rows, cols = matrix.shape
                cell_size = 30
                img = Image.new("RGB", (cols * cell_size, rows * cell_size), "white")
                draw = ImageDraw.Draw(img)

                for r in range(rows):
                    for c in range(cols):
                        x0, y0 = c * cell_size, r * cell_size
                        x1, y1 = x0 + cell_size, y0 + cell_size
                        if (r, c) in visited:
                            fill_color = self._colors[-2] # visited
                        elif placed_mask[r, c]:
                            fill_color = self._colors[3] # new
                        elif matrix[r, c] != -1:
                            fill_color = self._colors[-1] # already existing
                        else:
                            fill_color = self._colors[0] # prazdne
                        draw.rectangle([x0, y0, x1, y1], fill=fill_color, outline="black")
                # zvyrazneni aktualni bunky
                cx0, cy0 = current_cell[1] * cell_size, current_cell[0] * cell_size
                cx1, cy1 = cx0 + cell_size, cy0 + cell_size
                draw.rectangle([cx0, cy0, cx1, cy1], fill="#FF6347", outline="black")
                img.save(f"{debug_path}/flood_fill_step_{step}.png")

            rows, cols = matrix.shape
            stack = [(start_row, start_col)]
            size = 0
            outreaching = False
            component_cells = []

            if debug_path != None:
                os.makedirs(debug_path, exist_ok=True) # aby nebuzeroval
            debug_step = 0

            while stack:
                r, c = stack.pop()
                if (r, c) in visited or r < 0 or r >= rows or c < 0 or c >= cols: # skip if out of region or visited
                    continue
                if matrix[r, c] != target_value:
                    continue

                visited.add((r, c))
                component_cells.append((r, c))
                size += 1

                # check if cell outreaches card
                if not placed_mask[r, c]:  # if not within card mask
                    outreaching = True
                if debug_path != None:
                    debug_image(matrix, visited, placed_mask, (r, c), debug_step, debug_path)
                debug_step += 1
                stack.extend([(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]) # kontrola ostatnich smeru

            logging.info(f"Flood fill at ({start_row}, {start_col}): size={size}, extends_to_existing={outreaching}, cells={component_cells}")
            
            if not outreaching:
                size = 0
            return size 

        best_card = None
        best_score = -1
        best_position = None
        best_rotation = 0
        cnt = 0

        for card in self.available_cards:
            for rotation in range(4):
                # try all rotations
                if rotation > 0:
                    card.rotate()
                card_rows, card_cols = card.size

                for row in range(self.rows - card_rows + 1):
                    for col in range(self.columns - card_cols + 1):
                        card.position = (row, col)

                        # validate placement
                        if row < 0 or col < 0 or row + card_rows > self.rows or col + card_cols > self.columns:
                            continue
                        submatrix = self.game_matrix[row:row + card_rows, col:col + card_cols]
                        card_mask = card.matrix >= 0 # binary mask of current card
                        overlap_mask = (submatrix != -1) & card_mask # True where overlap 
                        
                        if np.any(overlap_mask):
                            continue
                        if not self.check_touch(row, col, card_rows, card_cols):
                            continue

                        # simulate placement (maybe faster?)
                        temp_matrix = self.game_matrix.copy()
                        temp_matrix[row:row + card_rows, col:col + card_cols][card_mask] = card.matrix[card_mask]
                        placed_mask = np.zeros_like(temp_matrix, dtype=bool)
                        placed_mask[row:row + card_rows, col:col + card_cols][card_mask] = True

                        color_scores = {}
                        visited = set()

                        for r in range(card_rows):
                            for c in range(card_cols):
                                if card.matrix[r, c] > 0:  # exclude empty cells
                                    abs_row, abs_col = row + r, col + c
                                    if(abs_row, abs_col) not in visited:
                                        color = card.matrix[r, c]
                                        cnt += 1
                                        if SHOW_ENABLED:
                                            d_path = f"debug/flood_fill_debug_{cnt}"
                                        else:
                                            d_path = None
                                        size = connected_components_size(temp_matrix, abs_row, abs_col, color, visited, placed_mask, debug_path=d_path)
                                        if size > 0:
                                            color_scores[color] = max(color_scores.get(color, 0), size) # sth.get(něco, fallback) je error-proof verze sth[něco]

                        total_score = sum(color_scores.values())
                        logging.info(f"Trying card at position ({row}, {col}) with rotation {card.rotation}.")
                        logging.info(f"Total connected components: {total_score}")

                        if total_score > best_score:
                            best_score = total_score
                            best_card = card
                            best_position = (row, col)
                            best_rotation = card.rotation

        if best_card:
            best_card.position = best_position
            best_card.set_best_rotation(best_rotation) # important, card may be rotated while cecking other possibilities
            self.place_card(best_card)
            self.placed_cards.append(best_card)
            self.available_cards.remove(best_card)
            self.refresh_game_matrix()
            logging.info(f"Best card placed at ({best_position[0]}, {best_position[1]}) with rotation {best_rotation}.")
            logging.info(f"Total connected component score: {best_score}")
            return best_card

        logging.info("No valid moves found. Returning NOSOLUTION.")
        return None

    def draw_game_matrix(self):
        """
        Creates image of current game_matrix state
        """
        _cardOutline = "#CD853F"
        _gridColor = "#ADACB5"
        _originColor2 = "#f8c8dc"
        _cellWidth = 60

        width = _cellWidth * self.columns
        height = _cellWidth * self.rows
        img = Image.new('RGBA', (width, height), "white")
        draw = ImageDraw.Draw(img)

        for row in range(self.rows):
            for col in range(self.columns):
                value = self.game_matrix[row, col]
                color = self._colors.get(value, "#000000")
                cell_top_left = (col * _cellWidth, row * _cellWidth)
                cell_bottom_right = ((col + 1) * _cellWidth, (row + 1) * _cellWidth)
                draw.rectangle([cell_top_left, cell_bottom_right], fill=color)

        for i in range(1, self.rows):
            draw.line([0, i * _cellWidth, width, i * _cellWidth], fill=_gridColor, width=2)
        for i in range(1, self.columns):
            draw.line([i * _cellWidth, 0, i * _cellWidth, height], fill=_gridColor, width=2)

        for id, card in enumerate(self.placed_cards):
            row, col = card.position
            card_rows, card_cols = card.size
            eps = -2.5
            if(id == len(self.placed_cards)-1):
                _cardOutline = "#FF0000"
            draw.rectangle(
                [col * _cellWidth - eps, row * _cellWidth - eps,
                 (col + card_cols) * _cellWidth - 0.5 * eps, (row + card_rows) * _cellWidth - 0.5 * eps],
                outline=_cardOutline, width=3
            )
            eps = _cellWidth / 6
            rc, cc = row * _cellWidth + _cellWidth / 2, col * _cellWidth + _cellWidth / 2
            draw.ellipse(
                [cc - eps, rc - eps, cc + eps, rc + eps],
                fill=_originColor2
            )

        eps = 2
        draw.line([eps, eps, width - eps, eps, width - eps, height - eps, eps, height - eps, eps, eps],
                  fill=_gridColor, width=5)

        return img


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Error: No input file path provided.\n")
        sys.exit(1)

    file_path = sys.argv[1]
    if file_path == "-": # script.py - < sth
        lines = sys.stdin.readlines()
    elif os.path.exists(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
    else:
        sys.stderr.write(f"Error: The file '{file_path}' does not exist.\n")
        sys.exit(1)

    rows, cols = map(int, lines[0].split())
    placed_count, available_count = map(int, lines[1].split())
    game = GameEnvironment((rows, cols))

    for i in range(2, 2 + placed_count):
        game.placed_cards.append(Card(lines[i]))

    for i in range(2 + placed_count, 2 + placed_count + available_count):
        game.available_cards.append(Card(lines[i], my_card=True))

    game.refresh_game_matrix()
    if SHOW_ENABLED:
        game.draw_game_matrix().show()

    played_card = game.game_step()
    if played_card is not None:
        print(played_card.create_repr_string())
        if SHOW_ENABLED:
            game.draw_game_matrix().show()
    else:
        print("NOSOLUTION")
