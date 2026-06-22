# Sterowanie zdalną maszyną przez URI (urirun mesh)

Jak z hosta (`studio`) sterować zdalnym węzłem (`lenovo` / `192.168.188.201:8765`)
przez adresy URI, jak włączyć **tryb bezpieczny**, i jak przez URI kontrolować
ustawienia samego węzła. Wszystkie komendy poniżej zostały sprawdzone na żywo.

---

## 0. Trzy nazwy jednej maszyny — uważaj

Jedna fizyczna maszyna ma w tym secie **trzy** różne nazwy:

| Nazwa | Skąd | Gdzie jej używasz |
|---|---|---|
| `lenovo`  | `hostname` systemu (zwraca `env health`) | nigdzie w URI |
| `laptop`  | **nazwa węzła** (`node serve --name`) | **w adresach URI** (`env://laptop/...`) |
| `officepc`| nazwa wpisu w `~/.urirun-host/mesh.json` | w `urirun host …` (np. `host deploy officepc`) |

→ Trasy adresujesz **nazwą węzła** (`laptop`), a komendy `urirun host …`
**nazwą z mesha** (`officepc`). `host deploy lenovo` zawiedzie („unknown node").
Najlepiej ujednolicić: `--name officepc` przy starcie węzła.

---

## 1. Co węzeł udostępnia (odczyt przez HTTP)

```bash
B=http://192.168.188.201:8765
curl -s $B/health          # nazwa, wersja, execute, deploy, keyAuth, keyCount
curl -s $B/routes          # lista tras URI + ich inputSchema
curl -s $B/errors          # ostatnie błędy (error:// adresy)
```

Aktualnie 7 tras (wszystkie `safe`):
```
env://laptop/runtime/query/health        # hostname/platform/python
log://laptop/session/command/write  {text}
log://laptop/session/query/recent   {limit}
proc://laptop/process/query/list    {limit}
shell://laptop/command/date
shell://laptop/command/uname
shell://laptop/command/which        {binary}
```

---

## 2. Sterowanie przez URI (POST /run)

Każde sterowanie to `POST /run` z `{"uri": …, "payload": …}`:

```bash
B=http://192.168.188.201:8765
run(){ curl -s -X POST $B/run -H 'Content-Type: application/json' -d "$1"; }

run '{"uri":"shell://laptop/command/date","payload":{}}'
run '{"uri":"shell://laptop/command/which","payload":{"binary":"python3"}}'
run '{"uri":"proc://laptop/process/query/list","payload":{"limit":5}}'
run '{"uri":"log://laptop/session/command/write","payload":{"text":"hello from studio"}}'
```

Odpowiedź ma `decision.allowed`, `result.stdout`/`result.value` i `ok`.

### To samo z biblioteki / mesha (Python)

```python
import os, json
from urirun.runtime import v2_service
os.environ["URI_SERVICE_MAP"] = json.dumps({"laptop": "http://192.168.188.201:8765"})
env = v2_service.call("shell://laptop/command/uname", {}, registry=reg, mode="execute")
print(env["ok"], env["result"])
```

### To samo przez naturalny język (LLM → flow)

```bash
urirun host ask "na laptop pokaż datę i listę procesów"     # NL → URI-flow → wykonanie
# albo self-naprawiający się flow z examples/23-llm-flow-repair/
```

---

## 3. Tryb bezpieczny — domknięcie otwartego `/run`

**Problem:** `keyAuth:true` chroni tylko `POST /deploy`. `POST /run` jest nadal
**otwarty** — każdy w LAN może wykonać dozwolone trasy (zweryfikowane: `/run`
zwraca 200 bez żadnego tokenu). Trzeba jawnie włączyć `--require-run-auth`.

### Włączenie na węźle (na maszynie `.201`)

Tryb tokenowy (najprostszy, klient mesha go wspiera):
```bash
urirun node serve --name officepc --host 0.0.0.0 --port 8765 --execute \
  --allow 'shell://*' --allow 'env://*' --allow 'proc://*' --allow 'log://*' \
  --admin-token 'MOCNY_TOKEN' --require-run-auth
```
Przez instalator `get.urirun.com/node.sh`:
```bash
URIRUN_NODE_REQUIRE_RUN_AUTH=1 \
  curl -fsSL https://get.urirun.com/node.sh | bash -s -- --admin-token 'MOCNY_TOKEN'
```
Instalator wypisze `!! SECURITY …`, jeśli węzeł jest wystawiony na LAN bez bramki `/run`.

### Wołanie z hosta (`studio`) po włączeniu

```bash
export URIRUN_RUN_TOKEN='MOCNY_TOKEN'      # klient dokłada nagłówek X-Urirun-Token
urirun host ask "na officepc pokaż uname"  # teraz przechodzi; bez tokenu → 403
```
Surowo:
```bash
curl -s -X POST $B/run -H 'X-Urirun-Token: MOCNY_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"uri":"shell://laptop/command/uname","payload":{}}'
```

Zachowanie (zweryfikowane live, in-process):
| Żądanie `/run` | Wynik |
|---|---|
| bez tokenu | **403** |
| zły token | **403** |
| poprawny token | **200** + wynik |
| klient `v2_service` bez `URIRUN_RUN_TOKEN` | `ok:false` |
| klient `v2_service` z `URIRUN_RUN_TOKEN` | `ok:true` |

> Tryb kluczowy (`--key-auth`) chroni `/deploy` podpisem ed25519 (enrollment
> `uri-copy-id`, TOFU). Bramkowanie `/run` podpisem klucza po stronie klienta
> nie jest jeszcze podpięte — do `/run` użyj trybu **tokenowego** powyżej.

---

## 4. Kontrola USTAWIEŃ węzła przez URI (re-provisioning)

Czym węzeł steruje (trasy, polityka `allow`, nazwa, kod handlerów) zmieniasz
**przez `POST /deploy`** — to URI-natywne provisioning po meshu, podpisane kluczem
(bez SSH). Wymaga `--key-auth` lub `--admin-token` na węźle.

```bash
# 1) jednorazowo zarejestruj swój klucz (TOFU na świeżym węźle):
uri-copy-id 192.168.188.201            # lub: urirun host copy-id officepc -i ~/.ssh/id_ed25519

# 2) wgraj nowy zestaw tras / politykę / kod (zmiana ustawień węzła):
urirun host deploy officepc \
  --bindings office.json \
  --allow 'shell://*' --allow 'kvm://*' \
  --code bridge.py \
  --identity ~/.ssh/id_ed25519
```
`/deploy` hot-swapuje serwowany rejestr, listę `allow` i nazwę **bez restartu**.
Stan po zmianie odczytasz znów przez `GET /routes` i `env://<nazwa>/runtime/query/health`.

Czego **nie** zmienisz przez `/deploy`: bind/port/flagi auth (`--require-run-auth`,
`--key-auth`) — to parametry startu procesu; zmiana wymaga restartu `node serve`
(lokalnie na `.201` lub przez usługę systemd z instalatora).

---

## 5. Higiena

- Nie zostawiaj otwartego `/run` z `shell://*` na LAN — włącz `--require-run-auth`
  albo zawęź `--allow`, albo bind `127.0.0.1`.
- Ujednolić nazwę węzła (`--name officepc`), żeby URI i `urirun host …` się zgadzały.
- Token trzymaj poza repo (env / `~/.pypirc`-style), nie w plikach śledzonych.
