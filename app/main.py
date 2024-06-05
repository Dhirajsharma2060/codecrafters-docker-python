import subprocess
import sys
import tempfile
import shutil
import os
def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    command = sys.argv[3]
    args = sys.argv[4:]
    tmp_dir = tempfile.mkdtemp()
    shutil.copy(command, tmp_dir)
    os.chroot(tmp_dir)
    command = os.path.join("/", os.path.basename(command))
    completed_process = subprocess.run([command, *args], capture_output=True)
    sys.stdout.write(completed_process.stdout.decode("utf-8"))
    sys.stderr.write(completed_process.stderr.decode("utf-8"))
    exit(completed_process.returncode)
if __name__ == "__main__":
    main()