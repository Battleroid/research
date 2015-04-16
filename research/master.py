import numpy as np
from numpy import linalg
import sys
import files

class CannotSplit(Exception):
    """
    Used to indicate you cannot split the matrix due to size constraints.
    """
    def __init__(self, message=None):
        if not message:
            message = 'Cannot split, matrix too small.'
        self.message = message

class Part(object):
    """
    Object used as proxy to pass named information to manager.
    """
    def __init__(self, filename, ext, q, shape, a_elems):
        self.filename = filename
        self.ext = ext
        self.q = q
        self.shape = shape
        self.a_elems = a_elems

def create_p1(shape, ki, kj):
    """
    Creates intermediate step p1 using information from parent group.

    :param shape:
    :type shape: int
    :param ki:
    :type ki: int
    :param kj:
    :type kj: int
    :return: returns matrix p1
    :rtype: numpy.array
    """
    a = np.zeros(shape, dtype=np.int)
    for i, row in enumerate(a):
        for j, col in enumerate(row):
            a[i][j] = ki[i] * kj[j]
    return a

def create_p(p1, m):
    """
    Creates intermediate step p from p1 and m.

    :param p1:
    :type p1: numpy.array
    :param m:
    :type m: numpy.array
    :return: return matrix p
    :rtype: numpy.array
    """
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
    """
    Sort elements and corresponding rows to g1 or g2 based on whether or not the first eigenvector of the row is
    positive or negative.

    :param a: parent matrix
    :type a: numpy.array
    :param evec: set of eigenvectors for matrix a
    :type evec: numpy.array
    :return: both sets of order and arrays (g1, g2)
    :rtype: list of int, list of int, list of int, list of int
    """
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
    """
    Given a set of element numbers and rows, build a new group.

    :param order: row elements
    :type order: list
    :param arrays: rows for elements
    :type arrays: list
    :return: returns new matrix G assembled from order and arrays
    :rtype: numpy.array
    """
    size = len(order)
    g = np.zeros((size, size), dtype=np.int)
    for i, row in enumerate(g):
        for j, col in enumerate(order):
            g[i][j] = arrays[i][order[j]]
    return g

def create_q(size, b, order, m):
    """
    Retrieve Q value from given order of elements and information from parent matrix.

    :param size: size from parent matrix
    :type size: int
    :param b: B matrix from parent matrix
    :type b: numpy.array
    :param order: order of elements from grouping (g1, g2)
    :type order: list of int
    :param m: m from parent matrix
    :type m: numpy.array
    :return: first element of resulting matrix which is our Q value
    :rtype: float
    """
    s = np.matrix(np.zeros(size))
    for i in order:
        s[0,i] = 1
    a = np.dot(np.dot(s, b), s.T)
    a = a * (1. / (2. * m))
    return a.item(0)

def create_b_of_g(b, order):
    """
    Create new B of a grouping.

    :param b: B from parent matrix
    :type b: numpy.array
    :param order: ordering of elements from grouping
    :type order: list of int
    :return: returns B matrix for grouping
    :rtype: numpy.array
    """
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

def temp_split(filename):
    """
    Splits information on a temporary basis for debugging. Used for node/tree summary. Does not perform checks present
    in normal split method.

    :param filename:
    :type filename: str
    :return: returns two Part objects containing information for debugging
    :rtype: :py:class:`Part`, :py:class:`Part`
    """
    filename, ext = filename.rsplit('.')
    data = np.load(filename + "." + ext)
    # define basic constants from parent
    A = data['a']
    A_SIZE = A.shape[0]
    A_SHAPE = A.shape
    ORIGINAL_SIZE = data['original_size']
    B = data['b']
    # basics
    ki, kj, m = np.sum(A, 1), np.sum(A, 0), np.sum(np.sum(A, 1))
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
    # a_elems
    a1_elems = []
    a2_elems = []
    original_elems = data['a_elems']
    for i in g1_order:
        a1_elems.append(original_elems[i])
    for i in g2_order:
        a2_elems.append(original_elems[i])
    return Part(filename + ',1', ext, q1, g1.shape[0], ','.join([str(x) for x in a1_elems])), \
           Part(filename + ',2', ext, q2, g2.shape[0], ','.join([str(x) for x in a2_elems]))

