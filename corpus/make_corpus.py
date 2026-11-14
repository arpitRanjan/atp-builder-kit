"""Write the Quillnote help corpus with an OpenAI model. Quillnote is an invented note-taking app.

Needs OPENAI_API_KEY. Model comes from COURSE_MODEL (default "gpt-5.4").
Writes corpus/qn-01.md ... qn-15.md and corpus/questions.jsonl. Costs a few cents. Run once.
"""
import json
import os
from pathlib import Path

from openai import OpenAI

HERE = Path(__file__).resolve().parent
MODEL = os.environ.get("COURSE_MODEL", "gpt-5.4")
TOPICS = [
    ("Create and edit notes", "public"), ("Export a note as PDF", "public"), ("Tags and folders", "public"),
    ("Search your notes", "public"), ("Fix sync problems", "public"), ("Dark mode and themes", "public"),
    ("Recover a deleted note", "public"), ("Offline mode", "public"), ("Plans and pricing", "public"),
    ("Share a notebook with your team", "team"), ("Team roles and permissions", "team"),
    ("Team shared templates", "team"), ("Refund a double charge", "admin"),
    ("Delete a user's data on request", "admin"), ("Read the audit log", "admin"),
]

client = OpenAI()  # reads OPENAI_API_KEY from the environment


def ask(prompt):
    resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return resp.choices[0].message.content.strip()


# Step 1: one short help page per topic.
pages = []
for n, (title, visibility) in enumerate(TOPICS, start=1):
    page_id = f"qn-{n:02d}"
    body = ask(
        f"Write a short help page (120 to 200 words, markdown, no front matter, no title line) for "
        f"Quillnote, an invented note-taking app. Topic: {title}. Audience: {visibility} users. "
        f"Use plain steps. Do not mention any real company. Do not use em dashes or en dashes."
    )
    text = f"---\nid: {page_id}\ntitle: {title}\nvisibility: {visibility}\n---\n{body}\n"
    (HERE / f"{page_id}.md").write_text(text)
    pages.append({"id": page_id, "title": title, "visibility": visibility})
    print("wrote", page_id, title)

# Step 2: 25 questions, each labeled with the page ids that answer it.
index = "\n".join(f"{p['id']}: {p['title']} ({p['visibility']})" for p in pages)
raw = ask(
    "Here are help pages for an invented note app:\n" + index + "\n\nWrite 25 realistic user questions. "
    'Reply with JSON only: {"questions": [{"question": "...", "page_ids": ["qn-01"]}]}. '
    "Most questions need one page, a few need two. Include 3 questions only admin pages answer."
)
questions = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])["questions"]
with open(HERE / "questions.jsonl", "w") as f:
    for i, q in enumerate(questions, start=1):
        f.write(json.dumps({"qid": f"q{i:02d}", "question": q["question"], "page_ids": q["page_ids"]}) + "\n")
print(f"wrote {len(questions)} questions to questions.jsonl")
