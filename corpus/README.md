# corpus/

The 15 help pages for Quillnote (an invented note-taking app, not a real company) are already in this
folder, so you never need to run anything to get them. They were generated once by `corpus/make_corpus.py`,
which needs an OpenAI key. Run it only if you want to regenerate them:

```
export OPENAI_API_KEY=...        # your key
export COURSE_MODEL=gpt-5.4      # optional, this is the default
python corpus/make_corpus.py
```

It writes about 15 markdown pages (`qn-01.md`, `qn-02.md`, ...), each with `id`, `title` and
`visibility` (public, team or admin) front matter, plus `corpus/questions.jsonl` with 25 questions
labeled with the page ids that answer them.
