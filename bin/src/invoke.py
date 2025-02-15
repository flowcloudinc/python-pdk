import extism
import json
import traceback

# The idea is to keep the host functions wrapped under the extism interface
# As of now, host_callback is the host function that we intend to expose.
@extism.import_fn("fc", "host_callback")
def host_callback(typ: str, payload: str) -> str:
    pass


def __invoke(index, shared, *args):
    import extism

    import time
    # patch the *.sleep functions which will invoke the host_callback
    # instead and make the guest wait until the delay argument specified.
    # Note: We don't support asyncio yet, so please refrain from using it and
    # patching it here also.
    time.sleep = extism.sleep


    try:
        f = extism.__exports[index]

        if shared:
            a = []
            argnames = f.__code__.co_varnames
            for i, arg in enumerate(args):
                t = f.__annotations__.get(argnames[i], extism.memory.MemoryHandle)
                a.append(extism._load(t, arg))
        else:
            # The arguments to the function always have to be keyword mapped.
            # It is marshalled JSON.
            a = json.loads(extism.input_str())

        res = f(**a)

        extism.output(res)
        if shared and res is not None:
            return extism._store(res)
        if res is not None and "return" in f.__annotations__:
            return extism._load(f.__annotations__["return"], res)
        else:
            return res
    except BaseException as exc:
        tb = "".join(traceback.format_tb(exc.__traceback__))
        err = f"{str(exc)}:\n{tb}"
        extism.ffi.set_error(err)
        raise exc
