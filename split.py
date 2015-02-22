import numpy as np
from numpy import linalg
import master

# basically skip the process of making B, just import that, then
# create the new B of Gs later after using it


def split(filename):
    data = np.load(filename)
    a = data['a']
    a_size = a.shape[0]
    a_shape = a.shape
