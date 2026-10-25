"""第1回: 会話履歴を保ちながら素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 対話入力を開始する

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
from time import perf_counter

from google import genai
from google.genai import errors
from google.genai import types

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat():
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(temperature=1.0),
    )
    return client, chat


def ask_in_chat(chat, question: str) -> str:
    started_at = perf_counter()
    try:
        response = chat.send_message(question)
    finally:
        elapsed = perf_counter() - started_at
        print(f"[応答時間] {elapsed:.2f}秒")

    usage = response.usage_metadata
    if usage is None:
        print("[入力トークン] 不明")
        print("[出力トークン] 不明")
    else:
        print(f"[入力トークン] {usage.prompt_token_count}")
        print(f"[出力トークン] {usage.candidates_token_count}")

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="会話履歴を保ちながら素のLLMに質問する")
    parser.add_argument("question", nargs="?", help="最初に送る質問（省略すると入力待ち）")
    args = parser.parse_args()

    client, chat = create_chat()
    print(f"[model] {MODEL}")
    print("終了するには exit または quit を入力してください。\n")

    question = args.question
    try:
        while True:
            if question is None:
                try:
                    question = input("質問> ")
                except EOFError:
                    print()
                    break

            question = question.strip()
            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                question = None
                continue

            print(f"[質問] {question}\n")
            print(ask_in_chat(chat, question))
            print()
            question = None
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    finally:
        client.close()


def ask(question: str) -> str:
    client, chat = create_chat()
    try:
        return ask_in_chat(chat, question)
    finally:
        client.close()


if __name__ == "__main__":
    main()
