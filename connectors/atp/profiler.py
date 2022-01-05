from memory_profiler import profile
# pip install memory-profiler

@profile
def my_func():
    import app

if __name__ == '__main__':
    my_func()

