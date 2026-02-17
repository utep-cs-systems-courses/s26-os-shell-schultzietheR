# Placeholder file for Linux developers to work on later

import os
import sys
import re

while true:
    cmd = input("spsh: ")
    if cmd.lower() in ["exit","quit"]:
        break
    sys.run(cmd, shell=True)