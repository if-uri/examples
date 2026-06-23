# Social scout scenarios

These scenarios exercise read-only browser work over URI commands: search,
filter, scroll, parse posts/comments, OCR the current page, take a snapshot, and
append local markdown files. They do not publish, comment, like, message, follow,
type into forms, or click social actions.

Prerequisite:

```bash
cd /home/tom/github/if-uri/examples/39-local-social-autonomy
google-chrome --remote-debugging-port=9222
```

The browser session should already be logged in. The runtime attaches through
CDP and writes captures under `.state/`.

## 1. Feed capture

Goal: save a slice of the home feed and visible comments.

Prompt:

```text
przejdz do feedu, przewin kilka razy, zapisz widoczne posty i komentarze
```

Command:

```bash
python3 uri_runtime.py --program programs/01-feed-save.json
```

Output:

```text
.state/captures-feed.md
```

## 2. Search, filter, save

Goal: search posts for a phrase, keep only matching visible content, and save it.

Prompt:

```text
wyszukaj posty o "system design", przefiltruj wynik i zapisz interesujace posty
```

Command:

```bash
python3 uri_runtime.py --program programs/02-search-filter-save.json --query "system design"
```

Output:

```text
.state/captures-search.md
```

## 3. Hashtag watch

Goal: open a hashtag/topic page, scroll, OCR image-heavy blocks, and save posts.

Prompt:

```text
obserwuj hashtag python, zapisz posty oraz tekst widoczny na obrazach
```

Command:

```bash
python3 uri_runtime.py --program programs/03-hashtag-watch.json --hashtag python
```

Output:

```text
.state/captures-hashtag.md
```

## 4. Saved posts archive

Goal: archive saved posts into local markdown.

Prompt:

```text
wejdz w zapisane posty, przewin liste i dopisz je do lokalnego archiwum
```

Command:

```bash
python3 uri_runtime.py --program programs/04-saved-posts-archive.json
```

Output:

```text
.state/captures-saved.md
```

## 5. Profile posts review

Goal: visit the configured profile activity page and capture recent posts.

Configure the path in `.env`:

```dotenv
LI_PROFILE_PATH=/in/tom-developer/recent-activity/
```

Prompt:

```text
przejdz do moich ostatnich aktywnosci i zapisz moje posty do markdown
```

Command:

```bash
python3 uri_runtime.py --program programs/05-profile-posts-review.json
```

Output:

```text
.state/captures-profile.md
```

## 6. Comments, OCR, snapshot

Goal: search a topic, capture posts/comments, OCR the main column, and store a
visual snapshot next to the markdown capture.

Prompt:

```text
wyszukaj "agentic workflow", zapisz posty, komentarze, OCR i screenshot
```

Command:

```bash
python3 uri_runtime.py --program programs/06-comments-ocr-snapshot.json --query "agentic workflow"
```

Outputs:

```text
.state/captures-comments-ocr.md
.state/scout-search-snapshot.png
```

## Useful URI building blocks

The programs above are plain JSON lists of URI steps. The core commands are:

```text
chrome://scout/navigate?url=https://www.linkedin.com/feed/
chrome://scout/search?scope=posts&q=__QUERY__
chrome://scout/filter?q=__QUERY__
chrome://scout/scroll?steps=5&delay=1.0
chrome://scout/extract_posts?min_text_len=80
chrome://scout/extract_comments?min_text_len=20
chrome://scout/ocr?selector=main
chrome://scout/snapshot?path=.state/snapshot.png
chrome://scout/append_markdown?path=.state/captures.md
```

Supported placeholders:

- `__QUERY__` - URL-encoded `--query` or fallback hashtag.
- `__HASHTAG__` - URL-encoded `--hashtag`.
- `__PROFILE_PATH__` - `.env` value `LI_PROFILE_PATH`.

