from rm import RM
import os
import numpy as np

np.set_printoptions(threshold=np.nan, linewidth=110)

a = RM(50)

print 'A size is', len(a.a), '', os.linesep, a.a
z = raw_input('Press any key to continue')
print 'Eigenvectors', os.linesep, a.evec
z = raw_input('Press any key to continue')
print 'G1', len(a.g1), os.linesep, a.g1
z = raw_input('Press any key to continue')
print 'G2', len(a.g2), os.linesep, a.g2
z = raw_input('Press any key to continue')

