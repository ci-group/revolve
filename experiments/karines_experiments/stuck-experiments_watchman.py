from datetime import datetime, timedelta
import os

# set these variables according to your experiments #
dir_path = '../data'
experiments_names = ['baseline_',
                     'lava_'
                     ]
runs = 10
limit_of_minutes = 5
# set these variables according to your experiments #

some_has_been_updated = False
while 1:

    # 5 minutes
    os.system(" sleep 300s")

    for exp in experiments_names:
        for run in range(0, runs):

            path = dir_path + "/" + exp +'_'+str(run+1) + "/data_fullevolution/fitness"
            if os.path.isdir(path):
                files = []
                for r, d, f in os.walk(path):
                    for file in f:
                        filetime = datetime.fromtimestamp(os.path.getctime(path+'/'+file))
                        files.append(filetime)
                files.sort()
                print(files)
                time_ago = datetime.now() - timedelta(minutes=limit_of_minutes)
                print(files[-1])
                print(time_ago)
                if files[-1] > time_ago:
                     some_has_been_updated = True

    if not some_has_been_updated:
       os.system(" kill $(  ps aux | grep 'gzserver' | awk '{print $2}')")
       os.system(" kill $(  ps aux | grep 'revolve.py' | awk '{print $2}')")
       print('  killled gzserver and revolve.py !')

    some_has_been_updated = False

