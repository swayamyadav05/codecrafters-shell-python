import sys
import os
import subprocess
import shlex
import readline


def find_executable(cmd, path_dirs):
    """Search for an executable command in the directories listed in PATH."""
    for path in path_dirs:
        cmd_path = os.path.join(path, cmd)
        if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
            return cmd_path
    return None


def handle_builtin(
    cmd,
    tokens,
    stdout_filename,
    stdout_mode,
    stderr_filename,
    stderr_mode,
    home_dir,
    path_dirs,
    shell_builtins,
):
    """Execute a built-in command with optional stdout and stderr redirection."""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    f_out = None
    f_err = None

    try:
        # Open files for redirection if requested
        if stdout_filename:
            f_out = open(stdout_filename, stdout_mode)
            sys.stdout = f_out
        if stderr_filename:
            f_err = open(stderr_filename, stderr_mode)
            sys.stderr = f_err

        if cmd == "echo":
            args = tokens[1:]
            newline = True
            # Handle -n option if provided
            if args and args[0] == "-n":
                newline = False
                args = args[1:]
            output = " ".join(args)
            if newline:
                output += "\n"
            sys.stdout.write(output)
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
        # Restore original stdout and stderr and close files
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

    # Global variables to keep track of completion attempts
    last_matches = []
    completion_attempt = 0

    def tab_completer(text, state):
        matches = []
        # Check built-in commands (append a trailing space)
        for cmd in shell_builtin:
            candidate = cmd + " "
            if candidate.startswith(text):
                matches.append(candidate)
        # Check external executables in PATH directories
        for path_dir in path_dirs:
            try:
                for filename in os.listdir(path_dir):
                    filepath = os.path.join(path_dir, filename)
                    if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                        candidate = filename + " "
                        if candidate.startswith(text):
                            matches.append(candidate)
            except (FileNotFoundError, PermissionError):
                continue
        # Remove duplicates and sort
        matches = sorted(list(set(matches)))
        if state < len(matches):
            return matches[state]
        else:
            return None

    # Custom display hook for completions.
    # On the first TAB press (when the matches list changes), ring a bell.
    # On the second consecutive TAB press (with the same prefix),
    # print the list of matches separated by two spaces, then reprint the prompt.
    def display_matches(substitution, matches, longest_match_length):
        nonlocal last_matches, completion_attempt
        # If the matches list has changed, reset the counter.
        if matches != last_matches:
            completion_attempt = 1
            last_matches = matches
            sys.stdout.write("\a")  # ring the bell
            sys.stdout.flush()
        else:
            completion_attempt += 1
            if completion_attempt >= 2:
                # Print the list of matches on the next line
                sys.stdout.write("\n" + "  ".join(matches) + "\n")
                # Reprint the prompt and the current line buffer
                prompt = "$ "
                current_line = readline.get_line_buffer()
                sys.stdout.write(prompt + current_line)
                sys.stdout.flush()

    readline.set_completer(tab_completer)
    readline.set_completion_display_matches_hook(display_matches)
    readline.parse_and_bind("tab: complete")

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

        # Reset our completion tracking variables for each new command input.
        last_matches = []
        completion_attempt = 0

        # Parse redirection tokens (">", "1>", ">>", "1>>", "2>", "2>>")
        redirect_stdout = None
        stdout_mode = "w"  # default is truncate
        redirect_stderr = None
        stderr_mode = "w"
        new_tokens = []
        i = 0
        error_occurred = False

        while i < len(tokens):
            token = tokens[i]
            if token in (">", "1>"):
                if i + 1 >= len(tokens):
                    sys.stderr.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stdout = tokens[i + 1]
                stdout_mode = "w"
                i += 2
            elif token in (">>", "1>>"):
                if i + 1 >= len(tokens):
                    sys.stderr.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stdout = tokens[i + 1]
                stdout_mode = "a"
                i += 2
            elif token == "2>":
                if i + 1 >= len(tokens):
                    sys.stderr.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stderr = tokens[i + 1]
                stderr_mode = "w"
                i += 2
            elif token == "2>>":
                if i + 1 >= len(tokens):
                    sys.stderr.write(f"Syntax error: no filename after '{token}'\n")
                    error_occurred = True
                    break
                redirect_stderr = tokens[i + 1]
                stderr_mode = "a"
                i += 2
            else:
                new_tokens.append(token)
                i += 1

        if error_occurred:
            sys.stderr.flush()
            continue

        if not new_tokens:
            # In case the command line only contained redirections, create the files.
            if redirect_stdout:
                try:
                    with open(redirect_stdout, stdout_mode):
                        pass
                except Exception as e:
                    sys.stderr.write(f"Error creating file: {e}\n")
            if redirect_stderr:
                try:
                    with open(redirect_stderr, stderr_mode):
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
                stdout_mode,
                redirect_stderr,
                stderr_mode,
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
                    stdout_handle = open(redirect_stdout, stdout_mode)
                if redirect_stderr:
                    stderr_handle = open(redirect_stderr, stderr_mode)

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
                        with open(redirect_stderr, stderr_mode) as f:
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
                    with open(redirect_stderr, stderr_mode) as f:
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
