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

        redirect_stdout = None
        new_tokens = []
        i = 0
        error_occurred = False

        # Process tokens to find redirection operators
        while i < len(tokens):
            token = tokens[i]
            if token in (">", "1>"):
                if i + 1 >= len(tokens):
                    sys.stdout.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stdout = tokens[i + 1]
                i += 2  # Skip the operator and filename
            else:
                new_tokens.append(token)
                i += 1

        if error_occurred:
            sys.stdout.flush()
            continue

        # Handle empty command with redirection
        if not new_tokens and redirect_stdout:
            try:
                with open(redirect_stdout, "w"):
                    pass
            except Exception as e:
                sys.stdout.write(f"Error creating file: {e}\n")
            sys.stdout.flush()
            continue
        elif not new_tokens:
            continue  # Skip processing if no command and no redirection

        cmd = new_tokens[0]

        # Handle exit command
        if cmd == "exit":
            if len(new_tokens) == 2 and new_tokens[1] == "0":
                break
            else:
                continue

        # Handle echo command
        if cmd == "echo":
            output = " ".join(new_tokens[1:]) + "\n"
            if redirect_stdout:
                try:
                    with open(redirect_stdout, "w") as f:
                        f.write(output)
                except Exception as e:
                    sys.stdout.write(f"Error writing to file: {e}\n")
            else:
                sys.stdout.write(output)
            sys.stdout.flush()
            continue

        # Handle pwd command
        if cmd == "pwd":
            pwd = os.getcwd() + "\n"
            if redirect_stdout:
                try:
                    with open(redirect_stdout, "w") as f:
                        f.write(pwd)
                except Exception as e:
                    sys.stdout.write(f"Error writing to file: {e}\n")
            else:
                sys.stdout.write(pwd)
            sys.stdout.flush()
            continue

        # Handle cd command
        if cmd == "cd":
            path = new_tokens[1] if len(new_tokens) > 1 else ""
            if path == "~" or not path:
                new_path = HOME
            else:
                new_path = os.path.expanduser(path)
                if not os.path.isabs(new_path):
                    new_path = os.path.abspath(new_path)
            if os.path.isdir(new_path):
                os.chdir(new_path)
            else:
                sys.stdout.write(f"cd: {path}: No such file or directory\n")
            sys.stdout.flush()
            continue

        # Handle type command
        if cmd == "type":
            output = []
            for cmd_name in new_tokens[1:]:
                if cmd_name in shell_builtin:
                    output.append(f"{cmd_name} is a shell builtin\n")
                else:
                    cmd_path = find_executable(cmd_name, path_dirs)
                    if cmd_path:
                        output.append(f"{cmd_name} is {cmd_path}\n")
                    else:
                        output.append(f"{cmd_name}: not found\n")
            full_output = "".join(output)
            if redirect_stdout:
                try:
                    with open(redirect_stdout, "w") as f:
                        f.write(full_output)
                except Exception as e:
                    sys.stdout.write(f"Error writing to file: {e}\n")
            else:
                sys.stdout.write(full_output)
            sys.stdout.flush()
            continue

        # Handle external commands
        cmd_path = find_executable(cmd, path_dirs)
        if cmd_path:
            try:
                if redirect_stdout:
                    with open(redirect_stdout, "w") as f:
                        subprocess.run(new_tokens, stdout=f)
                else:
                    subprocess.run(new_tokens)
            except Exception as e:
                sys.stdout.write(f"Error executing command: {e}\n")
        else:
            sys.stdout.write(f"{cmd}: command not found\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
