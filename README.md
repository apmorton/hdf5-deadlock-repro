* PyTables issue: https://github.com/PyTables/PyTables/issues/957
* h5py issue: https://github.com/h5py/h5py/issues/2128

This deadlock was observed in the wild in a real application that was using the following concurrently:
- pandas `read_hdf`/`to_hdf`
- a custom data format library using h5py

This is not easily reproducable outside of conda (IE, using pip) because `tables` and `h5py` binary wheels each include their own uniquely named copy of the hdf5 library and therefor will not share the same mutex in `H5TS_mutex_lock`.

To reproduce you need a working conda install.

Run `make` to install a conda environment and run the reproducer.

You should see something like:
```
env/bin/python repro.py
starting
no deadlock yet  0
```

The program has deadlocked if it stops outputting new lines and counting upwards.


## pytables thread
```
#0  futex_wait_cancelable (private=<optimized out>, expected=0, futex_word=0x7ffff762595c <H5_g+92>) at ../sysdeps/nptl/futex-internal.h:183
#1  __pthread_cond_wait_common (abstime=0x0, clockid=0, mutex=0x7ffff7625908 <H5_g+8>, cond=0x7ffff7625930 <H5_g+48>) at pthread_cond_wait.c:508
#2  __pthread_cond_wait (cond=0x7ffff7625930 <H5_g+48>, mutex=0x7ffff7625908 <H5_g+8>) at pthread_cond_wait.c:638
#3  0x00007ffff74f3164 in H5TS_mutex_lock () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/../../../libhdf5.so.200
#4  0x00007ffff726f651 in H5open () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/../../../libhdf5.so.200
#5  0x00007fff2b53e628 in __pyx_pf_6tables_13hdf5extension_4File__g_new (__pyx_v_params=<optimized out>, __pyx_v_pymode=<optimized out>, __pyx_v_name=<optimized out>, __pyx_v_self=0x7fff2fe39670) at tables/hdf5extension.c:5243
#6  __pyx_pw_6tables_13hdf5extension_4File_1_g_new (__pyx_v_self=0x7fff2fe39670, __pyx_args=<optimized out>, __pyx_kwds=<optimized out>) at tables/hdf5extension.c:4036
#7  0x000055555569850c in cfunction_call (func=0x7fff2fec8450, args=<optimized out>, kwargs=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/methodobject.c:543
#8  0x00005555556a6db9 in _PyObject_Call (kwargs=<optimized out>, args=0x7ffff77f0780, callable=0x7fff2fec8450, tstate=0x555555f15030) at /usr/local/src/conda/python-3.10.5/Objects/call.c:305
#9  PyObject_Call (callable=0x7fff2fec8450, args=0x7ffff77f0780, kwargs=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/call.c:317
#10 0x000055555568dd00 in do_call_core (kwdict=0x7fff2b39a780, callargs=0x7ffff77f0780, func=0x7fff2fec8450, trace_info=0x7fff2b213330, tstate=<optimized out>) at /usr/local/src/conda/python-3.10.5/Python/ceval.c:5893
#11 _PyEval_EvalFrameDefault (tstate=<optimized out>, f=<optimized out>, throwflag=<optimized out>) at /usr/local/src/conda/python-3.10.5/Python/ceval.c:4277
#12 0x0000555555690b42 in _PyEval_EvalFrame (throwflag=0, f=0x7fff2fa66040, tstate=0x555555f15030) at /usr/local/src/conda/python-3.10.5/Python/ceval.c:5052
#13 _PyEval_Vector (kwnames=0x0, argcount=<optimized out>, args=<optimized out>, locals=0x0, con=0x7fff2b3b34a0, tstate=0x555555f15030) at /usr/local/src/conda/python-3.10.5/Python/ceval.c:5065
#14 _PyFunction_Vectorcall (kwnames=0x0, nargsf=<optimized out>, stack=<optimized out>, func=0x7fff2b3b3490) at /usr/local/src/conda/python-3.10.5/Objects/call.c:342
#15 _PyObject_FastCallDictTstate (tstate=0x555555f15030, callable=0x7fff2b3b3490, args=<optimized out>, nargsf=<optimized out>, kwargs=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/call.c:142
#16 0x00005555556a339b in _PyObject_Call_Prepend (kwargs=0x7fff2fe80540, args=0x7fff2b4436a0, obj=<optimized out>, callable=0x7fff2b3b3490, tstate=0x7fff2b2134b0) at /usr/local/src/conda/python-3.10.5/Objects/call.c:431
#17 slot_tp_init (self=<optimized out>, args=<optimized out>, kwds=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/typeobject.c:7731
#18 0x0000555555691be5 in type_call (type=<optimized out>, args=0x7fff2b4436a0, kwds=0x7fff2fe80540) at /usr/local/src/conda/python-3.10.5/Objects/typeobject.c:4435
#19 0x00005555556a6db9 in _PyObject_Call (kwargs=<optimized out>, args=0x7fff2b4436a0, callable=0x555555ef8410, tstate=0x555555f15030) at /usr/local/src/conda/python-3.10.5/Objects/call.c:305
```

