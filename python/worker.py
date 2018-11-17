import os
dir_path = os.path.dirname(os.path.realpath(__file__))
cwd = os.getcwd()

with open("pythonworker-worker.txt", "a") as myfile:
    myfile.write("dir_path = '{0}' cwd = '{1}'".format(dir_path , cwd))

from azure.functions_worker import main

with open("pythonworker-worker.txt", "a") as myfile:
    myfile.write('before2 python/worker.py main.main()')

if __name__ == '__main__':
    main.main()
