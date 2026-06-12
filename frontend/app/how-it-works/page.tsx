export default function HowItWorks() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-bold">How it works</h1>
      <p className="mt-4 text-slate-600">
        FoodSense uses embeddings to perform semantic search and falls back to
        lexical search when needed. Summaries are generated with a local LLM
        (Mistral via Ollama) or via an extractive fallback.
      </p>
    </main>
  );
}
