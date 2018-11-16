with open("pythonworker-worker.txt", "a") as myfile:
    myfile.write('before1 python/worker.py main.main()')

from azure.functions_worker import main

with open("pythonworker-worker.txt", "a") as myfile:
    myfile.write('before2 python/worker.py main.main()')

if __name__ == '__main__':
    main.main()
