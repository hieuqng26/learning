import os
import sys
from ORE import *

os.chdir('../../doc/ORE/Examples/Exposure')
sys.path.append('../')

params_xva = Parameters()
params_xva.fromFile("Input/ore_swaption.xml")
ore_xva = OREApp(params_xva, True)
ore_xva.run()
print("\n✓ ORE example ran successfully")
