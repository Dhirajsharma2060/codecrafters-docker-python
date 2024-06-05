import subprocess
import sys
import os


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    #print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[3]
    args = sys.argv[4:]
    #
    os.system("mkdir -p /yinh/usr/local/bin")
    os.system("cp /usr/local/bin/docker-explorer /yinh/usr/local/bin")
    os.chroot("/yinh")
    completed_process = subprocess.run([command, *args], capture_output=True)
    #print(completed_process.stdout.decode("utf-8"))
    sys.stdout.buffer.write(completed_process.stdout)
    sys.stderr.buffer.write(completed_process.stderr)
    sys.exit(completed_process.returncode)


if __name__ == "__main__":
    main()
