import numpy as np
from numpy import linalg
import sys
import files

class CannotSplit(Exception):
    def __init__(self, message=None):
        if not message:
            message = 'Cannot split, matrix too small.'
        self.message = message

class Part(object):
    def __init__(self, filename, ext, q, shape, a_elems):
        self.filename = filename
        self.ext = ext
        self.q = q
        self.shape = shape
        self.a_elems = a_elems

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

def split(filename, initial=False):
    # load data
    filename, ext = filename.rsplit('.')
    data = np.load(filename + "." + ext)
    # define constants and load A if initial
    # if initial:
    #     A = data['arr_0']
    # else:
    #     A = data['a']
    A = data['a']
    A_SIZE = A.shape[0]
    A_SHAPE = A.shape
    # basics
    ki, kj, m = np.sum(A, 1), np.sum(A, 0), np.sum(np.sum(A, 1))
    # create B if initial, if not, import from archive
    if initial:
        p1 = create_p1(A_SHAPE, ki, kj)
        p = create_p(p1, m)
        B = A - p
    else:
        B = data['b']
    if A_SIZE <= 1:
        raise CannotSplit
    # eval & evec
    eval, evec = linalg.eigh(B)
    # split
    g1_order, g1_arrays, g2_order, g2_arrays = create_g(A, evec)
    g1, g2 = create_g_matrix(g1_order, g1_arrays), create_g_matrix(g2_order, g2_arrays)
    # threshold (q)
    q1 = create_q(A_SIZE, B, g1_order, m)
    q2 = create_q(A_SIZE, B, g2_order, m)
    # B of G
    b1 = create_b_of_g(B, g1_order)
    b2 = create_b_of_g(B, g2_order)
    # a elems
    a1_elems = []
    a2_elems = []
    if initial:
        a1_elems = g1_order
        a2_elems = g2_order
    else:
        original_elems = data['a_elems']
        for i in g1_order:
            a1_elems.append(original_elems[i])
        for i in g2_order:
            a2_elems.append(original_elems[i])
    # save
    if not g1_order or not g2_order:
        raise CannotSplit(message='One group is empty, cannot split.')
    if initial:
        # first entries, so no need to return them and manipulate
        np.savez('g1.npz', a=g1, b=b1, q=q1, a_elems=a1_elems)
        np.savez('g2.npz', a=g2, b=b2, q=q2, a_elems=a2_elems)
        files.File.create(filename='g1', ext=ext, q=q1, shape=g1.shape[0], a_elems=','.join([str(x) for x in a1_elems]))
        files.File.create(filename='g2', ext=ext, q=q2, shape=g2.shape[0], a_elems=','.join([str(x) for x in a2_elems]))
    else:
        # return to manager to set parents
        np.savez(filename + ",1" + "." + ext, a=g1, b=b1, q=q1, a_elems=a1_elems)
        np.savez(filename + ",2" + "." + ext, a=g2, b=b2, q=q2, a_elems=a2_elems)
        return Part(filename + ",1", ext, q1, g1.shape[0], ','.join([str(x) for x in a1_elems])), \
               Part(filename + ",2", ext, q2, g2.shape[0], ','.join([str(x) for x in a2_elems]))

def loadtxt(filename, save=True, stripe=True, blank=False):
    a = []
    f = open(filename, 'r')
    fn = filename.split('.')[0]
    for line in f.readlines():
        line = line.strip()
        elems = [int(i) for i in list(line)]
        a.append(elems)
    b = np.array(a, dtype=np.int)
    np.fill_diagonal(b, 0)
    if blank:
        b = remove_blanks(b)
    if save:
        np.savez('.'.join((fn, 'npz')), a=b)
    else:
        return b

def remove_blanks(mat):
    ids = []
    for idx, row in enumerate(mat):
        if not 1 in row:
            ids.append(idx)
    mat = np.delete(mat, ids, 0)
    mat = np.delete(mat, ids, 1)
    return mat

if __name__ == '__main__':
    filename = sys.argv[1]
    initial = sys.argv[2]
    if not initial or initial != 'true':
        initial = False
    split(filename, initial)
