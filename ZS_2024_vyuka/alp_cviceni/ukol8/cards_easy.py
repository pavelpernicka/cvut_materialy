#!/usr/bin/env python3
import numpy as np
import os, sys
import logging
from PIL import Image, ImageDraw

LOGGING_ENABLED = False

if LOGGING_ENABLED:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.CRITICAL)

class Card:
    def __init__(self, repr_string, my_card=False):
        self.is_my = my_card
        self.matrix = np.zeros((0, 0))
        self.position = (None, None)
        self.size = (None, None)
        self._parse_repr_string(repr_string)

    def _parse_repr_string(self, init_string):
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

    def create_repr_string(self):
        rows, cols = self.size
        repr_string = f"{self.position[0]} {self.position[1]} {rows} {cols} " + " ".join(map(str, self.matrix.flatten()))
        return repr_string

    def rotate(self, clockwise=True):
        if clockwise:
            self.matrix = np.rot90(self.matrix, -1)
        else:
            self.matrix = np.rot90(self.matrix, 1)
        self.size = self.matrix.shape


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
        row, col = card.position
        card_rows, card_cols = card.size

        if row + card_rows > self.rows or col + card_cols > self.columns:
            logging.debug("Card does not fit within the game matrix at the specified position.")
            return True

        submatrix = self.game_matrix[row:row + card_rows, col:col + card_cols]
        card_mask = card.matrix >= 0
        overlap_mask = (submatrix != -1) & card_mask
        if np.any(overlap_mask):
            logging.debug("Card overlap detected, not placing the card.")
            return True

        submatrix[card_mask] = card.matrix[card_mask]
        self.game_matrix[row:row + card_rows, col:col + card_cols] = submatrix
        return False

    def refresh_game_matrix(self):
        self.game_matrix[:] = -1
        for card in self.placed_cards:
            self.place_card(card)

    def game_step(self):
        for card in self.available_cards:
            for rotation in range(4):
                for r in range(self.rows - card.size[0] + 1):
                    for c in range(self.columns - card.size[1] + 1):
                        card.position = (r, c)
                        if self._can_place_card(card):
                            self.place_card(card)
                            self.placed_cards.append(card)
                            self.available_cards.remove(card)
                            return card
                card.rotate(clockwise=True)
        return None

    def _can_place_card(self, card):
        row, col = card.position
        card_rows, card_cols = card.size

        if row + card_rows > self.rows or col + card_cols > self.columns:
            return False

        submatrix = self.game_matrix[row:row + card_rows, col:col + card_cols]
        card_mask = card.matrix >= 0
        overlap_mask = (submatrix != -1) & card_mask
        if np.any(overlap_mask):
            return False

        for r in range(row, row + card_rows):
            for c in range(col, col + card_cols):
                if card.matrix[r - row, c - col] > 0:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.columns:
                            if self.game_matrix[nr, nc] != -1:
                                return True
        return False

    def draw_game_matrix(self):
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

        for card in self.placed_cards:
            row, col = card.position
            card_rows, card_cols = card.size
            eps = -2.5
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
        sys.stderr.write("Error: No file path provided.\n")
        sys.exit(1)

    file_path = sys.argv[1]
    if file_path == "-":
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
    game.draw_game_matrix().show()

    played_card = game.game_step()
    if played_card is not None:
        print(played_card.create_repr_string())
        game.draw_game_matrix().show()
    else:
        print("NOSOLUTION")
