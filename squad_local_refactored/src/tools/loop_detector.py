import re
from typing import List, Tuple, Optional


class LoopDetector:
    def __init__(self, max_history: int = 5, trigger_threshold: int = 3):
        self.max_history = max_history
        self.trigger_threshold = trigger_threshold
        # List of tuples (error_type, error_message, line_info)
        self.history: List[Tuple[str, str, str]] = []

    def register_error(self, error_str: str) -> bool:
        """
        Parses and registers an error message.
        Returns True if the identical error threshold is hit consecutively, otherwise False.
        """
        if not error_str:
            return False

        parsed = self._parse_error(error_str)
        if parsed:
            self.history.append(parsed)
            if len(self.history) > self.max_history:
                self.history.pop(0)

            return self._check_loop()
        return False

    def _parse_error(self, error_str: str) -> Optional[Tuple[str, str, str]]:
        lines = [line.strip() for line in error_str.splitlines() if line.strip()]
        if not lines:
            return None

        # Tracebacks put the exception type and details in the final line
        last_line = lines[-1]

        # Match "ExceptionName: Message Details"
        match = re.match(
            r"^([a-zA-Z_][a-zA-Z0-9_]*Error|[a-zA-Z_][a-zA-Z0-9_]*Exception):\s*(.*)$",
            last_line
        )

        if match:
            err_type = match.group(1)
            err_msg = match.group(2)

            # Search for line numbers in traceback text
            line_indicator = ""
            for line in lines:
                line_match = re.search(r"line\s+(\d+)", line, re.IGNORECASE)
                if line_match:
                    line_indicator = f"line {line_match.group(1)}"
                    break
            return (err_type, err_msg, line_indicator)

        # Fallback for plain outputs/errors
        return ("GeneralError", last_line, "")

    def _check_loop(self) -> bool:
        if len(self.history) < self.trigger_threshold:
            return False

        last_err = self.history[-1]
        consecutive_count = 1

        # Scan backwards to count consecutive identical errors
        for i in range(len(self.history) - 2, -1, -1):
            curr_err = self.history[i]
            if curr_err[0] == last_err[0] and curr_err[1] == last_err[1] and curr_err[2] == last_err[2]:
                consecutive_count += 1
            else:
                break

        return consecutive_count >= self.trigger_threshold

    def clear(self):
        self.history.clear()
