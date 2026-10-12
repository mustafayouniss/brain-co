"""Retrieval evaluation metrics (Ring 0: evaluation framework).

retrieved: ranked list of document ids returned by the system (best first)
relevant:  set of document ids that are the correct answers
"""
import math


def precision_at_k(retrieved, relevant, k):
    """Of the top-k results, what fraction is relevant?"""
    if k <= 0:
        return 0.0
    return sum(1 for d in retrieved[:k] if d in relevant) / k


def recall_at_k(retrieved, relevant, k):
    """Of all relevant documents, what fraction appears in the top-k?"""
    if not relevant:
        return 0.0
    return sum(1 for d in retrieved[:k] if d in relevant) / len(relevant)


def reciprocal_rank(retrieved, relevant):
    """1 / rank of the first relevant result (0 if none). Mean over queries = MRR."""
    for rank, d in enumerate(retrieved, start=1):
        if d in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved, relevant, k):
    """Like recall, but rewards putting relevant results higher in the ranking."""
    dcg = sum(1 / math.log2(i + 2) for i, d in enumerate(retrieved[:k]) if d in relevant)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 0.0


def evaluate(results, ground_truth, k=5):
    """results: {query_id: [ranked doc ids]}, ground_truth: {query_id: {relevant ids}}"""
    n = len(ground_truth)
    return {
        f"precision@{k}": sum(precision_at_k(results[q], ground_truth[q], k) for q in ground_truth) / n,
        f"recall@{k}": sum(recall_at_k(results[q], ground_truth[q], k) for q in ground_truth) / n,
        "mrr": sum(reciprocal_rank(results[q], ground_truth[q]) for q in ground_truth) / n,
        f"ndcg@{k}": sum(ndcg_at_k(results[q], ground_truth[q], k) for q in ground_truth) / n,
    }


if __name__ == "__main__":
    results = {"q1": ["a", "b", "c"], "q2": ["x", "a", "c"]}
    truth = {"q1": {"a"}, "q2": {"a"}}
    print(evaluate(results, truth, k=3))