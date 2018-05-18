from chs.models import Account
from chs.pgn import load_file
import os

# Change this to whatever account name you want to use
account = Account.objects.get(pseudo="colin")

# Set the files to load here
files = []
for f in os.listdir(".."):
    if f.startswith("KingBase"):
        # take care to use proper encoding, as the parser may otherwise fail
        files.append(open("../" + f, encoding="cp1252"))

# You should not need to change this
for f in files:
    print("Loading file " + f.name)
    load_file(f, account)
