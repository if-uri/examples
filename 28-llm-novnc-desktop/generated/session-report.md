# noVNC desktop session — driven by an LLM from a natural-language intent

- **NL goal:** Open a terminal on the desktop and run a command that prints 'urirun agent was here', then take a screenshot of the result.
- **planner:** llm  ·  **action space:** 6 typed routes

## What the agent did, step by step

| # | URI | ran | ok | payload (LLM-filled from schema) | why |
|---|-----|-----|----|----------------------------------|-----|
| 0 | `desktop://novnc/session/command/start` | ✓ | ✓ | `{}` | Start the desktop session to perform actions. |
| 1 | `desktop://novnc/app/command/launch` | ✓ | ✓ | `{"command": "lxterminal"}` | Open a terminal window on the desktop. |
| 2 | `desktop://novnc/input/command/type` | ✓ | ✓ | `{"enter": true, "text": "echo 'urirun agent was here'"}` | Type the command to print the message and press enter. |
| 3 | `desktop://novnc/screen/query/screenshot` | ✓ | ✓ | `{"name": "result_screenshot"}` | Capture the screenshot showing the command output. |
| 4 | `desktop://novnc/session/command/stop` | ✓ | ✓ | `{}` | Stop the desktop session. |

## Session screenshot(s)

![result_screenshot.png](result_screenshot.png)

## Was the NL intention realized?

- ✓ every planned step ran and succeeded
- ✓ a screenshot of the result was captured
- ✓ the typed text is visible on screen (OCR-confirmed)

**Verdict: YES — the NL intent became typed commands that ran on a real desktop.**
