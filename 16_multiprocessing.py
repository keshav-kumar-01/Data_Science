import multiprocessing
import time

def square_of_numbers():
    for i in range(5):
        time.sleep(1)
        print(f"Square is {i*i}")

def cube_of_numbers():
    for i in range(5):
        time.sleep(1.5)
        print(f"Cube is {i*i*i}")

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=square_of_numbers)
    p2 = multiprocessing.Process(target=cube_of_numbers)

    t1 = time.time()

    # start the processes
    p1.start()
    p2.start()

    # wait for them to finish
    p1.join()
    p2.join()

    print(f"Finished in: {time.time() - t1:.2f} seconds")
