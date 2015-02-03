import numpy as np

class RM:
    def __init__(self, size=10):
        self.size = size
        self.a = self._create_symm_matrix(self._create_matrix())
        self.ki, self.kj, self.m = self._create_ki_kj(self.a)

    def _create_matrix(self):
        """Creates random matrix with values (0, 1) based on size.

        :return:
        """
        return np.random.randint(0, 2, (self.size, self.size))

    @staticmethod
    def _create_symm_matrix(matrix):
        """Creates symmetrical matrix based on bottom left half of matrix.

        :param matrix:
        :return:
        """
        return np.tril(matrix, -1) + np.tril(matrix, -1).T

    @staticmethod
    def _create_ki_kj(matrix):
        """Returns array of sum across y axis (ki) and x axis (kj) and returning the sum of ki (m).

        :param matrix:
        :return:
        """
        return np.sum(matrix, 1), np.sum(matrix, 0), np.sum(np.sum(matrix, 1))
