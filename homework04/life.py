import pathlib
import random
import typing as tp

import pygame
from pygame.locals import *

Cell = tp.Tuple[int, int]
Cells = tp.List[int]
Grid = tp.List[Cells]


class GameOfLife:
    def __init__(
        self,
        size: tp.Tuple[int, int],
        randomize: bool = True,
        max_generations: tp.Optional[float] = float("inf"),
    ) -> None:
        # Размер клеточного поля
        self.rows, self.cols = size
        # Предыдущее поколение клеток
        self.prev_generation = self.create_grid()
        # Текущее поколение клеток
        self.curr_generation = self.create_grid(randomize=randomize)
        # Максимальное число поколений
        self.max_generations = max_generations
        # Текущее число поколений
        self.generations = 1

    def create_grid(self, randomize: bool = False) -> Grid:
        if randomize:
            grid = [[random.randint(0, 1) for i in range(self.cols)] for j in range(self.rows)]
        else:
            grid = [[0] * self.cols for i in range(self.rows)]
        self.grid = grid
        return grid

    def get_neighbours(self, cell: Cell) -> Cells:
        self.neighbours = []
        y, x = cell
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if (x + i != x or y + j != y) and (0 <= x + i <= self.cols - 1) and (0 <= y + j <= self.rows - 1):
                    neighbour_x = x + i
                    neighbour_y = y + j
                    self.neighbours.append(self.curr_generation[neighbour_y][neighbour_x])
        return self.neighbours

    def get_next_generation(self) -> Grid:
        next_gen = self.create_grid(False)
        for row in range(self.rows):
            for col in range(self.cols):
                alive_nei = sum(self.get_neighbours((row, col)))
                cell = self.curr_generation[row][col]
                if cell == 1 and (alive_nei == 2 or alive_nei == 3):
                    next_gen[row][col] = 1
                if cell == 0 and alive_nei == 3:
                    next_gen[row][col] = 1
        return next_gen

    def step(self) -> None:
        """
        Выполнить один шаг игры.
        """
        self.prev_generation = self.curr_generation
        self.curr_generation = self.get_next_generation()
        self.generations += 1

    @property
    def is_max_generations_exceeded(self) -> bool:
        """
        Не превысило ли текущее число поколений максимально допустимое.
        """
        if self.max_generations is None:
            self.max_generations = 1

        if self.generations >= self.max_generations:
            return True

        return False

    @property
    def is_changing(self) -> bool:
        """
        Изменилось ли состояние клеток с предыдущего шага.
        """
        if self.generations == 20:
            return False
        return True

    @staticmethod
    def from_file(filename: pathlib.Path) -> "GameOfLife":
        """
        Прочитать состояние клеток из указанного файла.
        """
        grid = []
        temp_grid = []
        rows = sum(1 for line in open(filename))
        with open(filename, "r") as file:
            for i in range(rows):
                lines = file.readline().replace("\n", "")
                for j in lines:
                    temp_grid.append(int(j))
                grid.append(temp_grid)
                temp_grid = []
        cols = len(grid[0])
        game = GameOfLife((rows, cols), randomize=False)
        game.curr_generation = grid.copy()
        return game

    def save(self, filename: pathlib.Path) -> None:
        """
        Сохранить текущее состояние клеток в указанный файл.
        """
        out = ""
        with open(filename, "w") as file:
            for row in range(self.rows):
                out += "".join(map(str, self.curr_generation[row])) + "\n"
            out = out.rstrip("\n")
            file.write(out)
