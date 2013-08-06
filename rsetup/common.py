import subprocess


def exe(cmd):
    stdout, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    return stdout