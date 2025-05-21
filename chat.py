import os
import subprocess
import time
import threading
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from kubernetes import config, client

# Load environment variables
load_dotenv()

GCLOUD_PATH = r"C:\Users\u32s98\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
ADC_PATH = Path("~/.config/gcloud/application_default_credentials.json").expanduser()

def text_to_speech(text):
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def authenticate_with_gke(service_account_key_path, project_id, cluster_name, region):
    if ADC_PATH.exists():
        print("🔁 Using cached GCP authentication.")
    else:
        try:
            subprocess.run([
                GCLOUD_PATH, "auth", "activate-service-account", "--key-file", service_account_key_path
            ], check=True)
            subprocess.run([GCLOUD_PATH, "config", "set", "project", project_id], check=True)
            subprocess.run([
                GCLOUD_PATH, "container", "clusters", "get-credentials", cluster_name, "--region", region
            ], check=True)
            print("✅ GKE authentication successful")
        except subprocess.CalledProcessError as e:
            print("❌ Error during GKE authentication:", e)

def setup_k8s_and_gemini():
    config.load_kube_config()

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        safety_settings=safety_settings,
        generation_config=generation_config,
        system_instruction=(
            "You are a DevOps Architect. Your task is to explain complex technical concepts in short, easy and layman terms. "
            "First every time please give standard definition of the term. "
            "Ask questions to better understand the user and improve the response. "
            "Suggest real-world observations and experiments where possible."
        ),
    )
    return model.start_chat(history=[])

def get_gemini_response(chat_session, prompt):
    response = chat_session.send_message(prompt)
    return response.text

def monitor_k8s_and_analyze(chat_session):
    try:
        pods_output = subprocess.check_output(
            "kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name' --no-headers",
            shell=True
        ).decode()
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ Failed to connect to Kubernetes API: {e.output.decode()}"
        print(error_msg)
        return get_gemini_response(chat_session, f"Kubernetes monitoring failed with this error:\n{error_msg}")

    error_keywords = ["Error", "CrashLoopBackOff", "OOMKilled", "Failed", "Exception"]
    error_logs = ""

    for line in pods_output.strip().splitlines():
        namespace, pod = line.strip().split()
        try:
            logs = subprocess.check_output(
                f"kubectl logs -n {namespace} {pod} --tail=20",
                shell=True,
                stderr=subprocess.STDOUT
            ).decode()
            matching_lines = [l for l in logs.splitlines() if any(word in l for word in error_keywords)]
            if matching_lines:
                error_logs += f"\n\n--- Logs from {namespace}/{pod} ---\n" + "\n".join(matching_lines)
        except subprocess.CalledProcessError:
            continue

    if not error_logs:
        return "✅ No Kubernetes errors detected in the logs."

    prompt = f"""These are the Kubernetes logs with potential errors. 
Can you analyze them and suggest what went wrong and how to fix it?\n\n{error_logs}"""

    return get_gemini_response(chat_session, prompt)

def continuous_monitoring(chat_session, interval_seconds=60):
    def monitor_loop():
        while True:
            result = monitor_k8s_and_analyze(chat_session)
            print(result)
            time.sleep(interval_seconds)

    threading.Thread(target=monitor_loop, daemon=True).start()

def run_chatbot_cli(chat_session):
    print("Bot: Hello, how can I help you?\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            print("⚠️ Please enter a message.\n")
            continue
        response = get_gemini_response(chat_session, user_input)
        print(f"Bot: {response}\n")

# ✅ Entry point
if __name__ == "__main__":
    authenticate_with_gke(
        service_account_key_path="dominic-infra-f0c06438b9dc.json",
        project_id="dominic-infra",
        cluster_name="dominic-gke",
        region="us-central1"
    )

    chat_session = setup_k8s_and_gemini()

    # 🔁 Start monitoring in background
    continuous_monitoring(chat_session, interval_seconds=60)

    # 🗨️ Start interactive chat in main thread
    run_chatbot_cli(chat_session)
