import threading, functools

def threaded_func(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread  # 如果需要返回线程对象，可以返回它，否则可以选择不返回
    return wrapper