def split(filename, initial=False, optimize=False):
    """
    Split the parent matrix into two separate groupings. Can be used for the initial split (master matrix) or subsequent
    groupings.

    :param filename:
    :type filename: str
    :param initial: True to perform duties for initial split, default is False
    :type initial: bool
    :param optimize: (currently) gather information on optimization results, default is True
    :type optimize: bool
    :return: if initial and optimize are True returns sorted list of optimization results, otherwise return two Parts
             for information regarding g1 and g2
    :rtype: [list of tuples (int, float, float) | :py:class:`Part`, :py:class:`Part`]
    """
    # load data
    filename, ext = filename.rsplit('.')
    data = np.load(filename + "." + ext)
    # define constants and load A if initial
    A = data['a']
    A_SIZE = A.shape[0]
    A_SHAPE = A.shape
    if initial:
        ORIGINAL_SIZE = A_SIZE
    else:
        ORIGINAL_SIZE = data['original_size']
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
        # save files
        np.savez('g1.npz', a=g1, b=b1, q=q1, a_elems=a1_elems, original_size=ORIGINAL_SIZE)
        np.savez('g2.npz', a=g2, b=b2, q=q2, a_elems=a2_elems, original_size=ORIGINAL_SIZE)
        # create File records
        files.File.create(filename='g1', ext=ext, q=q1, shape=g1.shape[0], a_elems=','.join([str(x) for x in a1_elems]))
        files.File.create(filename='g2', ext=ext, q=q2, shape=g2.shape[0], a_elems=','.join([str(x) for x in a2_elems]))
        # create Item records for burning
        files.Item.create(filename='.'.join(('g1', ext)))
        files.Item.create(filename='.'.join(('g2', ext)))
        if optimize:
            opt_table = []
            for idx, elem in enumerate(g1_order):
                # create copies of new arrays
                new_g1_order, new_g1_arrays, new_g2_order, new_g2_arrays = g1_order[:], g1_arrays[:], g2_order[:], g2_arrays[:]
                # first append new material to other array
                new_g2_order.append(elem)  # TODO: check if need to be sorted
                new_g2_arrays.append(new_g1_arrays[idx])  # TODO: check if insert instead if size g2 size is >= g1 size?
                # delete material from new_g1_*
                del new_g1_order[idx]
                del new_g1_arrays[idx]
                # create new Qs
                new_q1, new_q2 = create_q(A_SIZE, B, new_g1_order, m), create_q(A_SIZE, B, new_g2_order, m)
                opt_table.append((elem, new_q1, new_q2))
            return sorted(opt_table, key=lambda x: x[0])
    else:
        # return to manager to set parents
        np.savez(filename + ",1" + "." + ext, a=g1, b=b1, q=q1, a_elems=a1_elems, original_size=ORIGINAL_SIZE)
        np.savez(filename + ",2" + "." + ext, a=g2, b=b2, q=q2, a_elems=a2_elems, original_size=ORIGINAL_SIZE)
        # save filenames for burn regardless if saved or not, why didn't I do this before in master?
        files.Item.create(filename=filename + ',2.' + ext)
        files.Item.create(filename=filename + ',1.' + ext)
        # return so we can manipulate
        return Part(filename + ',1', ext, q1, g1.shape[0], ','.join([str(x) for x in a1_elems])), \
               Part(filename + ',2', ext, q2, g2.shape[0], ','.join([str(x) for x in a2_elems]))

def loadtxt(filename, save=True, stripe=True, blank=False):
    """
    Used to prep and convert text file of bitstrings to numpy compressed archive.

    :param filename:
    :type filename: str
    :param save: save results to numpy archive, else return matrix, default is True
    :type save: bool
    :param stripe: uh oh, this does nothing, woops
    :type stripe: bool
    :param blank: remove blank objects (rows & cols)
    :type blank: bool
    :return: return matrix if not saving to archive
    :rtype: numpy.array
    """
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
    """
    Remove blank objects (rows & cols) from matrix.

    :param mat:
    :type mat: numpy.array
    :return: return matrix with blank objects removed
    :rtype: numpy.array
    """
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
