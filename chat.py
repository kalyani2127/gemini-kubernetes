import os
import subprocess
import shutil
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from kubernetes import config, client
from main import text_to_speech

# Load environment variables
load_dotenv()

GCLOUD_PATH = r"C:\Users\u32s98\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

def live_monitor(interval=30, namespace=None):
    while True:
        print("🔍 Quick Kubernetes overview...")
        quick_k8s_overview(namespace)
        print("\n🔍 Checking Kubernetes logs for errors...")
        result = monitor_k8s_and_analyze(namespace)
        print(result)
        print("-" * 80)
        time.sleep(interval)

def authenticate_with_gke(service_account_key_path, project_id, cluster_name, region):
    if not Path("~/.config/gcloud/application_default_credentials.json").expanduser().exists():
        return
    try:
        subprocess.run(
            [GCLOUD_PATH, "auth", "activate-service-account", "--key-file", service_account_key_path],
            check=True
        )
        subprocess.run([GCLOUD_PATH, "config", "set", "project", project_id], check=True)
        subprocess.run(
            [GCLOUD_PATH, "container", "clusters", "get-credentials", cluster_name, "--region", region],
            check=True
        )
        print("✅ GKE authentication successful")
    except subprocess.CalledProcessError as e:
        print("❌ Error during GKE authentication:", e)

authenticate_with_gke(
    service_account_key_path="dominic-infra-f0c06438b9dc.json",
    project_id="dominic-infra",
    cluster_name="dominic-gke",
    region="us-central1"
)

# Load kubeconfig after authentication
config.load_kube_config()
v1 = client.CoreV1Api()

# Configure Gemini API
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

chat_session = model.start_chat(history=[])

def get_gemini_response(prompt):
    response = chat_session.send_message(prompt)
    text = response.text
    chat_session.history.append({"role": "user", "parts": [prompt]})
    chat_session.history.append({"role": "model", "parts": [text]})
    return text

def run_chatbot_cli():
    print("Bot: Hello, how can I help you?\n")
    text_to_speech("Hello, how can I help you?")

    while True:
        user_input = input("You: ")
        print()

        model_response = get_gemini_response(user_input)

        print(f'Bot: {model_response}\n')
        text_to_speech(model_response)

def monitor_k8s_and_analyze(namespace=None):
    pods = get_running_pods(namespace)
    if not pods:
        return "❌ No running pods found."

    error_keywords = ["Error", "CrashLoopBackOff", "OOMKilled", "Failed", "Exception"]
    all_error_logs = []

    for pod_name, ns in pods:
        logs = get_pod_logs(pod_name, ns)
        error_logs = [line for line in logs.splitlines() if any(word in line for word in error_keywords)]
        if error_logs:
            all_error_logs.append(f"--- Errors in pod {pod_name} (namespace: {ns}) ---")
            all_error_logs.extend(error_logs)
            all_error_logs.append("")

    if not all_error_logs:
        return "✅ No Kubernetes errors detected in any pod logs."

    prompt = f"""These are the Kubernetes logs with potential errors:
Please analyze and suggest what went wrong and how to fix it.

{chr(10).join(all_error_logs)}"""

    return get_gemini_response(prompt)

# ✅ New utility functions added below

def describe_deployment(namespace, deployment_name):
    try:
        output = subprocess.check_output(
            f"kubectl describe deployment {deployment_name} -n {namespace}",
            shell=True
        ).decode()
        return output
    except subprocess.CalledProcessError as e:
        return f"❌ Error describing deployment: {e.output.decode()}"

def get_running_pods(namespace=None):
    try:
        if namespace:
            cmd = (
                f"kubectl get pods -n {namespace} "
                f"--field-selector=status.phase=Running "
                f"-o jsonpath='{{range .items[*]}}{{.metadata.name}} {{.metadata.namespace}}\\n{{end}}'"
            )
        else:
            # For all namespaces
            cmd = (
                "kubectl get pods --all-namespaces "
                "--field-selector=status.phase=Running "
                "-o jsonpath='{range .items[*]}{.metadata.name} {.metadata.namespace}\\n{end}'"
            )

        output = subprocess.check_output(cmd, shell=True).decode().strip()
        pods = [line.split() for line in output.splitlines()]
        return pods  # list of [pod_name, namespace]

    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting running pods: {e.output.decode()}")
        return []

def get_pod_logs(pod_name, namespace, tail=50):
    try:
        cmd = f"kubectl logs {pod_name} -n {namespace} --tail={tail} --all-containers"
        logs = subprocess.check_output(cmd, shell=True).decode()
        return logs
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get logs for pod {pod_name}: {e.output.decode()}")
        return ""

def get_service_endpoints(namespace=None):
    try:
        cmd = f"kubectl get endpoints{' -n ' + namespace if namespace else ''}"
        output = subprocess.check_output(cmd, shell=True).decode()
        return output
    except subprocess.CalledProcessError as e:
        return f"❌ Error getting service endpoints: {e.output.decode()}"

def get_resource_usage(namespace=None):
    try:
        cmd = f"kubectl top pods{' -n ' + namespace if namespace else ''}"
        output = subprocess.check_output(cmd, shell=True).decode()
        return output
    except subprocess.CalledProcessError as e:
        return f"❌ Error getting resource usage: {e.output.decode()}"

def get_node_status():
    try:
        output = subprocess.check_output("kubectl get nodes -o wide", shell=True).decode()
        return output
    except subprocess.CalledProcessError as e:
        return f"❌ Error getting node status: {e.output.decode()}"

def quick_k8s_overview(namespace=None):
    print("📦 Running Pods:")
    print(get_running_pods(namespace))

    print("\n📊 Resource Usage (CPU/Memory):")
    print(get_resource_usage(namespace))

    print("\n🖥️ Node Status:")
    print(get_node_status())

# ✅ Entry point
if __name__ == "__main__":
    # run_chatbot_cli()
    live_monitor(interval=120)
    # Uncomment to run error analysis at start
    # print(monitor_k8s_and_analyze())
