# About this example

This is an example finished Stage 9, made with the kit's offline mock model and the stand-in embedder and
reranker (`KIT_OFFLINE=1`). The numbers are NOT real model results. Run the 09 notebooks live (they download
two small models) for numbers you can use. `.github/workflows/evals.yml` is at its repo path.

You must still do these yourself:

- Wire the retrieval path into your app and link that change from the README (`<link to your app change ...>`).
- Add your own labeled questions to `evals/retrieval_questions.jsonl` (20 or more in total).
