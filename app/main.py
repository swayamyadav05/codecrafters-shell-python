import sys


def main():
    while True:
        # Display the prompt
        sys.stdout.write("$ ")
        sys.stdout.flush()

        shell_builtin = ["exit", "echo", "type"]
        # Wait for user input
        command = input().strip()

        # Skip empty commands
        if not command:
            continue

        # Check for exit condition
        if command == "exit 0":
            sys.exit()

        # Split the command into words
        cmd = command.split()

        # Process the command using and if-elif-else structure
        if cmd[0] == "echo":
            # Print everything after the command name
            print(" ".join(cmd[1:]))
        elif cmd[0] == "type" and cmd[1] in shell_builtin:
            print(f"{cmd[1]} is a shell builtin")
        elif cmd[0] == "type" and cmd[1] not in shell_builtin:
            print(f"{cmd[1]}: command not found")
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
