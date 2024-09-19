## **Prioritize Evaluation Setup**

Jupyter Notebook will be our medium for experimentation and presentation

## **Collaborate on Experiment Design**

- *Key Challenge:* We don’t know how good pre-existing LLMs are on USC-centered queries.
- *Initial experiment design:*
    - Gather official [USC-related FAQs](https://sc.edu/about/offices_and_divisions/advising/curriculum_services/faq/index.php) (will serve as the ground truth)
    - Compare the ground truth with outputs from all LLMs.
- *Metrics (source:* https://learn.microsoft.com/en-us/ai/playbook/technology-guidance/generative-ai/working-with-llms/evaluation/list-of-eval-metrics):
    - Reference-based metrics are used to compare generated text to a reference, the human-annotated *ground truth* text.
    - **N-gram-based metrics:** Metrics [BLEU (Bilingual Evaluation Understudy)](https://aclanthology.org/P02-1040.pdf), [ROUGE (Recall-Oriented Understudy for Gisting Evaluation)](https://aclanthology.org/W04-1013.pdf), and [JS divergence (JS2)](http://arxiv.org/abs/2010.07100) are overlap-based metrics that measure the similarity of the output text and the reference text using n-grams.
    - **Text Similarity metrics:** Text similarity metrics evaluators focus on computing similarity by comparing the overlap of word or word sequences between text elements. They’re useful for producing a similarity score for predicted output from an LLM and reference ground truth text. These metrics also give an indication as to how well the model is performing for each respective task.
    - **Semantic Similarity metrics:** [BERTScore](https://github.com/Tiiiger/bert_score), [MoverScore](http://tiny.cc/vsqtbz), and [Sentence Mover Similarity (SMS)](https://github.com/src-d/wmd-relax) metrics all rely on contextualized embeddings to measure the similarity between two texts. While these metrics are relatively simple, fast, and inexpensive to compute compared to LLM-based metrics, [studies have shown](https://arxiv.org/abs/2008.12009) that they can have poor correlation with human evaluators, lack of interpretability, inherent bias, poor adaptability to a wider variety of tasks, and inability to capture subtle nuances in language.

## **Design of Experiments (DOE)**

- System Prompt setup
    - Go through USC FAQs
    - Find relevant statistics
    - Find the average answer response length $\lambda$ to FAQs
    - Edit the LLM system-prompt to include something along the following lines:
        - *You are a university-centered chatbot for the University of South Carolina. Limit your response to $\lambda$ words.*
- For each LLM, provide each of the 40 FAQs as a separate query and record the responses
- Now have a 2d array with each element being the array of responses from each LLM and the first element being the ground truth answers
- Now evaluate the responses against the ground truth for each LLM utilizing the aforementioned metrics
- Construct different charts for each metric, with the 40 responses being points on the x-axis and the metric score being on the y-axis. Each LLM will be a different colored line graph. The result will be something similar to [this graph](https://canvasjs.com/wp-content/uploads/2021/03/multi-series-line-chart.png).
- *Independent Variables:* Model size and question/answers
- *Dependent Variables:* Metrics
- *Control Variables:* LLM System prompt

## **Examples of Solid Motivation Experiments**

- One potential issue in our approach is that automated evaluation metrics might not accurately convey the entire similarity/difference spectrum. Reference-based metrics have traditionally been the cornerstone of evaluating LLM outputs. For instance, studies have shown that metrics such as BLEU and ROUGE, which rely on lexical similarity to reference texts, often fail to capture the semantic richness of generated outputs. This inadequacy has been highlighted by Sellam et al., who argue that these metrics correlate poorly with human judgment, especially when comparing outputs of similar accuracy levels (Sellam et al., 2020).
    
    *Sellam, T., Das, D., & Parikh, A. (2020). Bleurt: learning robust metrics for text generation.. https://doi.org/10.18653/v1/2020.acl-main.704*