### app.py
# 1) [put the prompt into a string]
# Seldom use notations such as ** ()
# Never share or explain profanity, slurs, sexual or violent content, hate, drugs, self-harm or anything unsuitable; 
# every reply with simple questions can stay under 25 words, for some complex questions such as user wants to hear a story,you should respond with as many words as you can. 
#You are an encouraging, friendly English teaching assistant for children. Your name is Jarvis, just like the assistant of Tony stark, the iron man in the marvel movie.
#You know everything about education and engineering, also you are an expert of perfume.
reading_buddy_prompt = """
Seldom use notations such as ** ()
Never share or explain profanity, slurs, sexual or violent content, hate, drugs, self-harm or anything unsuitable; 
 every reply with simple questions can stay under 25 words, for some complex questions such as user wants to hear a story,you should respond with as many words as you can. 
You are an encouraging, friendly English teaching assistant for children. Your name is Jarvis, just like the assistant of Tony stark, the iron man in the marvel movie.
"""
from flask import Flask, render_template, request, jsonify,session
from flask_cors import CORS
import os
import re
import xyfun_eval
import subprocess
import requests
def convert_to_ise_compatible(input_path, output_path):
    command = [
        'ffmpeg', '-y', '-i', input_path,
        '-ar', '16000', '-ac', '1', '-ab', '32k',
        output_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

app = Flask(__name__)
app.secret_key = 'my_very_secret_key_123456' 
# CORS(app)
UPLOAD_FOLDER = 'uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['audio']
    file_path = os.path.join(UPLOAD_FOLDER, '1.mp3')
    fixed_path = os.path.join(UPLOAD_FOLDER,'fixed.mp3')
    file.save(file_path)
    convert_to_ise_compatible(file_path,fixed_path)
    result_xml = xyfun_eval.run_ise_eval(fixed_path, "OKC, short for the Oklahoma City Thunder, will win the 2025 NBA Champion.")
    score = extract_all_scores(result_xml)

    return jsonify({'score': score})

def extract_all_scores(xml: str) -> dict:
    def extract(pattern):
        match = re.search(pattern, xml)
        return float(match.group(1)) if match else -1

    return {
        "accuracy": extract(r'accuracy_score="([\d.]+)"'),
        "fluency": extract(r'fluency_score="([\d.]+)"'),
        "integrity": extract(r'integrity_score="([\d.]+)"'),
        "total": extract(r'total_score="([\d.]+)"'),
        "standard": extract(r'standard_score="([\d.]+)"')
    }
@app.route('/chat_text', methods=['POST'])
def chat_text():
    data = request.get_json()
    user_input = data.get('text')
    if "chat_history" not in session:
        session["chat_history"] = [{"role":"system","content":"You are a kind AI English friend for children."}]
    session["chat_history"].append({"role":"user", "content":user_input})
    history = session["chat_history"]
    prompt = ""
    for turn in history:
        prompt += f'{turn["role"]}: {turn["content"]}\n'
    clean_text = prompt.replace("*","")
    clean_text = prompt.replace("/","")
    clean_text = prompt.replace("#","")
    reply = ask_deepseek(clean_text)
    cleaned_reply = reply.replace("*", "")
    session["chat_history"].append({"role": "assistant", "content": cleaned_reply})
    # if len(session["chat_history"]) > 7:
    #     session["chat_history"] = [session["chat_history"][0]] + session["chat_history"][-6:]
    return jsonify({'reply': cleaned_reply})

def ask_deepseek(message):
    try:
        headers = {
            "Authorization": "Bearer sk-3d3af47a3d484d77b07846a22f92a1af",  
            "Content-Type": "application/json"
        }
        data = {
         "model": "deepseek-chat",
         "messages": [
        {"role": "system", "content": reading_buddy_prompt},  #
        {"role": "assistant", "content": "Hi there! How can I assist you, my dear friend? 😊"},
        {"role": "user", "content": message}
    ]
}

        res = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)

        # print("HTTP status code:", res.status_code)
        # print("Raw response text:", res.text)

        res.raise_for_status() 

        response_json = res.json()
        return response_json['choices'][0]['message']['content']

    except Exception as e:
        print(" DeepSeek :", str(e))
        return "Sorry, I couldn't reach the AI service right now."

if __name__ == '__main__':
    app.run(debug=True)
