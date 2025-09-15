import subprocess
import json
import os

# --- CONFIGURE THIS ---
# Make sure this path points to your JavaScript test file
test_file_path = os.path.join('test', 'test.js')
# ---

print(f"--- Running ESLint Diagnostic on: {os.path.abspath(test_file_path)} ---")

if not os.path.exists(test_file_path):
    print(f"\nERROR: Test file not found at '{test_file_path}'. Please make sure the file exists.")
    exit()

command = ["eslint", "-f", "json", test_file_path]
print(f"Executing command: {' '.join(command)}")

try:
    result = subprocess.run(
        command, 
        capture_output=True, 
        text=True, 
        check=False,
        shell=True # Use shell=True for global npm packages on Windows, it can help find the command
    )
    
    print("\n--- Subprocess Results ---")
    print(f"Return Code: {result.returncode}")
    print(f"\n--- STDOUT (ESLint's JSON Output) ---")
    print(result.stdout if result.stdout.strip() else "[EMPTY]")
    print(f"\n--- STDERR (Error Messages) ---")
    print(result.stderr if result.stderr.strip() else "[EMPTY]")
    
    if result.stdout:
        print("\n--- JSON Parsing Test ---")
        try:
            # ESLint outputs an array, so we check the first element
            data = json.loads(result.stdout)
            print("JSON parsing successful.")
            if data:
                issues_found = data[0].get("messages", [])
                print(f"Number of issues found by ESLint: {len(issues_found)}")
                if issues_found:
                    print("Issues:", issues_found)
            else:
                print("JSON output was empty.")
        except json.JSONDecodeError as e:
            print(f"JSON parsing FAILED: {e}")

except FileNotFoundError:
    print("\n--- DIAGNOSIS ---")
    print("CRITICAL ERROR: The 'eslint' command was not found by the subprocess.")
    print("This confirms a system PATH issue. Please ensure Node.js is installed and 'npm install -g eslint' was successful.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")