# noVNC desktop session — driven by an LLM from a natural-language intent

- **NL goal:** Open a terminal and run a command printing 'urirun ci check', then screenshot.
- **planner:** llm  ·  **action space:** 6 typed routes

## What the agent did, step by step

| # | URI | ran | ok | payload (LLM-filled from schema) | why |
|---|-----|-----|----|----------------------------------|-----|
| 0 | `desktop://novnc/session/command/start` | ✓ | ✓ | `{}` | Start the desktop session to perform actions. |
| 1 | `desktop://novnc/app/command/launch` | ✓ | ✓ | `{"command": "lxterminal"}` | Open a terminal to run the command. |
| 2 | `desktop://novnc/input/command/type` | ✓ | ✓ | `{"enter": true, "text": "echo 'urirun ci check'"}` | Type the command to print the required text and press enter. |
| 3 | `desktop://novnc/screen/query/screenshot` | ✓ | ✓ | `{"name": "final_output"}` | Capture the screenshot showing the command and its output. |
| 4 | `desktop://novnc/session/command/stop` | ✓ | ✓ | `{}` | Stop the desktop session as the goal is achieved. |

## Session screenshot(s)

![final_output.png](final_output.png)

## Was the NL intention realized?

- ✓ every planned step ran and succeeded
- ✓ a screenshot of the result was captured
- ✓ the typed text is visible on screen (OCR-confirmed)

**Verdict: YES — the NL intent became typed commands that ran on a real desktop.**
