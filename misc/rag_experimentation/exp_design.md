### RAG Experiments
#### In previous results, we have motivated the use of RAG over traditional approaches such as LLMs for our use case. Now, we do some experimentation to determine which RAG configuration is optimal for our use case. In our research, we found there were many chunking strategies available to generate a vectorized database for a RAG application. To compare the efficacy of these different databases, we utilize available metrics for RAG, such as [RAGAS](https://arxiv.org/abs/2309.15217)

### Experimental design
#### We have 4 chunking strategies that we study
- Fixed Size Token Chunking (each chunk is 1024 tokens)
- Sentence Splitting Chunking (each sentence is a chunk)
- Semantic Chunking at 5% similarity threshold *
- Semantic Chunking at 50% similarity threshold *

##### * n% similarity threshold - each sentence is added to a chunk as long as it is 5% or more similar to the chunk

#### We have ~110 questions derived from USC frequently asked questions (FAQs) and their corresponding university provided answers. So we can use reference-based and reference-free RAG metrics. For each of our vectorized databases, we initialize our RAG pipeline and record the response provided by our system.

#### We consider the following metrics for evaluating each instantiation of the RAG system
- [Context Precision with reference](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/#context-precision-without-reference:~:text=(sample)-,Context%20Precision%20with%20reference,-LLMContextPrecisionWithReference%20metric%20is)
- [LLM Based Context Recall](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/)
- [Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)
- [Noise Sensitivity](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/noise_sensitivity/)
- [Response Relevancy](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/)

#### We will also compare each RAG instance by using the existing reference-based metrics we have used in the past