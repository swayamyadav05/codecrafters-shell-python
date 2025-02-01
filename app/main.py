import sys
import os
import subprocess


def find_executable(cmd, path_dirs):
    """Search for an executable command in the directories listed in PATH."""
    for path in path_dirs:
        cmd_path = os.path.join(path, cmd)
        if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
            return cmd_path
    return None


def main():
    shell_builtin = {"exit", "echo", "type"}  # Using a set for fast lookup
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

        tokens = command.split()

        # Handle exit command
        if tokens[0] == "exit" and len(tokens) == 2 and tokens[1] == "0":
            break

        # Handle echo command
        if tokens[0] == "echo":
            sys.stdout.write(" ".join(tokens[1:]) + "\n")
            sys.stdout.flush()
            continue

        # Handle type command
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

        # Handle external commands
        cmd_path = find_executable(tokens[0], path_dirs)
        if cmd_path:
            try:
                subprocess.run([tokens[0]] + tokens[1:], executable=cmd_path)
            except Exception as e:
                sys.stdout.write(f"Error executing {tokens[0]}: {e}\n")
        else:
            sys.stdout.write(f"{tokens[0]}: command not found\n")

        sys.stdout.flush()


if __name__ == "__main__":
    main()
