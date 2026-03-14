import Vision
import ollama
import os
import pandas as pd
import subprocess
from Foundation import NSURL

def read_text_apple_vision(image_path):
    input_url = NSURL.fileURLWithPath_(image_path)
    
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(True)
    
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(input_url, None)
    handler.performRequests_error_([request], None)
    
    texts = []
    for observation in request.results():
        texts.append(observation.topCandidates_(1)[0].string())
    
    return texts

dir_path = "/Users/cankale/Downloads/ilaclar"
out_path = "/Users/cankale/code_projects/medicine_bot/medicines.csv"
data = []

for file in os.listdir(dir_path):
    if not file.endswith(('.jpg', '.jpeg', '.png', '.heic', '.HEIC')):
        continue
    try:
        texts = read_text_apple_vision(os.path.join(dir_path, file))
    except Exception as e:
        print(f"⚠️ Failed, add manually: {os.path.join(dir_path, file)}")
        continue
    print(f"\n{file}: {texts}")

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