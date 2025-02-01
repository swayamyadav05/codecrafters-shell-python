import sys
import os
import subprocess
import shlex


def find_executable(cmd, path_dirs):
    """Search for an executable command in the directories listed in PATH."""
    for path in path_dirs:
        cmd_path = os.path.join(path, cmd)
        if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
            return cmd_path
    return None


def handle_redirection(command):
    """Check if output redirection is requested, and split the command accordingly."""
    if ">" in command:
        parts = command.split(">")
        command_part = parts[0].strip()
        file_part = parts[1].strip()
        return command_part, file_part
    return command, None


def main():
    shell_builtin = {"exit", "echo", "type", "pwd", "cd"}  # Using a set for fast lookup
    PATH = os.environ.get("PATH", "")
    path_dirs = PATH.split(":")
    HOME = os.environ.get("HOME", "/")  # Get home directory from environment

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

        # Use shlex.split to correctly parse quoted arguments
        try:
            tokens = shlex.split(command)
        except ValueError as e:
            sys.stdout.write(f"Error: {e}\n")
            sys.stdout.flush()
            continue

        # Handle exit command
        if tokens[0] == "exit" and len(tokens) == 2 and tokens[1] == "0":
            break

        # Handle echo command (preserves quotes)
        if tokens[0] == "echo":
            # Handle redirection in echo command
            if ">" in command:
                command, file_to_redirect = handle_redirection(command)
                with open(file_to_redirect, "w") as f:
                    f.write(" ".join(tokens[1:]) + "\n")
                continue  # Do not print anything, just handle the redirection
            else:
                sys.stdout.write(" ".join(tokens[1:]) + "\n")
            sys.stdout.flush()
            continue

        # Handle pwd command
        if tokens[0] == "pwd":
            sys.stdout.write(f"{os.getcwd()}\n")
            sys.stdout.flush()
            continue

        # Handle cd command (Supports ~ and quoted paths)
        if tokens[0] == "cd":
            if len(tokens) < 2:
                continue  # Do nothing if no argument is given

            path = tokens[1]

            # If '~' is used, go to the home directory
            if path == "~":
                new_path = HOME
            else:
                # Convert relative paths to absolute
                new_path = os.path.abspath(path) if not os.path.isabs(path) else path

            if os.path.isdir(new_path):  # Check if directory exists
                os.chdir(new_path)  # Change directory
            else:
                sys.stdout.write(f"cd: {path}: No such file or directory\n")

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

        # Handle redirection (other commands)
        command, file_to_redirect = handle_redirection(command)
        if file_to_redirect:
            try:
                # Execute the command and redirect its output to the file
                cmd_path = find_executable(command.split()[0], path_dirs)
                if cmd_path:
                    with open(file_to_redirect, "w") as f:
                        subprocess.run(
                            command.split(), stdout=f, stderr=subprocess.PIPE
                        )
                else:
                    sys.stdout.write(f"{command.split()[0]}: command not found\n")
            except Exception as e:
                sys.stdout.write(f"Error: {e}\n")

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
