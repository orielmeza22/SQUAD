import sys
import json
import io
import contextlib
import code


def main():
    # Stateful interactive console
    console = code.InteractiveConsole()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            data = json.loads(line)
            code_str = data.get("code", "")

            # Redirect stdout and stderr
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()

            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                # runsource compiles and runs multi-line code blocks statefully
                more = console.runsource(code_str)

            stdout_val = stdout_buf.getvalue()
            stderr_val = stderr_buf.getvalue()

            response = {
                "success": not more,
                "output": stdout_val,
                "error": stderr_val,
                "more": more
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception as e:
            sys.stdout.write(json.dumps({
                "success": False,
                "output": "",
                "error": str(e),
                "more": False
            }) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
