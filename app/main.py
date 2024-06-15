import sys
import os
import ctypes
import requests
import tarfile

CLONE_NEWPID = 0x20000000

def unshare(flags):
    libc = ctypes.CDLL("libc.so.6")
    if libc.unshare(flags) != 0:
        raise OSError("unshare failed")

def authenticate(image):
    auth_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/{image}:pull"
    response = requests.get(auth_url)
    response.raise_for_status()
    token = response.json()["token"]
    return token

def fetch_manifest(image, tag, token):
    manifest_url = f"https://registry.hub.docker.com/v2/library/{image}/manifests/{tag}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(manifest_url, headers=headers)
    response.raise_for_status()
    manifest = response.json()
    return manifest

def pull_layers(image, manifest, token, chroot_dir):
    headers = {"Authorization": f"Bearer {token}"}
    for layer in manifest["layers"]:
        layer_url = f"https://registry.hub.docker.com/v2/library/{image}/blobs/{layer['digest']}"
        response = requests.get(layer_url, headers=headers, stream=True)
        response.raise_for_status()
        
        layer_file = os.path.join(chroot_dir, layer['digest'].replace(":", "_") + ".tar")
        with open(layer_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        
        with tarfile.open(layer_file, "r") as tar:
            tar.extractall(chroot_dir)
        
        os.remove(layer_file)

def main():
    if len(sys.argv) < 3:
        print("Usage: mydocker run <image:tag> <command> [args...]")
        sys.exit(1)
    
    image_tag = sys.argv[2].split(":")
    image = image_tag[0]
    tag = image_tag[1] if len(image_tag) > 1 else "latest"
    command = sys.argv[3]
    args = sys.argv[4:]

    chroot_dir = "/yinh"
    os.system(f"mkdir -p {chroot_dir}")

    token = authenticate(image)
    manifest = fetch_manifest(image, tag, token)
    pull_layers(image, manifest, token, chroot_dir)

    unshare(CLONE_NEWPID)
    pid = os.fork()
    if pid == 0:  # Child process
        os.chroot(chroot_dir)
        os.chdir("/")
        os.execvp(command, [command] + args)
    else:  # Parent process
        _, status = os.waitpid(pid, 0)
        sys.exit(os.WEXITSTATUS(status))

if __name__ == "__main__":
    main()
