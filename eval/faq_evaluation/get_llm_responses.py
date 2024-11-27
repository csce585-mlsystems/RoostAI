from dotenv import load_dotenv
from os import getenv
import pandas as pd
from llms import (
    phi_3_5_mini_ins,
    llama_3_8b_ins,
    gemini_flash,
    mixtral_8x7b_ins,
    claude_sonnet,
    gpt_4o,
)


def save_temp_df(df: pd.DataFrame, out_file: str):
    print(f"Writing to file {out_file}")
    df.to_csv(out_file, index=False)


def main():
    load_dotenv()

    hf_api_key = getenv("HF_API_KEY")
    google_api_key = getenv("GOOGLE_API_KEY")
    anthropic_api_key = getenv("ANTHROPIC_API_KEY")
    openai_api_key = getenv("OPENAI_API_KEY")

    data_file: str = "data/faq_pairs.csv"
    print(f"Reading data from {data_file}")

    bank_df: pd.DataFrame = pd.read_csv(data_file)
    print(f"Number of questions: {len(bank_df)}\n")

    print("Getting Phi responses...")
    bank_df["phi"] = phi_3_5_mini_ins(bank_df, hf_api_key).get_responses().values

    print("Getting Llama responses...")
    bank_df["llama"] = llama_3_8b_ins(bank_df, hf_api_key).get_responses().values

    print("Getting Gemini responses...")
    bank_df["gemini"] = gemini_flash(bank_df, google_api_key).get_responses().values

    print("Getting Mixtral responses...")
    bank_df["mixtral"] = mixtral_8x7b_ins(bank_df, hf_api_key).get_responses().values

    print("Getting Claude responses...")
    bank_df["claude"] = claude_sonnet(bank_df, anthropic_api_key).get_responses().values

    print("Getting GPT-4o responses...")
    bank_df["gpt"] = gpt_4o(bank_df, openai_api_key).get_responses().values

    out_file: str = "data/faq_responses.csv"
    print(f"Writing to file {out_file}")
    bank_df.to_csv(out_file, index=False)


if __name__ == "__main__":
    main()
