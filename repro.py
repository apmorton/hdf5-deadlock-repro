import time
import threading

import h5py
import tables


def thread_tables():
    with h5py.File('tables.h5', mode='w') as f:
        f.create_dataset('ds', dtype='|S2', data=['s1', 's2'])

    while True:
        with tables.open_file('tables.h5') as f:
            f.get_node('/ds')


def thread_h5py():
    with h5py.File('h5py.h5', mode='w') as f:
        f.create_dataset('ds', data=['s1', 's2'])

    while True:
        with h5py.File('h5py.h5') as f:
            f.get('/ds')[()]


def main():
    thrd1 = threading.Thread(target=thread_tables, daemon=True)
    thrd2 = threading.Thread(target=thread_h5py, daemon=True)

    print('starting')
    thrd1.start()
    thrd2.start()

    i = 0
    while True:
        print('no deadlock yet ', i)
        i += 1
        time.sleep(1)


if __name__ == '__main__':
    main()
