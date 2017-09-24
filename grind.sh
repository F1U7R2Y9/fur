python main.py $1
gcc -ggdb3 "$1".c
valgrind --tool=memcheck --leak-check=yes --show-reachable=yes --num-callers=20 --track-fds=yes --error-exitcode=666 ./a.out
