from datetime import datetime, timedelta
import os

some_has_been_updated = False

experiments_names = ['baseline_',
                     'lava_']
runs = 10
limit_of_minutes = 15

while 1:

    for e in experiments_names:
        for r in range(0, runs):

            path = "experiments/data/" + e+str(r+1) + "/selectedpop_to_recover.txt"
            if os.path.isfile(path):
                time_ago = datetime.now() - timedelta(minutes=limit_of_minutes)
                filetime = datetime.fromtimestamp(os.path.getctime(path))
                if filetime > time_ago:
                    some_has_been_updated = True

    if not some_has_been_updated:

        os.system(" kill $(  ps aux | grep 'gzserver' | awk '{print $2}')")
        os.system(" kill $(  ps aux | grep 'revolve.py' | awk '{print $2}')")

        print('  killled !')

    some_has_been_updated = False

