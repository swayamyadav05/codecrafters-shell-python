# Custom POSIX-Compliant Shell

A simple POSIX-compliant shell implemented in Python, created as part of the Codecrafters Shell challenge: https://app.codecrafters.io/courses/shell/overview

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Built-in Commands](#built-in-commands)
- [Command Parsing & Execution](#command-parsing--execution)
- [Input Editing & Tab Completion](#input-editing--tab-completion)
- [Installation & Requirements](#installation--requirements)
- [Usage & Example](#usage--examples)
- [Limitations & Future Improvements](#limitations--future-improvements)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Overview
This project implements a minimal POSIX-like shell in Python. It demonstrates:
- A REPL loop that reads user input, parses tokens (using `shlex`), handles redirections, and executes commands.
- Support for external executables found in the user’s `PATH`.
- Built-in commands (`cd`, `pwd`, `echo`, `type`, `exit`).
- I/O redirection for stdout (`>`, `>>`, `1>`, `1>>`) and stderr (`2>`, `2>>`).
- Tab completion of built-in commands and executables in `PATH` (using the `readline` module).
- Error handling for syntax errors, missing files, and command-not-found cases.

Along the way, this project deepened understanding of:
- Shell parsing and quoting rules (`shlex.split` to respect quoted strings).
- Process invocation (`subprocess.run`) and file descriptor redirection.
- Working with environment variables (`PATH`, `HOME`) and filesystem operations (`os.chdir`, `os.getcwd`).
- Building an interactive prompt (REPL) with graceful handling of EOF (Ctrl+D) and interrupts (Ctrl+C).
- Using Python’s `readline` for input editing and completion hooks.

## Features
- **Interactive prompt** with `$ ` prefix.
- **Built-in commands**:  
  - `cd [dir]`: change directory (with `~` expansion or no-arg → HOME).  
  - `pwd`: print current working directory.  
  - `echo [-n] [args...]`: print text, with optional `-n` to suppress trailing newline.  
  - `type [names...]`: report whether a given name is a shell builtin or an external executable (with path), or “not found”.  
  - `exit [status]`: exit the shell (only checks if `exit 0` to break; other codes can be extended).  
- **External commands**: search `$PATH` for executables, run via `subprocess.run`.
- **I/O Redirection**:  
  - `>` / `1>` (overwrite stdout), `>>` / `1>>` (append stdout).  
  - `2>` (overwrite stderr), `2>>` (append stderr).  
  - Handles syntax errors (e.g. missing filename).
- **Tab Completion**: using `readline`, completes built-ins and executable names in `PATH`. Displays matches in columns.
- **Robust parsing**: uses `shlex.split` to respect quoting and escapes.
- **Graceful exit**: handles `EOFError` / Ctrl+D and `KeyboardInterrupt` / Ctrl+C to avoid crashing.

## Built-in Commands
- **`cd [path]`**  
  Change the current working directory.  
  - No argument or `~` → `$HOME`.  
  - Relative paths are resolved against current directory; absolute paths accepted.  
  - Errors if directory does not exist.
- **`pwd`**  
  Print the absolute current working directory.
- **`echo [-n] args...`**  
  Print the arguments separated by spaces.  
  - `-n` suppresses the trailing newline.
- **`type names...`**  
  For each `name`, if it matches a shell builtin, prints:  
  ```
  name is a shell builtin
  ```  
  Otherwise, searches in `$PATH` and prints either:  
  ```
  name is /full/path/to/executable
  ```  
  or  
  ```
  name: not found
  ```
- **`exit [status]`**  
  If `exit 0`, breaks out of the REPL. (You may extend to handle other status codes or cleanup.)

## Command Parsing & Execution
1. **Read input** via `input().strip()`.  
2. **Tokenize**: `shlex.split(command)` handles quoted strings, escapes, etc.  
3. **Scan tokens** for redirection operators (`>`, `>>`, `1>`, `1>>`, `2>`, `2>>`).  
   - Record redirect filenames and modes (`w` or `a`), skip these tokens when building the command.  
   - On syntax error (e.g., missing filename), print a message to stderr and skip execution.  
4. **Determine command**:  
   - If no tokens after removing redirections: create (empty) files if redirection specified (mimicking shell), then continue.  
   - If first token is a builtin: call `handle_builtin(...)`, passing in redirection info, environment (`HOME`, `PATH` dirs).  
   - Else: search executable in `PATH` dirs via a helper `find_executable(cmd, path_dirs)`.  
     - If found: run with `subprocess.run`, redirecting stdout/stderr to files or inheriting.  
     - If not: print “command not found” to stderr (or redirected file).  
5. **Flush** stdout/stderr after each command.

## Input Editing & Tab Completion
- Uses Python’s `readline` module:
  - Defines `tab_completer(text, state)`: suggests builtins + executables whose names start with the typed text.
  - Defines `display_matches(...)` hook: prints possible completions in columns, then redraws prompt and current buffer.
  - Binds Tab key via `readline.parse_and_bind("tab: complete")`.
- This enhances usability similar to typical shells.

## Installation & Requirements
- **Requirements**:  
  - Python 3.6+ (tested on 3.8+).  
  - Modules: part of Python standard library (`os`, `sys`, `subprocess`, `shlex`, `readline`).
- **Clone repository**:
  ```bash
  git clone https://github.com/<your-username>/<repo-name>.git
  cd <repo-name>
  ```
- **Run shell**:
  ```bash
  python3 shell.py
  ```
  (Adjust file name/path if named differently.)
- **Exiting**: type `exit 0`, or press Ctrl+D on empty line, or Ctrl+C.

## Usage & Examples
Once running, you’ll see a prompt:
```
$ 
```
- **External command**:
  ```bash
  $ ls -l /usr/bin
  ```
- **Built-in commands**:
  ```bash
  $ pwd
  /home/user/path
  $ cd /tmp
  $ pwd
  /tmp
  $ echo Hello, world!
  Hello, world!
  $ echo -n No newline
  $ echo after
  after
  $ type ls cd fakecmd
  ls is /bin/ls
  cd is a shell builtin
  fakecmd: not found
  ```
- **Redirection**:
  ```bash
  $ echo "Hello" > out.txt
  $ cat out.txt
  Hello
  $ echo "Append" >> out.txt
  $ cat out.txt
  Hello
  Append
  $ echo "Error test" 2> err.txt
  $ cat err.txt
  Error test
  ```
- **Tab completion**: start typing a builtin or executable name, press Tab to complete or list matches.

## Limitations & Future Improvements
- **Pipelines (`|`)**: not currently supported. Could implement parsing to set up multiple processes with piping.
- **Background jobs (`&`)**: missing job control. Could fork subprocesses without waiting.
- **Quoting nuances**: relies on `shlex.split`, which handles most POSIX quoting but may differ in some corner cases.
- **Environment variable expansion**: currently only expands `~`. Could add `$VAR` expansion.
- **Signal handling**: basic Ctrl+C handling; could trap signals more gracefully.
- **Scripting**: no support for running commands from a script file.
- **History**: persistent command history across sessions.
- **Prompt customization**: allow PS1-like variables, colors.
- **Chaining (&&, ||)**: not implemented.
- **Aliases**: support shell aliases.
- **Globbing**: wildcard expansion (`*`, `?`) not implemented.
- **Configuration**: read config files (e.g., `.rc`).
- **Enhanced `exit` status handling**: propagate exit codes, allow `exit 1`, etc.
- **Windows compatibility**: currently Unix-like environment assumed.

Contributions or suggestions for these enhancements are welcome!

## Project Structure
```
.
├── app
   ├── main.py           # Main Python script implementing the shell REPL
├── README.md            # This file
└── Others               # Config file from codecraft
```
- If you rename `main.py`, update instructions accordingly.

## Contributing
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit changes with descriptive messages.
4. Open a Pull Request explaining the changes.
5. Ensure that existing functionality is not broken; test built-ins, external commands, redirections, and tab completion.

Please file issues for bugs or feature requests.

## Acknowledgments
- The Codecrafters Shell challenge: https://app.codecrafters.io/courses/shell/overview  
- Python standard library: `shlex`, `subprocess`, `readline`.
