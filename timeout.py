# Dumb timeout library that shouldn't even need to be a thing
import sys


class TimeoutExpired(Exception):
    pass

if sys.platform == "win32":
    import msvcrt
    import time

    def input_with_timeout(prompt, timeout, timer=time.monotonic):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        endtime = timer() + timeout
        result = []
        while timer() < endtime:
            if msvcrt.kbhit():
                result.append(msvcrt.getwche())
                if result[-1] == '\r':
                    msvcrt.putwch('\n')
                    return ''.join(result[:-1])
            time.sleep(0.04) # Yield to other threads
        raise TimeoutExpired

elif sys.platform == "Linux":
    import select

    def input_with_timeout(prompt, timeout):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        ready, _, _ = select.select([sys.stdin], [],[], timeout)
        if ready:
            return sys.stdin.readline().rstrip('\n') # expect stdin to be line-buffered
        raise TimeoutExpired
else:
    raise NotImplementedError("Your operating system is pretty bad: {}".format(sys.platform))
    
if __name__ == "__main__":
    a = input_with_timeout("Hello? ", 3)
    print(a)