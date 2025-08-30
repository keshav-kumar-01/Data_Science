## multi threading - when there is I/O bound task that spends more time waiting for I/O or Concurrent execution
import threading
import time


def print_numbers():
    for i in range(5):
        time.sleep(2)
        print(f"Number : {i}")

def print_letter():
    for letters in "keshav":
        time.sleep(2)
        print(f"Letters : {letters}")


# create 2 thread
t1=threading.Thread(target=print_numbers)
t2=threading.Thread(target=print_letter)
t= time.time()
t1.start()
t2.start()


## wait for threads to complete
t1.join()
t2.join()
finished_time=(time.time()-t)
print(finished_time)
