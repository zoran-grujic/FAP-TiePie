"""
Explanation:

Convert ui into py file

Instruction:

To make this file specific for your self make a copy of the file
 with name: 'gui-compile.py' and use your local copy.
Change the path to the 'pyuic5' according to your own environment!
Run to have make it as an untracked copy:
git rm --cached gui-compile.py

"""

import os

cmd = "C:\\Users\\NameOfTheUser\\Anaconda3\\Library\\bin\\pyuic5 gui.ui -o gui.py"
os.system(cmd)

