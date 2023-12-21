
from .bitwarden import BitwardenCli


if __name__ == '__main__':
    bw_cli = BitwardenCli()
    bw_cli.login()
