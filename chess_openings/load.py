from chs.models import Account
from chs.pgn import load_file
import os

account = Account.objects.get(pseudo="colin")

files = []
for f in os.listdir(".."):
    if f.startswith("KingBase"):
        files.append(open("../" + f, encoding="cp1252"))

for f in files:
    print("Loading file " + f.name)
    load_file(f, account)
