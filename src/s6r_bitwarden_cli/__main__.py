
from .bitwarden import BitwardenCli


def main():
    bw_cli = BitwardenCli()
    bw_cli.login()


if __name__ == '__main__':
    main()
