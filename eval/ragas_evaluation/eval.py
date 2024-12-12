from ragas import SingleTurnSample
from ragas.metrics import LLMContextPrecisionWithReference, LLMContextRecall, FaithfulnesswithHHEM, NoiseSensitivity, ResponseRelevancy

# initialize metric calculators
context_precision = LLMContextPrecisionWithReference()
context_recall = LLMContextRecall()
faithfulness = FaithfulnesswithHHEM()
noise_sensitivity = NoiseSensitivity()


async def rag_eval(query_info: dict):
    """
    query_info = {'query': str, 'ground_truth': str, 'rag_response': str, 'contexts': List[str]}
    """
    sample = SingleTurnSample(
        user_input=query_info['query'], reference=query_info['ground_truth'], response=query_info['rag_response'], retrieved_contexts=query_info['contexts'])

    context_precision_score = await context_precision.single_turn_ascore(sample)
    context_recall_score = await context_precision.single_turn_ascore(sample)
    faithfulness_score = await faithfulness.single_turn_ascore(sample)
    noise_sensitivity_score = await noise_sensitivity.single_turn_ascore(sample)

    # add previous evals
    
    evals = {'context_precision': context_precision_score, 'context_recall': context_recall_score,
             'faithfulness': faithfulness_score, 'noise_sensitivty': noise_sensitivity_score}
