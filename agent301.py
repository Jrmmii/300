import requests
from tabulate import tabulate
from colorama import Fore, Style
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
import json

# Define a function to read the authorization file with first names and tokens
def read_auth_tokens(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            tokens_with_names = []
            for line in lines:
                if line.strip():
                    # Extract full auth_token (query) and first_name from the query
                    query = line.strip()
                    parsed_query = urllib.parse.parse_qs(query)
                    
                    # Get the auth_token (full query)
                    auth_token = query
                    
                    # Decode and extract `user` parameter to get first_name
                    user_data = parsed_query.get('user', [None])[0]
                    if user_data:
                        decoded_user_data = urllib.parse.unquote(user_data)
                        user_json = json.loads(decoded_user_data)
                        first_name = user_json.get('first_name', 'Unknown')  # Default to 'Unknown' if not found
                        
                        # Append the first_name and full auth_token
                        tokens_with_names.append((first_name, auth_token))
            return tokens_with_names
    except FileNotFoundError:
        print("Authorization file not found.")
        return []

# Load the authorization tokens and first names from the file
ACCOUNT_TOKENS = read_auth_tokens('query.txt')

# Define global headers
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Microsoft Edge\";v=\"127\", \"Chromium\";v=\"127\", \"Microsoft Edge WebView2\";v=\"127\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Referer": "https://telegram.agent301.org/",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

def print_welcome_message():
    print(Fore.WHITE + r"""
          
█▀▀ █░█ ▄▀█ █░░ █ █▄▄ █ █▀▀
█▄█ █▀█ █▀█ █▄▄ █ █▄█ █ ██▄
          """)
    print(Fore.GREEN + Style.BRIGHT + "Agent 301 BOT")
    print(Fore.YELLOW + Style.BRIGHT + "Free Konsultasi Join Telegram Channel: https://t.me/ghalibie")
    print(Fore.BLUE + Style.BRIGHT + "Buy me a coffee :) 0823 2367 3487 GOPAY / DANA")
    print(Fore.RED + Style.BRIGHT + "NOT FOR SALE ! Ngotak dikit bang. Ngoding susah2 kau tinggal rename :)\n\n")

def user(auth_token):
    url = "https://api.agent301.org/getMe"
    headers = HEADERS.copy()
    headers["authorization"] = auth_token
    response = requests.post(url, headers=headers)
    data = response.json()
    
    balance = data.get('result', {}).get('balance', 0)
    
    return balance

def check_task(auth_token):
    url = "https://api.agent301.org/getTasks"
    headers = HEADERS.copy()
    headers["authorization"] = auth_token
    body = {}
    response = requests.post(url, headers=headers, json=body)
    data = response.json()
    tasks = data.get('result', {}).get('data', [])
    return tasks

def clear_task(auth_token, task_type):
    url = "https://api.agent301.org/completeTask"
    headers = HEADERS.copy()
    headers["authorization"] = auth_token
    body = {"type": task_type}
    response = requests.post(url, headers=headers, json=body)
    return response.json()

def spin(auth_token):
    url = "https://api.agent301.org/wheel/spin"
    body = {}
    headers = HEADERS.copy()
    headers["authorization"] = auth_token

    while True:
        response = requests.post(url, headers=headers, json=body)
        result = response.json()

        if result.get('ok'):
            reward = result['result'].get('reward', 'No reward')
            tickets = result['result'].get('tickets', 0)

            print(f"[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Anda berhasil mendapatkan {Fore.LIGHTGREEN_EX}{reward}{Style.RESET_ALL} pada Spin. Tiket tersisa: {tickets}")

            if tickets <= 0:
                print(f"[ {Fore.LIGHTRED_EX}INFO{Style.RESET_ALL} ] Tiket sudah habis. Selesai....")
                break
        else:
            print(f"[ {Fore.LIGHTRED_EX}INFO{Style.RESET_ALL} ] Tiket anda habis!!!")
            break  # Exit the loop if tickets are exhausted

def process_task(auth_token, task_type, task_title, count):
    failed_count = 0  # Counter for failed attempts
    for _ in range(count):
        response = clear_task(auth_token, task_type)
        if response.get('ok') and response.get('result', {}).get('is_completed'):
            reward = response.get('result', {}).get('reward', 0)
            print(f"[ {Fore.LIGHTGREEN_EX}INFO{Style.RESET_ALL} ] Task {Fore.LIGHTMAGENTA_EX}{task_title}{Style.RESET_ALL} berhasil diselesaikan! Reward: {Fore.LIGHTGREEN_EX}{reward}{Style.RESET_ALL}")
        else:
            failed_count += 1
            if failed_count < 5:
                print(f"[ {Fore.LIGHTRED_EX}INFO{Style.RESET_ALL} ] Task {Fore.LIGHTMAGENTA_EX}{task_title}{Style.RESET_ALL} gagal diselesaikan atau sudah selesai")
            elif failed_count == 5:
                print(f"[ {Fore.LIGHTRED_EX}INFO{Style.RESET_ALL} ] Gagal menggunakan bug/Bug telah digunakan pada task {Fore.LIGHTMAGENTA_EX}{task_title}{Style.RESET_ALL}")
                break  # Stop further attempts after reaching 5 failures

def main():
    print_welcome_message()
    
    account_balances = []
    failed_queries = []  # To store any failed queries

    # Step 1: Process each account
    for firstname, auth_token in ACCOUNT_TOKENS:
        print(f"\n\n{Fore.LIGHTCYAN_EX}==========[{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{firstname}{Style.RESET_ALL} {Fore.LIGHTCYAN_EX}]=========={Style.RESET_ALL}")
        
        try:
            balance = user(auth_token)
            tasks = check_task(auth_token)
            
            # Process tasks
            with ThreadPoolExecutor(max_workers=50) as executor:  # Up to 50 threads
                futures = []
                for task in tasks:
                    task_type = task.get('type')
                    task_title = task.get('title')
                    
                    if task_type == "video":
                        print(f"[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Attempting to complete task: {Fore.LIGHTMAGENTA_EX}{task_title}{Style.RESET_ALL}")
                        futures.append(executor.submit(process_task, auth_token, task_type, task_title, 50))
                    else:
                        if not task.get('is_claimed'):
                            print(f"[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Attempting to complete task: {Fore.LIGHTMAGENTA_EX}{task_title}{Style.RESET_ALL}")
                            futures.append(executor.submit(process_task, auth_token, task_type, task_title, 50))
                
                # Await the completion of all tasks
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise exceptions if any task failed
                except Exception as e:
                    print(f"[ {Fore.LIGHTRED_EX}ERROR{Style.RESET_ALL} ] Error processing task for {firstname}: {str(e)}")
                    failed_queries.append((firstname, auth_token))  # Store the failed query

            # Fetch final user details after clearing tasks
            final_balance, _ = user(auth_token)
            account_balances.append([firstname, final_balance])
            
            # Prompt for spin confirmation after completing tasks
            spin(auth_token)
            time.sleep(10)  # Pass auth_token to the spin function
        
        except KeyboardInterrupt:
            print(f"\n{Fore.RED+Style.BRIGHT}Proses dihentikan paksa oleh anda!")
            break
        
        except Exception as e:
            print(f"[ {Fore.LIGHTRED_EX}ERROR{Style.RESET_ALL} ] Error processing account {firstname}: {str(e)}")
            failed_queries.append((firstname, auth_token))  # Store the failed query

    # Retry failed queries
    while failed_queries:
        print(f"[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Retrying failed queries...")
        retry_failed_queries(failed_queries, account_balances)

    # Delay for 5 seconds
    print(f"\n[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Semua proses selesai. Tunggu 5 detik untuk melihat detail semua akun...")
    time.sleep(5)  # Sleep for 5 seconds
    
    # Step 3: Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Tampilkan WM
    print_welcome_message()
        
    # Step 4: Display account details
    print(f"\n[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Detail Akun:")
    print(tabulate(account_balances, headers=["Accounts", "Balance"], tablefmt="grid"))
    
    # Calculate and display the total balance
    total_balance = sum(balance for _, balance in account_balances)
    print(f"\n[ {Fore.LIGHTYELLOW_EX}INFO{Style.RESET_ALL} ] Total Balance: {total_balance:.2f}")


def retry_failed_queries(failed_queries, account_balances):
    retries = []  # Store failed queries for another retry cycle

    for firstname, auth_token in failed_queries:
        try:
            print(f"\n\n{Fore.LIGHTCYAN_EX}==========[{Style.RESET_ALL} {Fore.LIGHTYELLOW_EX}{firstname}{Style.RESET_ALL} {Fore.LIGHTCYAN_EX}]=========={Style.RESET_ALL}")
            balance = user(auth_token)
            tasks = check_task(auth_token)
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = []
                for task in tasks:
                    task_type = task.get('type')
                    task_title = task.get('title')
                    
                    if task_type == "video":
                        futures.append(executor.submit(process_task, auth_token, task_type, task_title, 100))
                    else:
                        if not task.get('is_claimed'):
                            futures.append(executor.submit(process_task, auth_token, task_type, task_title, 100))
                
            for future in as_completed(futures):
                future.result()

            # Fetch final user details after clearing tasks
            final_balance, _ = user(auth_token)
            account_balances.append([firstname, final_balance])
            spin(auth_token)
            time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n{Fore.RED+Style.BRIGHT}Proses dihentikan paksa oleh anda!")
            break
        
        except Exception as e:
            print(f"[ {Fore.LIGHTRED_EX}ERROR{Style.RESET_ALL} ] Error retrying account {firstname}: {str(e)}")
            retries.append((firstname, auth_token))

    failed_queries.clear()  # Clear the original failed queries list
    failed_queries.extend(retries)  # Add remaining retries to the list

# Example usage
main()
