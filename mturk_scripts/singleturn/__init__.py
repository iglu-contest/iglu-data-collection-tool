import os
import sys
# With this we tell the system singleturn also depends on parent folder,
# even if they do not know
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
