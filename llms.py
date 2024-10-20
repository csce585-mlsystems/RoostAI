from abc import ABC, abstractmethod

import pandas as pd

import google.generativeai as genai
from huggingface_hub import InferenceClient
from openai import OpenAI
from anthropic import Anthropic


class LLM(ABC):
    def __init__(self, name: str, token: str, df: pd.DataFrame):
        """
        Initialize the LLM.
        @param name: The name of the LLM.
        @param token: The token for the API.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        self.name: str = name
        self.token: str = token
        self.df: pd.DataFrame = df
        self.system_prompt: str = ("You are a chatbot specifically designed to provide information about the "
                                   "University of South Carolina (USC). Your knowledge encompasses USC's "
                                   "history, academics, campus life, athletics, notable alumni, and current events "
                                   "related to the university. When answering questions, always assume they are in "
                                   "the context of USC unless explicitly stated otherwise. Provide accurate and "
                                   "up-to-date information about USC, maintaining a friendly and enthusiastic tone "
                                   "that reflects the spirit of the Trojan community. If you're unsure about any "
                                   "USC-specific information, state that you don't have that particular detail rather "
                                   "than guessing. Your purpose is to assist students, faculty, alumni, and anyone "
                                   "interested in learning more about USC.")

    @abstractmethod
    def get_response(self, question: str) -> str:
        pass  # Leave for subclasses

    def get_responses(self):
        """
        Get all responses for each question in the DataFrame.
        Add as a new column in the DataFrame with the name of the LLM.
        @return: The DataFrame with the responses.
        """
        self.df[self.name] = self.df["question"].apply(self.get_response)
        return self.df


class phi_3_5_mini_ins(LLM):
    def __init__(self, df, token):
        """
        Initialize the Meta Llama 3 8B LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("Phi-3.5-mini-ins ", token, df)

    def get_response(self, question: str) -> str:
        """
        Get response from the HuggingFace serverless API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = InferenceClient("microsoft/Phi-3.5-mini-instruct", token=self.token)

        return_str: str = ""

        for message in client.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=2048,
                stream=True,
        ):
            return_str += message.choices[0].delta.content

        return return_str


class llama_3_8b_ins(LLM):
    def __init__(self, df, token):
        """
        Initialize the Meta Llama 3 8B LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("Meta-Llama-3-8B-Instruct", token, df)

    def get_response(self, question: str) -> str:
        """
        Get response from the HuggingFace serverless API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=self.token)

        return_str: str = ""

        for message in client.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=2048,
                stream=True,
        ):
            return_str += message.choices[0].delta.content

        return return_str


class gemini_flash(LLM):
    def __init__(self, df, token):
        """
        Initialize the Gemini 1.5 Flash LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("gemini-1.5-flash", token, df)

    def get_response(self, question: str) -> str:
        """
        Get response from the Gemini API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        genai.configure(api_key=self.token)
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=self.system_prompt)

        return model.generate_content(question).text


class mixtral_8x7b_ins(LLM):
    def __init__(self, df, token):
        """
        Initialize the Mixtral 8x7B LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("mixtral-8x7B-instruct", token, df)

    def get_response(self, question: str) -> str:
        """
        Get response from the HuggingFace serverless API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = InferenceClient("mistralai/Mixtral-8x7B-Instruct-v0.1", token=self.token)

        return_str: str = ""

        for message in client.chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=2048,
                stream=True,
        ):
            return_str += message.choices[0].delta.content

        return return_str


class claude_sonnet(LLM):
    def __init__(self, df, token):
        """
        Initialize the Claude 3.5 Sonnet LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("claude-3.5-sonnet", token, df)

    def get_response(self, question: str) -> str:
        """
        Get a response from the Anthropic API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = Anthropic()

        message = client.messages.create(
            max_tokens=2048,
            system=self.system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model="claude-3-5-sonnet-20240620",
        )

        return message.content[0].text


class gpt_4o(LLM):
    def __init__(self, df, token):
        """
        Initialize the OpenAI GPT-4o LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("gpt-4o", token, df)

    def get_response(self, question: str) -> str:
        """
        Get a response from the OpenAI API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question}
            ]
        )

        return completion.choices[0].message.content


class gpt_4o_mini(LLM):
    def __init__(self, df, token):
        """
        Initialize the OpenAI GPT-4o LLM.
        @param df: The DataFrame of questions and answers.
        """
        super().__init__("gpt-4o-mini", token, df)

    def get_response(self, question: str) -> str:
        """
        Get a response from the OpenAI API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question}
            ]
        )

        return completion.choices[0].message.content
