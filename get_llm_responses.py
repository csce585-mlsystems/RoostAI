from dotenv import load_dotenv
from os import getenv
import pandas as pd
from llms import phi_3_5_mini_ins, llama_3_8b_ins, gemini_flash, mixtral_8x7b_ins, claude_sonnet, gpt_4o_mini


def merge_dfs(*args):
    """
    Function to merge DataFrames
    """
    # Start with the first DataFrame
    merged_df = args[0]

    # Iterate over the remaining DataFrames
    for df in args[1:]:
        # Combine using the following rules:
        # - Columns that are in both will retain the values from the first DataFrame (i.e., merged_df)
        # - New columns from df will be added (concatenated) to the merged_df
        merged_df = pd.concat([merged_df, df.loc[:, ~df.columns.isin(merged_df.columns)]], axis=1)
    
    return merged_df


def main():
    load_dotenv()

    hf_api_key = getenv('HF_API_KEY')
    google_api_key = getenv('GOOGLE_API_KEY')
    anthropic_api_key = getenv('ANTHROPIC_API_KEY')
    openai_api_key = getenv('OPENAI_API_KEY')
    
    data_file: str = "data/faq_pairs.csv"
    print(f"Reading data from {data_file}")

    bank_df: pd.DataFrame = pd.read_csv(data_file)
    print(f"Number of questions: {len(bank_df)}")

    # print('Getting Phi responses')
    # phi_response = phi_3_5_mini_ins(bank_df, hf_api_key).get_responses()
    
    # print('Getting Llama responses')
    # llama_response = llama_3_8b_ins(bank_df,hf_api_key).get_responses()
    
    # print('Getting Gemini responses')
    # gemini_response = gemini_flash(bank_df, google_api_key).get_responses()
    
    # print('Getting Mixtral responses')
    # mixtral_response = mixtral_8x7b_ins(bank_df, hf_api_key).get_responses()
    
    # print('Getting Claude responses')
    # claude_response = claude_sonnet(bank_df, anthropic_api_key).get_responses()
    
    print('Getting GPT-4o responses')
    gpt_response = gpt_4o_mini(bank_df, openai_api_key).get_responses()

    # all_llm_responses = merge_dfs(phi_response, llama_response, gemini_response, mixtral_response, claude_response, gpt_response)
    # all_llm_responses.to_csv('data/all_llm_responses.csv', index=False)

if __name__ == "__main__":
    main()
