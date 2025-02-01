import sys


def main():
    while True:
        sys.stdout.write("$ ")

        # Wait for user input
        command = input().strip()

        if not command:
            continue

        if command == "exit 0":
            sys.exit()

        cmd = command.split()

        if cmd[0] == "echo":
            print(" ".join(cmd[1:]))
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
