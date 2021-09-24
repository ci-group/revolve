while true
    do
        sleep 900s
        kill $( ps aux | grep 'gzserver' | awk '{print $2}');
        kill $( ps aux | grep 'revolve.py' | awk '{print $2}' );
        sleep 60s
    done
