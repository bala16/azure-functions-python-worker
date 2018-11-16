from azure.functions_worker import main

with open("pythonworker-worker.txt", "a") as myfile:
    myfile.write('python/worker.py main.main()')

if __name__ == '__main__':
    main.main()
