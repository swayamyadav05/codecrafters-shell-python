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


def handle_builtin(
    cmd, tokens, redirect_stdout, redirect_stderr, home_dir, path_dirs, shell_builtins
):
    """Execute a built-in command with optional stdout and stderr redirection."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    f_out = None
    f_err = None

    try:
        # Open files for redirection
        if redirect_stdout:
            f_out = open(redirect_stdout, "w")
            sys.stdout = f_out
        if redirect_stderr:
            f_err = open(redirect_stderr, "w")
            sys.stderr = f_err

        if cmd == "echo":
            sys.stdout.write(" ".join(tokens[1:]) + "\n")
        elif cmd == "pwd":
            sys.stdout.write(os.getcwd() + "\n")
        elif cmd == "cd":
            path = tokens[1] if len(tokens) > 1 else ""
            if path == "~" or not path:
                new_path = home_dir
            else:
                new_path = os.path.expanduser(path)
                if not os.path.isabs(new_path):
                    new_path = os.path.abspath(new_path)
            if os.path.isdir(new_path):
                os.chdir(new_path)
            else:
                sys.stderr.write(f"cd: {path}: No such file or directory\n")
        elif cmd == "type":
            for cmd_name in tokens[1:]:
                if cmd_name in shell_builtins:
                    sys.stdout.write(f"{cmd_name} is a shell builtin\n")
                else:
                    cmd_path = find_executable(cmd_name, path_dirs)
                    if cmd_path:
                        sys.stdout.write(f"{cmd_name} is {cmd_path}\n")
                    else:
                        sys.stdout.write(f"{cmd_name}: not found\n")
    except Exception as e:
        sys.stderr.write(f"Error executing built-in command: {e}\n")
    finally:
        # Restore original stdout and stderr
        if f_out is not None:
            sys.stdout = original_stdout
            f_out.close()
        if f_err is not None:
            sys.stderr = original_stderr
            f_err.close()


def main():
    shell_builtin = {"exit", "echo", "type", "pwd", "cd"}
    PATH = os.environ.get("PATH", "")
    path_dirs = PATH.split(":")
    HOME = os.environ.get("HOME", "/")

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        try:
            command = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not command:
            continue

        try:
            tokens = shlex.split(command)
        except ValueError as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()
            continue

        redirect_stdout = None
        redirect_stderr = None
        new_tokens = []
        i = 0
        error_occurred = False

        # Parse tokens for redirection operators
        while i < len(tokens):
            token = tokens[i]
            if token in (">", "1>"):
                if i + 1 >= len(tokens):
                    sys.stderr.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stdout = tokens[i + 1]
                i += 2
            elif token == "2>":
                if i + 1 >= len(tokens):
                    sys.stderr.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stderr = tokens[i + 1]
                i += 2
            else:
                new_tokens.append(token)
                i += 1

        if error_occurred:
            sys.stderr.flush()
            continue

        if not new_tokens:
            # Handle empty command with redirections
            if redirect_stdout:
                try:
                    with open(redirect_stdout, "w"):
                        pass
                except Exception as e:
                    sys.stderr.write(f"Error creating file: {e}\n")
            if redirect_stderr:
                try:
                    with open(redirect_stderr, "w"):
                        pass
                except Exception as e:
                    sys.stderr.write(f"Error creating file: {e}\n")
            continue

        cmd = new_tokens[0]

        # Handle exit command
        if cmd == "exit":
            if len(new_tokens) == 2 and new_tokens[1] == "0":
                break
            continue

        # Handle built-in commands
        if cmd in shell_builtin:
            handle_builtin(
                cmd,
                new_tokens,
                redirect_stdout,
                redirect_stderr,
                HOME,
                path_dirs,
                shell_builtin,
            )
            sys.stdout.flush()
            sys.stderr.flush()
            continue

        # Handle external commands
        cmd_path = find_executable(cmd, path_dirs)
        if cmd_path:
            stdout_handle = None
            stderr_handle = None
            try:
                if redirect_stdout:
                    stdout_handle = open(redirect_stdout, "w")
                if redirect_stderr:
                    stderr_handle = open(redirect_stderr, "w")

                subprocess.run(
                    new_tokens,
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    executable=cmd_path,
                )
            except Exception as e:
                error_msg = f"Error executing command: {e}\n"
                if redirect_stderr:
                    try:
                        with open(redirect_stderr, "a") as f:
                            f.write(error_msg)
                    except Exception as e:
                        sys.stderr.write(f"Error writing to stderr file: {e}\n")
                        sys.stderr.write(error_msg)
                else:
                    sys.stderr.write(error_msg)
            finally:
                if stdout_handle is not None:
                    stdout_handle.close()
                if stderr_handle is not None:
                    stderr_handle.close()
        else:
            error_message = f"{cmd}: command not found\n"
            if redirect_stderr:
                try:
                    with open(redirect_stderr, "w") as f:
                        f.write(error_message)
                except Exception as e:
                    sys.stderr.write(f"Error writing to stderr file: {e}\n")
                    sys.stderr.write(error_message)
            else:
                sys.stderr.write(error_message)
        sys.stdout.flush()
        sys.stderr.flush()


if __name__ == "__main__":
    main()
