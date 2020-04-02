import os
import time

START_TIME = time.time()


def footer_exit(status=0):
    ## -----*----- EXIT -----*----- ##
    print("")
    print("")
    print("")
    print("----------------------------------------------------------------------")
    print("Ran {} {} in {:5.3f}s".format(
        status,
        os.path.basename(__file__),
        time.time() - START_TIME
    ))
    print("")
    if status==0:
        print("\033[32mOK\033[0m")
    else:
        print("\033[31mERROR\033[0m")

    exit(status)

