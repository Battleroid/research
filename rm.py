import numpy as np

class RM:
    def __init__(self, size=10):
        self.size = size
        self.a = self._create_symm_matrix(self._create_matrix())
        self.ki, self.kj, self.m = self._create_ki_kj(self.a)

    def _create_matrix(self):
        return np.random.randint(0, 2, (self.size, self.size))

    def _create_symm_matrix(self, matrix):
        return np.tril(matrix, -1) + np.tril(matrix, -1).T

    def _create_ki_kj(self, matrix):
        return np.sum(matrix, 1), np.sum(matrix, 0), np.sum(np.sum(matrix, 1))
