import os
import subprocess
import sys
import tempfile
import ctypes
import logging
from urllib import request
import json
import tarfile

registry_base = "https://registry-1.docker.io/v2/library"
auth_base = "https://auth.docker.io"

def get_auth_token(service: str) -> str:
    try:
        uri = f"{auth_base}/token?service=registry.docker.io&scope=repository:library/{service}:pull"
        resp = request.urlopen(request.Request(uri, method="GET"))
        resp_data = resp.read().decode("utf-8")
        resp_json = json.loads(resp_data)
        return resp_json["token"]
    except Exception as e:
        logging.error(f"Error fetching auth token: {e}")
        sys.exit(1)

def get_image_blobs(service: str, tag: str, auth_token: str) -> list[str]:
    try:
        uri = f"{registry_base}/{service}/manifests/{tag}"
        req = request.Request(
            uri, method="GET", headers={"Authorization": f"Bearer {auth_token}"}
        )
        resp = request.urlopen(req)
        resp_data = resp.read().decode("utf-8")
        resp_json = json.loads(resp_data)
        blobs = [layer["blobSum"] for layer in resp_json["fsLayers"]]
        return blobs
    except Exception as e:
        logging.error(f"Error fetching image blobs: {e}")
        sys.exit(1)

def pull_image_layers(service: str, blobs: list[str], auth_token: str, output_dir: str):
    try:
        for blob in blobs:
            uri = f"{registry_base}/{service}/blobs/{blob}"
            req = request.Request(
                uri, method="GET", headers={"Authorization": f"Bearer {auth_token}"}
            )
            with tempfile.TemporaryDirectory() as tmp_dir:
                with open(os.path.join(tmp_dir, f"{blob}.tar"), "wb") as f:
                    with request.urlopen(req) as resp:
                        f.write(resp.read())
                for file in os.listdir(tmp_dir):
                    ff = tarfile.open(os.path.join(tmp_dir, file))
                    ff.extractall(output_dir)
    except Exception as e:
        logging.error(f"Error pulling image layers: {e}")
        sys.exit(1)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        image = sys.argv[2]
        tag = "latest" if ":" not in image else image.split(":")[1]
        command = sys.argv[3]
        args = sys.argv[4:]
        with tempfile.TemporaryDirectory() as tmp_dir:
            auth_token = get_auth_token(image)
            blobs = get_image_blobs(image, tag, auth_token)
            pull_image_layers(image, blobs, auth_token, tmp_dir)
            command = command[command.rfind("/") + 1 :]
            unshare = 272
            clone_new_pid = 0x20000000
            libc = ctypes.CDLL(None)
            libc.syscall(unshare, clone_new_pid)
            os.chroot(tmp_dir)
            completed_process = subprocess.run([command, *args], capture_output=True)
            sys.stdout.buffer.write(completed_process.stdout)
            sys.stderr.buffer.write(completed_process.stderr)
            sys.exit(completed_process.returncode)
    except IndexError:
        logging.error("Usage: python script.py <image> <command> <args>")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()