## h5py thread
```
#0  futex_abstimed_wait_cancelable (private=<optimized out>, abstime=0x7fff2a990d10, clockid=<optimized out>, expected=0, futex_word=0x5555558f792c <_PyRuntime+428>) at ../sysdeps/nptl/futex-internal.h:320
#1  __pthread_cond_wait_common (abstime=0x7fff2a990d10, clockid=<optimized out>, mutex=0x5555558f7930 <_PyRuntime+432>, cond=0x5555558f7900 <_PyRuntime+384>) at pthread_cond_wait.c:520
#2  __pthread_cond_timedwait (cond=0x5555558f7900 <_PyRuntime+384>, mutex=0x5555558f7930 <_PyRuntime+432>, abstime=0x7fff2a990d10) at pthread_cond_wait.c:656
#3  0x000055555566e6bd in PyCOND_TIMEDWAIT (us=<optimized out>, mut=<optimized out>, cond=0x5555558f7900 <_PyRuntime+384>) at /usr/local/src/conda/python-3.10.5/Python/condvar.h:73
#4  take_gil (tstate=0x7fff2a990d10) at /usr/local/src/conda/python-3.10.5/Python/ceval_gil.h:255
#5  0x00005555556b8022 in PyEval_RestoreThread (tstate=0x555555f0dbc0) at /usr/local/src/conda/python-3.10.5/Python/ceval.c:547
#6  0x000055555577b0f4 in PyGILState_Ensure () at /usr/local/src/conda/python-3.10.5/Python/pystate.c:1519
#7  0x00007fff2fdb68a8 in __pyx_f_4h5py_5_conv_vlen2str () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/_conv.cpython-310-x86_64-linux-gnu.so
#8  0x00007ffff747a37c in H5T_convert () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/../../../libhdf5.so.200
#9  0x00007ffff747a4f3 in H5Tconvert () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/../../../libhdf5.so.200
#10 0x00007fff2fefb149 in __pyx_f_4h5py_4defs_H5Tconvert () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/defs.cpython-310-x86_64-linux-gnu.so
#11 0x00007fff2fc7d8f2 in __pyx_f_4h5py_6_proxy_dset_rw () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/_proxy.cpython-310-x86_64-linux-gnu.so
#12 0x00007fff2fc64b58 in __pyx_pw_4h5py_3h5d_9DatasetID_1read () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/h5d.cpython-310-x86_64-linux-gnu.so
#13 0x0000555555699c8e in method_vectorcall_VARARGS_KEYWORDS (func=<optimized out>, args=<optimized out>, nargsf=<optimized out>, kwnames=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/stringlib/unicode_format.h:925
#14 0x00005555556a6fc9 in PyVectorcall_Call (callable=0x7fff2fe5e070, tuple=<optimized out>, kwargs=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/call.c:267
#15 0x00007fff2ffd8808 in __pyx_pw_4h5py_8_objects_9with_phil_1wrapper () from /home/amorton/repro/env/lib/python3.10/site-packages/h5py/_objects.cpython-310-x86_64-linux-gnu.so
#16 0x0000555555691858 in _PyObject_MakeTpCall (tstate=0x555555f0dbc0, callable=0x7fff2fe1b510, args=<optimized out>, nargs=<optimized out>, keywords=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/call.c:215
#17 0x00005555556a63e0 in _PyObject_VectorcallTstate (kwnames=<optimized out>, nargsf=<optimized out>, args=0x7fff1c092190, callable=0x7fff2fe1b510, tstate=0x555555f0dbc0) at /usr/local/src/conda/python-3.10.5/Include/cpython/abstract.h:112
#18 _PyObject_VectorcallTstate (kwnames=<optimized out>, nargsf=<optimized out>, args=0x7fff1c092190, callable=0x7fff2fe1b510, tstate=0x555555f0dbc0) at /usr/local/src/conda/python-3.10.5/Include/cpython/abstract.h:99
#19 method_vectorcall (method=<optimized out>, args=0x7fff1c092198, nargsf=<optimized out>, kwnames=<optimized out>) at /usr/local/src/conda/python-3.10.5/Objects/classobject.c:53
```
