
static PyObject *_get_interpstate_dict(void)
{
    /* hack around to return a dict that is subinterpreter-local */
    int err;
    PyObject *m, *modules = PyThreadState_GET()->interp->modules;

    if (modules == NULL) {
        PyErr_SetString(FFIError, "subinterpreter already gone?");
        return NULL;
    }
    m = PyDict_GetItemString(modules, "_cffi_backend._extern_py");
    if (m == NULL) {
        m = PyModule_New("_cffi_backend._extern_py");
        if (m == NULL)
            return NULL;
        err = PyDict_SetItemString(modules, "_cffi_backend._extern_py", m);
        Py_DECREF(m);    /* sys.modules keeps one reference to m */
        if (err < 0)
            return NULL;
    }
    return PyModule_GetDict(m);
}

static PyObject *_ffi_def_extern_decorator(PyObject *outer_args, PyObject *fn)
{
    char *s;
    PyObject *error, *onerror, *infotuple, *old1;
    int index, err;
    const struct _cffi_global_s *g;
    struct _cffi_externpy_s *externpy;
    CTypeDescrObject *ct;
    FFIObject *ffi;
    builder_c_t *types_builder;
    PyObject *name = NULL;
    PyObject *interpstate_dict;
    PyObject *interpstate_key;

    if (!PyArg_ParseTuple(outer_args, "OzOO", &ffi, &s, &error, &onerror))
        return NULL;

    if (s == NULL) {
        name = PyObject_GetAttrString(fn, "__name__");
        if (name == NULL)
            return NULL;
        s = PyText_AsUTF8(name);
        if (s == NULL) {
            Py_DECREF(name);
            return NULL;
        }
    }

    types_builder = &ffi->types_builder;
    index = search_in_globals(&types_builder->ctx, s, strlen(s));
    if (index < 0)
        goto not_found;
    g = &types_builder->ctx.globals[index];
    if (_CFFI_GETOP(g->type_op) != _CFFI_OP_EXTERN_PYTHON)
        goto not_found;
    Py_XDECREF(name);

    ct = realize_c_type(types_builder, types_builder->ctx.types,
                        _CFFI_GETARG(g->type_op));
    if (ct == NULL)
        return NULL;

    infotuple = prepare_callback_info_tuple(ct, fn, error, onerror, 0);
    Py_DECREF(ct);
    if (infotuple == NULL)
        return NULL;

    /* don't directly attach infotuple to externpy: in the presence of
       subinterpreters, each time we switch to a different
       subinterpreter and call the C function, it will notice the
       change and look up infotuple from the interpstate_dict.
    */
    interpstate_dict = _get_interpstate_dict();
    if (interpstate_dict == NULL) {
        Py_DECREF(infotuple);
        return NULL;
    }

    externpy = (struct _cffi_externpy_s *)g->address;
    interpstate_key = PyLong_FromVoidPtr((void *)externpy);
    if (interpstate_key == NULL) {
        Py_DECREF(infotuple);
        return NULL;
    }

    err = PyDict_SetItem(interpstate_dict, interpstate_key, infotuple);
    Py_DECREF(interpstate_key);
    Py_DECREF(infotuple);    /* interpstate_dict owns the last ref */
    if (err < 0)
        return NULL;

    /* force _update_cache_to_call_python() to be called the next time
       the C function invokes cffi_call_python, to update the cache */
    old1 = externpy->reserved1;
    externpy->reserved1 = Py_None;   /* a non-NULL value */
    Py_INCREF(Py_None);
    Py_XDECREF(old1);

    /* return the function object unmodified */
    Py_INCREF(fn);
    return fn;

 not_found:
    PyErr_Format(FFIError, "ffi.def_extern('%s'): no 'extern \"Python\"' "
                 "function with this name", s);
    Py_XDECREF(name);
    return NULL;
}


