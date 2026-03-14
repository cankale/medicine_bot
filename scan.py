import easyocr
import ollama
import os
import pandas as pd
import subprocess

dir_path = "/Users/cankale/Downloads/ilaclar"
out_path = "/Users/cankale/code_projects/medicine_bot/medicines.csv"
reader = easyocr.Reader(['en'])
data = []

for file in os.listdir(dir_path):
    if not file.endswith(('.jpg', '.jpeg', '.png')):
        continue

    result = reader.readtext(os.path.join(dir_path, file))
    texts = [text for (_, text, _) in result]

    # Get brand name
    name_response = ollama.chat(
        model='llama3.2',
        messages=[{
            "role": "user",
            "content": f"These texts were extracted from a medicine box: {texts}. Which one is the brand name of the medicine? Rules: ignore manufacturer names like Pfizer, Novartis, Bayer, GSK, etc. Ignore words like 'tablet', 'mg', 'ml', 'cream', 'gel'. The brand name is usually the largest or most prominent text. Pick only one word or short phrase from the list. Reply with only that, nothing else."
        }]
    )
    medicine_name = name_response['message']['content'].strip()

    # Get Turkish definition
    def_response = ollama.chat(
        model='llama3.2',
        messages=[{
            "role": "user",
            "content": f"What is {medicine_name} medicine used for? Answer in Turkish, maximum 3 words, no explanation."
        }]
    )
    definition = def_response['message']['content'].strip()

    data.append({
        "medicine": medicine_name,
        "adet": 1,
        "tanim": definition,
        "bbd": ""
    })

# If CSV exists, merge counts
if os.path.exists(out_path):
    old_df = pd.read_csv(out_path)
    new_df = pd.DataFrame(data)
    df = pd.concat([old_df, new_df]).groupby('medicine', as_index=False).agg({
        'adet': 'sum',
        'tanim': 'first',
        'bbd': 'first'
    })
else:
    df = pd.DataFrame(data)

df.to_csv(out_path, index=False)
print(df)

subprocess.run(["git", "add", out_path], cwd="/Users/cankale/code_projects/medicine_bot")
subprocess.run(["git", "commit", "-m", "update medicines"], cwd="/Users/cankale/code_projects/medicine_bot")
subprocess.run(["git", "push"], cwd="/Users/cankale/code_projects/medicine_bot")