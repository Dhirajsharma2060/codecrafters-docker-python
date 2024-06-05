import subprocess
import sys
import os
import ctypes

# Define the CLONE_NEWPID flag
CLONE_NEWPID = 0x20000000

def unshare(flags):
    libc = ctypes.CDLL("libc.so.6")
    if libc.unshare(flags) != 0:
        raise OSError("unshare failed")

def main():
    # Uncomment this block to pass the first stage
    #
    command = sys.argv[3]
    args = sys.argv[4:]
    #
    os.system("mkdir -p /yinh/usr/local/bin")
    os.system("cp /usr/local/bin/docker-explorer /yinh/usr/local/bin")

    # Unshare the PID namespace
    unshare(CLONE_NEWPID)

    # Fork the process
    pid = os.fork()
    if pid == 0:  # Child process
        os.chroot("/yinh")
        os.chdir("/")
        # Replace the current process with the target command
        os.execvp(command, [command] + args)
    else:  # Parent process
        _, status = os.waitpid(pid, 0)  # Wait for the child process to finish
        sys.exit(os.WEXITSTATUS(status))  # Exit with the same status as the child

if __name__ == "__main__":
    main()
