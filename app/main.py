import sys
import os
import subprocess
import shlex


def mysplit(input):
    """Custom function to split input handling quotes and escape sequences."""
    res = [""]
    current_quote = ""
    i = 0
    while i < len(input):
        c = input[i]
        if c == "\\":
            ch = input[i + 1]
            if current_quote == "'":
                res[-1] += c
            elif current_quote == '"':
                if ch in ["\\", "$", '"', "\n"]:
                    res[-1] += ch
                else:
                    res[-1] += "\\" + ch
                i += 1
            else:
                res[-1] += input[i + 1]
                i += 1
        elif c in ['"', "'"]:
            if current_quote == "":
                current_quote = c
            elif current_quote == c:
                current_quote = ""
            else:
                res[-1] += c
        elif c == " " and current_quote == "":
            if res[-1] != "":
                res.append("")
        else:
            res[-1] += c
        i += 1
    if res[-1] == "":
        res.pop()
    return res


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


def handle_command(tokens, path_dirs, HOME):
    """Handles the logic for various shell commands."""
    if tokens[0] == "exit" and len(tokens) == 2 and tokens[1] == "0":
        sys.exit(0)

    if tokens[0] == "echo":
        command, file_to_redirect = handle_redirection(" ".join(tokens))
        if file_to_redirect:
            with open(file_to_redirect, "w") as f:
                f.write(" ".join(tokens[1:]) + "\n")
        else:
            sys.stdout.write(" ".join(tokens[1:]) + "\n")
        sys.stdout.flush()

    elif tokens[0] == "pwd":
        sys.stdout.write(f"{os.getcwd()}\n")
        sys.stdout.flush()

    elif tokens[0] == "cd":
        if len(tokens) < 2:
            return
        path = tokens[1]
        new_path = HOME if path == "~" else os.path.abspath(path)
        if os.path.isdir(new_path):
            os.chdir(new_path)
        else:
            sys.stderr.write(f"cd: {path}: No such file or directory\n")
        sys.stdout.flush()

    elif tokens[0] == "type":
        for cmd in tokens[1:]:
            if cmd in {"exit", "echo", "pwd", "cd", "type"}:
                sys.stdout.write(f"{cmd} is a shell builtin\n")
            else:
                cmd_path = find_executable(cmd, path_dirs)
                if cmd_path:
                    sys.stdout.write(f"{cmd} is {cmd_path}\n")
                else:
                    sys.stdout.write(f"{cmd}: not found\n")
        sys.stdout.flush()

    else:
        command, file_to_redirect = handle_redirection(" ".join(tokens))
        cmd_path = find_executable(command.split()[0], path_dirs)
        if cmd_path:
            try:
                with (
                    open(file_to_redirect, "w") if file_to_redirect else sys.stdout
                ) as out:
                    subprocess.run(
                        [command.split()[0]] + tokens[1:],
                        executable=cmd_path,
                        stdout=out,
                        stderr=sys.stderr,
                    )
            except Exception as e:
                sys.stderr.write(f"Error executing {command.split()[0]}: {e}\n")
        else:
            sys.stderr.write(f"{command.split()[0]}: command not found\n")
        sys.stdout.flush()


def main():
    shell_builtin = {"exit", "echo", "type", "pwd", "cd"}
    PATH = os.environ.get("PATH", "")
    path_dirs = PATH.split(":")
    HOME = os.environ.get("HOME", "/")

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        # Wait for user input
        try:
            command = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not command:
            continue

        # Tokenize input using custom split
        try:
            tokens = mysplit(command)
        except ValueError as e:
            sys.stdout.write(f"Error: {e}\n")
            sys.stdout.flush()
            continue

        # Handle command
        handle_command(tokens, path_dirs, HOME)


if __name__ == "__main__":
    main()
