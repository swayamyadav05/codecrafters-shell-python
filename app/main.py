import sys
import os


def find_executable(cmd, path_dirs):
    for path in path_dirs:
        cmd_path = os.path.join(path, cmd)
        if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
            return cmd_path
    return None


def main():
    shell_builtin = ["exit", "echo", "type"]
    PATH = os.environ.get("PATH", "")
    path_dirs = PATH.split(":")

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        # Wait for user input
        try:
            command = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        # Skip empty commands
        if not command:
            continue

        # Check for exit condition
        if command == "exit 0":
            break

        tokens = command.split()

        if tokens[0] == "echo":
            sys.stdout.write(" ".join(tokens[1:]) + "\n")
            sys.stdout.flush()
            continue

        if tokens[0] == "type":
            for cmd in tokens[1:]:
                if cmd in shell_builtin:
                    sys.stdout.write(f"{cmd} is a shell builtin\n")
                else:
                    cmd_path = find_executable(cmd, path_dirs)
                    if cmd_path:
                        sys.stdout.write(f"{cmd} is {cmd_path}\n")
                    else:
                        sys.stdout.write(f"{cmd}: not found\n")
            sys.stdout.flush()
            continue

        sys.stdout.write(f"{tokens[0]}: command not found\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
