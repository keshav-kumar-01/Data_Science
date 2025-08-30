# multi threading with thread pool executer
#from concurrent.futures import ThreadPoolExecutor
#import time

#def print_numbers(number):
    #time.sleep(2)
    #return f"Numbers : {number}"

#numbers=[1,2,3,4,5,6,7,8,9,10]
#with ThreadPoolExecutor(max_workers=3) as executor:
#    results = executor.map(print_numbers,numbers)

#for result in results:
#    print(result)

from concurrent.futures import ProcessPoolExecutor
import time

def square_numbers(number):
    time.sleep(1)
    return f"Square : {number*number}"

numbers = [1,2,3,4,5,6,7,8,9,10]

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = executor.map(square_numbers, numbers)

    for result in results:
        print(result)
