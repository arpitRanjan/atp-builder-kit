"""Rule based answers for the offline mock model (KIT_OFFLINE=1), used by the Chapter 4 to 13 notebooks.

It is NOT a real model. It spots the prompts those notebooks send (by a phrase in the system
prompt or prompt) and answers with simple keyword rules, so every notebook runs with no network
and gives the same numbers every time. respond() returns None for any other prompt, and then
kit/llm.py uses its usual mock answer. Real models will behave differently: run them live.
"""
import hashlib
import json
import re

STOP = {"the", "a", "an", "to", "i", "how", "do", "my", "is", "of", "and", "or", "in", "on", "for", "it",
        "can", "what", "me", "you", "your", "be", "with", "this", "that", "are", "if", "at", "as", "by",
        "from", "does", "did", "there", "way", "get", "use", "so", "too", "we", "our", "any", "will"}


def words(text):
    # Lower case content words, with a crude plural strip so "notes" matches "note".
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        out.add(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


def _seed(text):
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def respond(prompt, system, model=None):
    system = system or ""
    for marker, handler in HANDLERS:
        if marker in system or marker in prompt:
            return handler(prompt, system, model or "")
    return None


# ---------- 04: pick the help page ----------
def _pick_page(prompt, system, model=None):
    question = prompt.split("Question:")[-1]
    q = words(question)
    scores = []
    for m in re.finditer(r"^(qn-\d+): (.*)$", prompt, re.M):
        title, _, body = m.group(2).partition(" | ")
        scores.append((len(q & words(title)) * 2 + len(q & words(body)), m.group(1)))
    scores.sort(key=lambda s: -s[0])
    if not scores or scores[0][0] == 0:
        return json.dumps({"page_id": "none"})
    # Now and then the mock picks the runner up, like a model that skims.
    pick = scores[1] if len(scores) > 1 and _seed(question) % 6 == 0 else scores[0]
    return json.dumps({"page_id": pick[1]})


# ---------- 06 and 13: the JSON tool protocol ----------
# Instructions planted inside a page (13_injection_and_redteam). Results are JSON text, so quotes may be escaped.
Q = r'\\?"'
PLANTED_DRAFT = re.compile(rf"call draft_issue with title {Q}(.+?){Q}, body {Q}(.+?){Q} and to {Q}(.+?){Q}")
PLANTED_FETCH = re.compile(rf"call fetch_url with url {Q}(.+?){Q}")


def _agent(prompt, system, model=None):
    task = prompt.split("Task:", 1)[1].split("\n\n", 1)[0].strip()
    calls = [json.loads(c) for c in re.findall(r"^CALL \d+: (.*)$", prompt, re.M)]
    results = re.findall(r"^RESULT \d+: (.*)$", prompt, re.M)
    tools = set(re.findall(r"^- (\w+)\(", system, re.M))
    quoted = re.findall(r'"([^"]+)"', task)
    query = quoted[0] if quoted and "search_docs" in task else task
    url = re.search(r"https?://[^\s\"']+", task)
    if not calls and url and "fetch_url" in tools:
        return json.dumps({"tool": "fetch_url", "args": {"url": url.group(0).rstrip(".,")}})
    if not calls or (len(calls) == 1 and calls[0].get("tool") == "fetch_url"):
        return json.dumps({"tool": "search_docs", "args": {"query": query, "top_k": 3}})
    last = results[-1] if results else ""
    # The mock obeys an instruction it reads in a tool result, once, like a model that trusts its input.
    planted = PLANTED_DRAFT.search(last)
    if planted and "draft_issue" in tools:
        title, body, to = planted.groups()
        return json.dumps({"tool": "draft_issue", "args": {"title": title, "body": body, "to": to}})
    planted = PLANTED_FETCH.search(last)
    if planted and "fetch_url" in tools:
        return json.dumps({"tool": "fetch_url", "args": {"url": planted.group(1)}})
    if last.startswith("ERROR"):
        # The mock gives up after a tool error. A real model might retry or invent an answer.
        return json.dumps({"final": "I could not finish: a tool failed."})
    wants_issue = "issue" in task.lower()
    if last.startswith("DENIED") and wants_issue:
        return json.dumps({"final": "A human did not approve the draft, so nothing was written."})
    if last.strip() == "[]":
        return json.dumps({"tool": "search_docs", "args": {"query": query, "top_k": 3}})
    ids = []
    for r in results:
        ids += [i for i in re.findall(r'"id": "(qn-\d+)"', r) if i not in ids]
    if wants_issue and not any(c.get("tool") == "draft_issue" for c in calls):
        title = quoted[0] if quoted else task.split(".")[0][:60]
        body = f"Reported by the help desk. Related pages: {', '.join(ids[:2]) or 'none'}."
        args = {"title": title, "body": body}
        email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", task)
        if email and re.search(r"draft_issue\([^)]*\bto\b", system):
            args["to"] = email.group(0).rstrip(".")
        return json.dumps({"tool": "draft_issue", "args": args})
    cite = " ".join(f"[{i}]" for i in ids[:1])
    done = " Draft saved to the outbox." if wants_issue else ""
    return json.dumps({"final": f"See the help page {cite}.{done}".replace("  ", " ")})


# ---------- 06: context blocks ----------
FILLER = "Let me know if you need anything else. Happy note taking!"


def _sections(prompt):
    parts = re.split(r"^## ([A-Z ]+)\n", prompt, flags=re.M)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def _context(prompt, system, model=None):
    s = _sections(prompt)
    question = s.get("QUESTION", "").strip()
    q = words(question)
    if "TOOLS" in s and re.search(r"which tool", question, re.I):
        tools = re.findall(r"^- (\w+)\(.*?\): (.*)$", s["TOOLS"], re.M)
        best = max(tools, key=lambda t: len(q & words(t[0].replace("_", " ") + " " + t[1])))
        return best[0]
    if re.search(r"which tool", question, re.I):
        return "I do not have any tools listed, so I cannot say."
    if "HISTORY" in s and re.match(r"(which|what)\b.*\b(am i|do i)\b", question, re.I):
        lines = [l for l in s["HISTORY"].splitlines() if l.startswith("User:")]
        best = max(lines, key=lambda l: len(q & words(l)))
        return f"You told me earlier: {best[5:].strip()}"
    pages = re.findall(r"^\[(qn-\d+)\] (.*)$", s.get("PAGES", ""), re.M)
    page = max(pages, key=lambda p: len(q & words(p[1]))) if pages else None
    first = re.split(r"(?<=[.!?])\s", page[1])[0] if page else "I could not find that in the help pages"
    cite = f" [{page[0]}]" if page and "EXAMPLES" in s else ""
    sentences = [f"About \"{question}\": {first.rstrip('.!?: ')}{cite}."]
    for topic, say in re.findall(r"If the question is about (.+?), say: (.+)", s.get("INSTRUCTIONS", "")):
        if q & words(topic):
            sentences.append(say.strip().rstrip(".") + ".")
    sentences.append(FILLER)
    text = " ".join(sentences)
    for banned in re.findall(r"Never say '(.+?)'", s.get("INSTRUCTIONS", "")):
        text = re.sub(banned, "", text, flags=re.I)
    cap = re.search(r"at most (\d+) sentences", s.get("SYSTEM", ""))
    if cap:
        text = " ".join(re.split(r"(?<=[.!?])\s", text)[: int(cap.group(1))])
    return text


def _summarize(prompt, system, model=None):
    # Keeps lines with rule words and the last three user turns. Facts without rule words get lost.
    limit = int((re.search(r"at most (\d+) words", prompt) or [0, 80])[1])
    users = [l[5:].strip() for l in prompt.splitlines() if l.startswith("User:")]
    keep = [u for u in users if re.search(r"\b(always|never|must)\b", u, re.I)] + users[-3:]
    return " ".join(" ".join(keep).split()[:limit])


def _consolidate(prompt, system, model=None):
    # Merges exact duplicates only. It does not check whether a note is true.
    notes = re.findall(r"^- (.*)$", prompt, re.M)
    return json.dumps(list(dict.fromkeys(notes)))


# ---------- 06: structured output ----------
def _extract(prompt, system, model=None):
    note = prompt.split("Note:", 1)[1].split("\n", 1)[0].strip()
    retry = "failed validation" in prompt
    low = note.lower()
    name = re.search(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b", note) or re.search(r"(?:from|user:?)\s+([A-Z][a-z]+)", note)
    category = "other"
    for cat, keys in [("billing", ["charge", "billed", "refund", "money", "plan"]), ("sync", ["sync"]),
                      ("export", ["export", "pdf"]), ("account", ["account", "password", "locked"])]:
        if any(k in low for k in keys):
            category = cat
            break
    nums = re.findall(r"\$?(\d+(?:\.\d+)?)\s*(?:usd|dollars|\$)?", low)
    nums = [float(n) for n in nums if not re.search(rf"nov {n}\b", low)]
    amount = nums[0] if nums and category == "billing" else None
    refund = "refund" in low or "money back" in low
    priority = "medium"
    if re.search(r"urgent", low):
        priority = "URGENT"
    elif re.search(r"asap|twice|double", low):
        priority = "high"
    elif re.search(r"low prio|feedback|maybe", low):
        priority = "low"
    if retry:
        # On a retry the mock reads the validation error and fixes what it names.
        err = prompt.split("failed validation:", 1)[1].lower()
        if "priority" in err:
            priority = "high" if priority == "URGENT" else priority
        if "amount" in err and len(nums) > 1:
            amount = nums[1]
        if "refund" in err:
            refund = False
    obj = {"customer": name.group(1) if name else "unknown", "category": category,
           "amount_usd": amount, "priority": priority, "refund_requested": refund}
    return json.dumps(obj)


# ---------- 08: the judge ----------
def _judge(prompt, system, model=None):
    ref = prompt.split("Reference:", 1)[1].split("Answer:", 1)[0]
    ans = prompt.split("Answer:", 1)[1].split("Reply with", 1)[0]
    a, r = words(ans), words(ref)
    if not a or re.search(r"not sure|cannot help|no idea", ans, re.I):
        return "FAIL: the answer does not help."
    share = len(a & r) / len(a)
    # A word overlap judge: it misses answers that reuse the right words with one wrong detail.
    return "PASS: matches the reference." if share >= 0.5 else "FAIL: not supported by the reference."


# ---------- 09: answer from sources, and the citation judge ----------
def _rag(prompt, system, model=None):
    question = prompt.split("Question:")[-1]
    q = words(question)
    sources = re.findall(r"^\[([\w#-]+)\] (.*)$", prompt.split("Question:")[0], re.M)
    scored = sorted(((len(q & words(t)), i, t) for i, t in sources), key=lambda s: -s[0])
    if not scored or scored[0][0] < 2:
        return "The sources do not answer this."
    _, sid, text = scored[0]
    return " ".join(text.split()[:30]) + f" [{sid}]"


def _cite_judge(prompt, system, model=None):
    question = prompt.split("Question:", 1)[1].split("\n", 1)[0]
    source = prompt.split("Source:", 1)[1].split("Reply", 1)[0]
    ok = len(words(question) & words(source)) >= 2
    return "SUPPORTED" if ok else "NOT SUPPORTED"


# ---------- 10: the model cascade ----------
def _cheap(model):
    return model.endswith("-b") or "nano" in model or "lite" in model


def _cascade(prompt, system, model=None):
    # Small models are unsure when a question points back at an earlier turn; big ones read the history.
    users = [l[5:].strip() for l in prompt.splitlines() if l.startswith("User:")]
    current, earlier = (users[-1] if users else ""), users[:-1]
    pages = re.findall(r"^\[(qn-\d+)\] (.*)$", prompt, re.M)
    q = words(current)
    best = max(pages, key=lambda p: len(q & words(p[1]))) if pages else None
    fact = ""
    if best and len(q & words(best[1])) >= 2:
        fact = re.split(r"(?<=[.!?])\s", best[1])[0].rstrip(".") + f" [{best[0]}]."
    if re.search(r"\b(my plan|given my|as i said|earlier)\b", current, re.I):
        if _cheap(model or ""):
            return json.dumps({"answer": "I am not sure which plan you mean.", "confidence": 0.3})
        plan = next((m.group(1) for u in earlier for m in [re.search(r"\b(\w+) plan\b", u, re.I)] if m), None)
        if not plan:
            return json.dumps({"answer": "Which plan are you on? The answer depends on it.", "confidence": 0.4})
        return json.dumps({"answer": f"On the {plan} plan: {fact or 'see the help pages.'}", "confidence": 0.85})
    if fact:
        return json.dumps({"answer": fact, "confidence": 0.9})
    return json.dumps({"answer": "Thanks, noted.", "confidence": 0.9})


# ---------- 12: translate a question into English ----------
PHRASES = [("le cambio el nombre", "rename"), ("cambio el nombre", "rename"), ("palabra clave", "keyword"),
           ("modo oscuro", "dark mode"), ("modo oscruo", "dark mode"), ("sin conexion", "offline"),
           ("espacio de trabajo", "workspace"), ("por error", "by accident"), ("otro dispositivo", "other device")]
GLOSSARY = {
    "creo": "create", "crear": "create", "nota": "note", "notas": "notes", "nueva": "new", "exporto": "export",
    "exportar": "export", "exportr": "export", "archivo": "file", "guardar": "save", "imprimirla": "print",
    "imprimir": "print", "etiquetas": "tags", "organizar": "organize", "organizo": "organize",
    "carpetas": "folders", "busco": "search", "buscar": "search", "busqueda": "search", "aparecen": "showing",
    "arreglo": "fix", "arreglar": "fix", "sincronizacion": "sync", "aplicacion": "app", "colores": "colors",
    "tema": "theme", "borre": "deleted", "recuperar": "recover", "recuperarla": "recover", "funciona": "work",
    "planes": "plans", "precios": "prices", "suscripcion": "subscription", "comparto": "share",
    "compartir": "share", "cuaderno": "notebook", "notebok": "notebook", "equipo": "team", "miembros": "members",
    "plantillas": "templates", "compartidas": "shared", "encuentro": "find", "rapido": "quickly",
    "celular": "phone", "ver": "see", "donde": "where", "como": "how", "que": "what", "puedo": "can",
    "mis": "my", "mi": "my", "cambiar": "change", "cambio": "switch", "roles": "roles", "cada": "each",
    "hacer": "do", "funcionan": "work", "dispositivo": "device", "conexion": "connection",
}
ES_STOP = {"el", "la", "los", "las", "un", "una", "unos", "de", "del", "a", "al", "en", "y", "o", "con", "por",
           "para", "se", "le", "lo", "me", "porfa", "luego", "despues", "hay", "uno", "es", "son"}


def _plain(text):
    for a, b in zip("áéíóúñü", "aeiounu"):
        text = text.replace(a, b)
    return text


def _translate(prompt, system, model=None):
    # A word list, not a translator: enough for the kit's 20 Spanish questions. Real models do far better.
    text = _plain(prompt.split("Question:", 1)[-1].strip().lower())
    text = re.sub(r"[¿?¡!.,]", " ", text)
    for es, en in PHRASES:
        text = text.replace(es, en)
    out = []
    for w in text.split():
        if w in GLOSSARY:
            out.append(GLOSSARY[w])
        elif w not in ES_STOP:
            out.append(w)
    return " ".join(out)


# ---------- 13: the input check ----------
def _input_check(prompt, system, model=None):
    # Flags a few attack shapes. It misses rephrased attacks and flags some harmless messages.
    msg = prompt.split("Message:", 1)[-1].lower()
    rules = [("instruction override", r"ignore (all|any|your|previous|the above|my)"),
             ("role play to drop rules", r"\b(you are now|pretend|act as)\b"),
             ("asks for hidden instructions", r"system prompt|your instructions"),
             ("card number", r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b"),
             ("bulk data request", r"\b(all user|every user|everyone's)\b")]
    for reason, pattern in rules:
        if re.search(pattern, msg):
            return f"BLOCK: {reason}"
    return "ALLOW"


HANDLERS = [
    ("Pick the help page", _pick_page),
    ("TOOL PROTOCOL", _agent),
    ("## QUESTION", _context),
    ("Summarize this session", _summarize),
    ("Consolidate these memory notes", _consolidate),
    ("support ticket extractor", _extract),
    ("You grade answers from a help assistant", _judge),
    ("Does the source support", _cite_judge),
    ("Answer using only the numbered sources", _rag),
    ("CASCADE PROTOCOL", _cascade),
    ("Translate this help question into English", _translate),
    ("INPUT CHECK PROTOCOL", _input_check),
]
