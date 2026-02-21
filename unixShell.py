#! /usr/bin/env python3
# unixShell.py
import os, sys, re

def execute_command(args):
    path_list = [args[0]] if "/" in args[0] else [f"{d}/{args[0]}" for d in re.split(":", os.environ.get('PATH', ""))]
    
    for program in path_list:
        try:
            os.execve(program, args, os.environ)
        except FileNotFoundError:
            continue
        except OSError as e:
            if e.errno == 8: # Exec format error
                new_args = ["/bin/sh"] + args
                os.execve("/bin/sh", new_args, os.environ)
            else:
                raise e

    os.write(2, f"{args[0]}: command not found\n".encode())
    sys.exit(1)

def handle_redirection(args):
    """Processes < and > and returns cleaned args."""
    if ">" in args:
        idx = args.index(">")
        os.close(1)
        os.open(args[idx+1], os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
        os.set_inheritable(1, True)
        args = args[:idx]
    if "<" in args:
        idx = args.index("<")
        os.close(0)
        os.open(args[idx+1], os.O_RDONLY)
        os.set_inheritable(0, True)
        args = args[:idx]
    return args

def run_pipe(commands):
    """Handles N number of pipes through recursion."""
    # Base case: only one command left
    if len(commands) == 1:
        execute_command(handle_redirection(commands[0].split()))

    pr, pw = os.pipe()
    rc = os.fork()

    if rc == 0:  # Child: Left side of the current pipe
        os.dup2(pw, 1) # Send output to the pipe
        os.close(pr)
        os.close(pw)
        execute_command(handle_redirection(commands[0].split()))
    else:        # Parent: Right side of the current pipe
        os.dup2(pr, 0) # Read input from the pipe
        os.close(pr)
        os.close(pw)
        run_pipe(commands[1:]) # Recursive call with the rest of the commands

def main():
    while True:
        # 1. Handle Prompt properly for the tester
        ps1 = os.environ.get("PS1", "$ ")
        os.write(1, ps1.encode())
        sys.stdout.flush() # Ensure it appears before we wait for input
        
        line = sys.stdin.readline()
        if not line: # EOF (Tester finishes or Ctrl+D)
            break

        line = line.strip()
        if not line:
            continue

        # Check for background execution
        background = False
        if line.endswith("&"):
            background = True
            line = line[:-1].strip()
        # Handling pipes
        if "|" in line:
            parts = line.split("|")
            rc = os.fork()
            if rc == 0:
                run_pipe(parts)
            else:
                os.wait() # Parent waits for the entire pipe chain to finish
            continue

        args = line.split()
        if args[0] == "exit":
            break
        elif args[0] == "cd":
            try:
                os.chdir(args[1])
            except:
                os.write(2, b"cd: directory not found\n")
            continue

        rc = os.fork()
        if rc == 0:
            args = handle_redirection(args)
            execute_command(args)
        else:
            if not background:
                _, status = os.wait()
                code = os.waitstatus_to_exitcode(status)
                if code != 0:
                    os.write(2, f"Program terminated with exit code {code}.\n".encode())

if __name__ == "__main__":
    main()