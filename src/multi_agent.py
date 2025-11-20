# src/multi_agent.py

from typing import List, Dict


class RetrieverAgent:
    """
    Very simple retriever for demo:
    - Scores documents by counting occurrences of the query.
    - Replace later with embeddings + FAISS for real retrieval.
    """
    def __init__(self, corpus: Dict[str, str]):
        # corpus: {resource_id: text/summary}
        self.corpus = corpus

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        results = []
        q = query.lower()

        for rid, text in self.corpus.items():
            score = text.lower().count(q)
            if score > 0:
                results.append((score, rid, text))

        # sort by score descending
        results.sort(reverse=True)

        return [
            {"id": rid, "summary": text, "score": int(score)}
            for score, rid, text in results[:top_k]
        ]


class QAAgent:
    """
    Mock QA agent. In real model:
      - Use an LLM to answer using provided contexts.
    """
    def __init__(self, llm_provider: str = "mock"):
        self.provider = llm_provider

    def answer(self, question: str, contexts: List[Dict]) -> str:
        if not contexts:
            return "I couldn't find matching content; can you rephrase?"

        ctx_text = " \n\n".join(c["summary"] for c in contexts)

        return (
            f"[MockAnswer based on {len(contexts)} docs]\n"
            f"Question: {question}\n\n"
            f"Context excerpt:\n{ctx_text[:400]}"
        )


class Orchestrator:
    """
    Coordinates:
      - RetrieverAgent
      - QAAgent
    """
    def __init__(self, retriever: RetrieverAgent, qa_agent: QAAgent):
        self.retriever = retriever
        self.qa_agent = qa_agent

    def handle_query(self, question: str) -> Dict:
        contexts = self.retriever.retrieve(question, top_k=3)
        answer = self.qa_agent.answer(question, contexts)
        return {
            "question": question,
            "answer": answer,
            "contexts": contexts
        }