static int _update_cache_to_call_python(struct _cffi_externpy_s *externpy)
{
    PyObject *interpstate_dict, *interpstate_key, *infotuple, *old1, *new1;

    interpstate_dict = _get_interpstate_dict();
    if (interpstate_dict == NULL)
        goto error;

    interpstate_key = PyLong_FromVoidPtr((void *)externpy);
    if (interpstate_key == NULL)
        goto error;

    infotuple = PyDict_GetItem(interpstate_dict, interpstate_key);
    Py_DECREF(interpstate_key);
    if (infotuple == NULL)
        return 1;    /* no ffi.def_extern() from this subinterpreter */

    new1 = PyThreadState_GET()->interp->modules;
    Py_INCREF(new1);
    old1 = (PyObject *)externpy->reserved1;
    externpy->reserved1 = new1;         /* holds a reference        */
    externpy->reserved2 = infotuple;    /* doesn't hold a reference */
    Py_XDECREF(old1);

    return 0;   /* no error */

 error:
    PyErr_Clear();
    return 2;   /* out of memory? */
}

#if (defined(WITH_THREAD) && !defined(_MSC_VER) &&   \
     !defined(__amd64__) && !defined(__x86_64__) &&   \
     !defined(__i386__) && !defined(__i386))
# define read_barrier()  __sync_synchronize()
#else
# define read_barrier()  (void)0
#endif

static void cffi_call_python(struct _cffi_externpy_s *externpy, char *args)
{
    /* Invoked by the helpers generated from extern "Python" in the cdef.

       'externpy' is a static structure that describes which of the
       extern "Python" functions is called.  It has got fields 'name' and
       'type_index' describing the function, and more reserved fields
       that are initially zero.  These reserved fields are set up by
       ffi.def_extern(), which invokes _ffi_def_extern_decorator() above.

       'args' is a pointer to an array of 8-byte entries.  Each entry
       contains an argument.  If an argument is less than 8 bytes, only
       the part at the beginning of the entry is initialized.  If an
       argument is 'long double' or a struct/union, then it is passed
       by reference.

       'args' is also used as the place to write the result to
       (directly, even if more than 8 bytes).  In all cases, 'args' is
       at least 8 bytes in size.
    */
    int err = 0;

    /* This read barrier is needed for _embedding.h.  It is paired
       with the write_barrier() there.  Without this barrier, we can
       in theory see the following situation: the Python
       initialization code already ran (in another thread), and the
       '_cffi_call_python' function pointer directed execution here;
       but any number of other data could still be seen as
       uninitialized below.  For example, 'externpy' would still
       contain NULLs even though it was correctly set up, or
       'interpreter_lock' (the GIL inside CPython) would still be seen
       as NULL, or 'autoInterpreterState' (used by
       PyGILState_Ensure()) would be NULL or contain bogus fields.
    */
    read_barrier();

    save_errno();

    /* We need the infotuple here.  We could always go through
       interp->modules['..'][externpy], but to avoid the extra dict
       lookups, we cache in (reserved1, reserved2) the last seen pair
       (interp->modules, infotuple).
    */
    if (externpy->reserved1 == NULL) {
        /* Not initialized!  We didn't call @ffi.def_extern() on this
           externpy object from any subinterpreter at all. */
        err = 1;
    }
    else {
        PyGILState_STATE state = gil_ensure();
        if (externpy->reserved1 != PyThreadState_GET()->interp->modules) {
            /* Update the (reserved1, reserved2) cache.  This will fail
               if we didn't call @ffi.def_extern() in this particular
               subinterpreter. */
            err = _update_cache_to_call_python(externpy);
        }
        if (!err) {
            general_invoke_callback(0, args, args, externpy->reserved2);
        }
        gil_release(state);
    }
    if (err) {
        static const char *msg[2] = {
            "no code was attached to it yet with @ffi.def_extern()",
            "got internal exception (out of memory?)" };
        fprintf(stderr, "extern \"Python\": function %s() called, "
                        "but %s.  Returning 0.\n", externpy->name, msg[err-1]);
        memset(args, 0, externpy->size_of_result);
    }
    restore_errno();
}
