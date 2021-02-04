import os

my_directory = os.path.dirname(os.path.abspath(__file__))


# Writes current branch and sha to a file that is displayed by the /git
# endpoint
def write(content):
    file = my_directory + "/tests/gitstats.txt"
    with open(file, 'w') as filetowrite:
        filetowrite.write(content)


# Reads the contents of the file for the deployed git branch status
def read():
    file = my_directory + "/tests/gitstats.txt"
    with open(file, 'r') as filetoread:
        return(filetoread.read())
