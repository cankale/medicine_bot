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
    result = reader.readtext(os.path.join(dir_path, file))
    texts = [text for (_, text, _) in result]
    response = ollama.chat(
        model='llama3.2',
        messages=[{
            "role": "user",
            "content": f"These texts were extracted from a medicine box: {texts}. Which one of these texts is the brand name of the medicine (not active ingredient, not dosage, not manufacturer)? Reply with only that exact word from the list, nothing else."
        }]
    )
    medicine_name = response['message']['content'].strip()
    data.append({"medicine": medicine_name})

df = pd.DataFrame(data)
df.to_csv(out_path, index=False)
print(df)

# Push to GitHub
subprocess.run(["git", "add", "medicines.csv"], cwd="/Users/cankale/code_projects/medicine_bot")
subprocess.run(["git", "commit", "-m", "update medicines"], cwd="/Users/cankale/code_projects/medicine_bot")
subprocess.run(["git", "push"], cwd="/Users/cankale/code_projects/medicine_bot")