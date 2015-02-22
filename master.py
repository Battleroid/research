import numpy as np
from numpy import linalg
import sys

def create_p1(shape, ki, kj):
    a = np.zeros(shape, dtype=np.int)
    for i, row in enumerate(a):
        for j, col in enumerate(row):
            a[i][j] = ki[i] * kj[j]
    return a


def create_p(p1, m):
    shape = p1.shape
    a = np.zeros(shape, dtype=np.float64)
    for i, row in enumerate(a):
        for j, col in enumerate(row):
            try:
                a[i][j] = float(p1[i][j]) / m
            except ZeroDivisionError:
                pass
    return a


def create_g(a, evec):
    g1_order, g2_order = [], []
    g1_arrays, g2_arrays = [], []
    for idx, row in enumerate(a):
        if evec[idx][0] >= 0:
            g1_order.append(idx)
            g1_arrays.append(row)
        else:
            g2_order.append(idx)
            g2_arrays.append(row)
    return g1_order, g1_arrays, g2_order, g2_arrays


def create_g_matrix(order, arrays):
    size = len(order)
    g = np.zeros((size, size), dtype=np.int)
    for i, row in enumerate(g):
        for j, col in enumerate(order):
            g[i][j] = arrays[i][order[j]]
    return g


def create_q(size, b, order, m):
    s = np.matrix(np.zeros(size))
    for i in order:
        s[0,i] = 1
    a = np.dot(np.dot(s, b), s.T)
    a = a * (1. / (2. * m))
    return a.item(0)


def create_b_of_g(b, order):
    n_b = np.zeros((len(order), len(order)))
    for i, row in enumerate(n_b):
        for j, col in enumerate(row):
            n_b[i][j] = b[order[i]][order[j]]
    n_b_of_g = np.zeros((len(order), len(order)))
    for i, row in enumerate(n_b_of_g):
        for j, col in enumerate(row):
            same = 1 if i == j else 0
            n_b_of_g[i][j] = n_b[i][j] - same * (row.sum())
    return n_b_of_g


def main(filename):
    # load file and define basic constants, separate method for csv/npz?
    data = np.load(filename)
    arr = data['arr_0']
    arr_size = arr.shape[0]
    arr_shape = arr.shape
    # create initial B
    ki, kj, m = np.sum(arr, 1), np.sum(arr, 0), np.sum(np.sum(arr, 1))
    p1 = create_p1(arr_shape, ki, kj)
    p = create_p(p1, m)
    b = arr - p
    # eval & evec
    eval, evec = linalg.eigh(b)
    # first master split
    g1_order, g1_arrays, g2_order, g2_arrays = create_g(arr, evec)
    g1, g2 = create_g_matrix(g1_order, g1_arrays), create_g_matrix(g1_order, g1_arrays)
    # create threshold (q)
    q1 = create_q(arr_size, b, g1_order, m)
    q2 = create_q(arr_size, b, g2_order, m)
    # create B of Gs
    b1 = create_b_of_g(b, g1_order)
    b2 = create_b_of_g(b, g2_order)


def check():
    # check if database has info (which means we already have and are working with
    # an existing data set), if it does cancel out
    pass


if __name__ == '__main__':
    if not check():
        main(sys.argv[1])
    else:
        print 'Database already has data.'