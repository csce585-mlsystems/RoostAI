from dotenv import load_dotenv
from os import getenv
from abc import ABC, abstractmethod

import pandas as pd

import google.generativeai as genai
from huggingface_hub import InferenceClient
from openai import OpenAI
from anthropic import Anthropic

# TODO: Add system prompts

class LLM(ABC):
    def __init__(self, name: str, token: str, df: pd.DataFrame,  system_prompt: str):
        """
        Initialize the LLM.
        @param name: The name of the LLM.
        @param token: The token for the API.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        self.name: str = name
        self.token: str = token
        self.df : pd.DataFrame = df
        self.system_prompt: str = system_prompt

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


class gemini_flash(LLM):
    def __init__(self, df, system_prompt):
        """
        Initialize the Gemini 1.5 Flash LLM.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        super().__init__("gemini-1.5-flash", getenv('GOOGLE_API_KEY'), 
                         df, system_prompt)

    def get_response(self, question: str) -> str:
        """
        Get response from the Gemini API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        genai.configure(api_key=getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')

        return model.generate_content(question).text


class llama_3_8b(LLM):
    def __init__(self, df, system_prompt):
        """
        Initialize the Meta Llama 3 8B LLM.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        super().__init__("meta-llama-3-8B", getenv("HF_API_KEY"), 
                         df, system_prompt)

    def get_response(self, question: str) -> str:
        """
        Get response from the HuggingFace serverless API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = InferenceClient(
            "meta-llama/Meta-Llama-3-8B-Instruct",
            token=getenv("HF_API_KEY"),
        )

        return_str: str = ""

        for message in client.chat_completion(
                messages=[{"role": "user", "content": question}],
                max_tokens=500,
                stream=True,
        ):
            return_str += message.choices[0].delta.content

        return return_str


class mixtral_8x7b(LLM):
    def __init__(self, df, system_prompt):
        """
        Initialize the Mixtral 8x7B LLM.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        super().__init__("mixtral-8x7B-instruct", getenv("HF_API_KEY"),
                         df, system_prompt)

    def get_response(self, question: str) -> str:
        """
        Get response from the HuggingFace serverless API given a prompt.
        @param question: The question to send to the LLM.
        @return: The response from the LLM.
        """
        client = InferenceClient(
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            token=getenv("HF_API_KEY"),
        )

        return_str: str = ""

        for message in client.chat_completion(
                messages=[{"role": "user", "content": question}],
                max_tokens=2048,
                stream=True,
        ):
            return_str += message.choices[0].delta.content

        return return_str


class gpt_4o(LLM):
    def __init__(self, df, system_prompt):
        """
        Initialize the OpenAI GPT-4o LLM.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        super().__init__("gpt-4o", getenv("OPENAI_API_KEY"), df, system_prompt)

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


class claude_sonnet(LLM):
    def __init__(self, df, system_prompt):
        """
        Initialize the Claude 3.5 Sonnet LLM.
        @param df: The DataFrame of questions and answers.
        @param system_prompt: The system prompt for the LLM.
        """
        super().__init__("claude-3.5-sonnet", getenv("ANTHROPIC_API_KEY"), 
                         df, system_prompt)

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


def main():
    load_dotenv()

    system_prompt: str = ""  # TODO

    bank_df: pd.DataFrame = pd.read_csv("data/bank.csv")

    gemini_flash(bank_df, system_prompt).get_responses()
    llama_3_8b(bank_df, system_prompt).get_responses()
    mixtral_8x7b(bank_df, system_prompt).get_responses()
    gpt_4o(bank_df, system_prompt).get_responses()
    claude_sonnet(bank_df, system_prompt).get_responses()


if __name__ == "__main__":
    main()
