import json
import os
os.system('cls')

def main():
    with open("C:\\1337-Project\\ai-rag-assistant\\data\\evaluation_dataset50.json", "r") as f:
        data = json.load(f)
    for item in data:
        question = item["question"]
        print(question)
if __name__ == "__main__":
    main()