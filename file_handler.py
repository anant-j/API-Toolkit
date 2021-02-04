import os

my_directory = os.path.dirname(os.path.abspath(__file__))


def write(content):
    file = my_directory + "/tests/gitstats.txt"
    with open(file, 'w') as filetowrite:
        filetowrite.write(content)


def read():
    file = my_directory + "/tests/gitstats.txt"
    with open(file, 'r') as filetoread:
        return(filetoread.read())
