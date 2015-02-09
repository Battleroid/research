import numpy as np
from numpy.linalg import linalg


class RM:
    def __init__(self, size=10):
        self.size = size
        self.a = self._create_symm_matrix(self._create_matrix())
        self.ki, self.kj, self.m = self._create_ki_kj_m(self.a)
        # to assure that a random array is created that has at least 1 in every cell
        while 0 in self.ki:
            self.a = self._create_symm_matrix(self._create_matrix())
            self.ki, self.kj, self.m = self._create_ki_kj_m(self.a)
        self.p1 = self._create_p1()
        self.p = self._create_p()
        self.b = self.a - self.p
        self.eval, self.evec = linalg.eig(self.b)
        self.max_eig_val = self._get_largest_eig_val(self.eval)
        self.max_eig_val_vec = self.evec[self.max_eig_val]

    def _create_matrix(self):
        """Creates random matrix with values (0, 1) based on size.

        :return matrix:
        """
        return np.random.randint(0, 2, (self.size, self.size))

    @staticmethod
    def _create_symm_matrix(matrix):
        """Creates symmetrical matrix based on bottom left half of matrix.

        :param matrix:
        :return matrix:
        """
        return np.tril(matrix, -1) + np.tril(matrix, -1).T

    @staticmethod
    def _create_ki_kj_m(matrix):
        """Returns array of sum across y axis (ki) and x axis (kj) and returning the sum of ki (m).

        :param matrix:
        :return ki, kj, m:
        """
        return np.sum(matrix, 1), np.sum(matrix, 0), np.sum(np.sum(matrix, 1))

    def _create_p1(self):
        """
        Creates p1, which is an intermediate step in creating p. Takes each value from ki, kj and multiples to create two-dimensional array.

        :return matrix:
        """
        a = np.zeros((self.size, self.size), dtype=np.int)
        for i, row in enumerate(a):
            for j, col in enumerate(row):
                a[i][j] = self.ki[i] * self.kj[j]
        return a

    def _create_p(self):
        """
        Divides the values of p1 by m, returns results in two-dimensional array.

        :return matrix:
        """
        a = np.zeros((self.size, self.size), dtype=np.float64)
        for i, row in enumerate(a):
            for j, col in enumerate(row):
                try:
                    a[i][j] = float(self.p1[i][j]) / self.m
                except ZeroDivisionError:
                    pass
        return a

    @staticmethod
    def _get_largest_eig_val(matrix):
        """
        Gets the largest index of largest eigenvalue.

        :param matrix:
        :return integer:
        """
        return matrix.argmax()
