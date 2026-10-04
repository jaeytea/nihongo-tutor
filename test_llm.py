from llm import ask_llm


if __name__ == "__main__":
    answer = ask_llm(
        "You are a helpful assistant.",
        "Reply with a short greeting in Hindi.",
    )
    print(answer if answer is not None else "No response from the LLM.")