# Retrieval Evaluation Metrics

## 1. Purpose

This code evaluates the quality of a **document retrieval system** by comparing the documents returned by the system with the documents known to be relevant to each query.

When a user submits a query, a retrieval system returns a ranked list of document IDs, ordered from the most relevant to the least relevant. However, returning results does not necessarily mean that the results are accurate or properly ranked.

To measure retrieval quality, this code calculates four evaluation metrics:

* **Precision@k:** Measures the proportion of the top-k retrieved documents that are relevant.
* **Recall@k:** Measures the proportion of all relevant documents that appear in the top-k results.
* **Mean Reciprocal Rank (MRR):** Measures how highly the first relevant document appears in the ranked results, averaged across queries.
* **Normalized Discounted Cumulative Gain (NDCG@k):** Evaluates ranking quality by giving more importance to relevant documents that appear near the top of the results.

Together, these metrics provide different perspectives on retrieval performance. Precision focuses on the correctness of returned results, Recall focuses on finding relevant documents, MRR focuses on the position of the first relevant result, and NDCG evaluates the overall ranking.

### Input Data

The code relies on the following inputs:

| Input          | Description                                                                      |
| -------------- | -------------------------------------------------------------------------------- |
| `retrieved`    | A ranked list of document IDs returned by the retrieval system.                  |
| `relevant`     | A set of document IDs considered relevant to the query.                          |
| `k`            | The number of top results considered during evaluation.                          |
| `results`      | A dictionary mapping each query ID to its ranked list of retrieved document IDs. |
| `ground_truth` | A dictionary mapping each query ID to the set of documents known to be relevant. |

The individual functions calculate each metric for a single query, while the `evaluate()` function combines them and calculates the average scores across all queries.

## 2. Evaluation Metrics Overview

| Metric      | What It Measures                                                         | Ideal Score |
| ----------- | ------------------------------------------------------------------------ | ----------: |
| Precision@k | The proportion of the top-k results that are relevant.                   |         1.0 |
| Recall@k    | The proportion of all relevant documents retrieved in the top-k results. |         1.0 |
| MRR         | How early the first relevant result appears across queries.              |         1.0 |
| NDCG@k      | How effectively relevant documents are ranked near the top.              |         1.0 |

**Note:** No single metric fully describes retrieval performance. The metrics should be considered together to provide a more complete evaluation.

## 3. Example and Expected Results

The example evaluates two queries using `k = 3`.

```python
results = {
    "q1": ["a", "b", "c"],
    "q2": ["x", "a", "c"]
}

truth = {
    "q1": {"a"},
    "q2": {"a"}
}

print(evaluate(results, truth, k=3))
```

For `q1`, the relevant document `a` appears in the first position. For `q2`, it appears in the second position.

The expected output is approximately:

```python
{
    'precision@3': 0.3333,
    'recall@3': 1.0,
    'mrr': 0.75,
    'ndcg@3': 0.8155
}
```

### Results Interpretation

* **Precision@3 = 0.3333:** One out of the three retrieved documents is relevant for each query.
* **Recall@3 = 1.0:** All known relevant documents appear within the top three results.
* **MRR = 0.75:** The first relevant result appears first for one query and second for the other.
* **NDCG@3 ≈ 0.8155:** The relevant documents are ranked reasonably well, although the first relevant result does not always appear in the first position.

## 4. Notes and Limitations

* The code assumes that every query in `ground_truth` also exists in `results`.
* An empty `ground_truth` dictionary would cause a division-by-zero error in `evaluate()`.
* The current implementation treats relevance as binary: each document is either relevant or not relevant.
* `precision_at_k()` divides by `k`, even if fewer than `k` documents are returned.
* Evaluation quality depends on the accuracy and completeness of the relevance labels in `ground_truth`.
* Evaluation data should remain separate from development data to avoid data leakage.

## 5. Relevance to Ring 0

In Ring 0, this code establishes an initial, reusable foundation for evaluating retrieval components. It defines how retrieval results can be measured and compared, but **it does not implement the retrieval system itself**.

In later Rings, the team will need to prepare evaluation queries, establish reliable relevance labels, run the retrieval system, calculate these metrics, and compare results across different system versions.

The detailed evaluation datasets, thresholds, and testing procedures can be defined when the corresponding retrieval components are implemented.
