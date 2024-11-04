import socket
import threading
import queue
import os
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((socket.gethostname(), 22222))
server_socket.listen(5)

print("SERVER IS RUNNING")
print("HOST:", server_socket.getsockname())

SECRET_KEY = "chleo"

connected_clients = queue.Queue()
verified_clients = []
file_storage_clients = []  # List to track clients that want to store files
file_retrieval_clients = []  # List to track clients that want to retrieve files

# Ensure the serverFiles directory exists
os.makedirs('serverFiles', exist_ok=True)

def connection_handler():
    while True:
        client_socket, addr = server_socket.accept()
        print(f"New connection from {addr}")
        
        connected_clients.put(client_socket)
        client_socket.send("Please provide the secret key to verify.".encode())

def verification_handler():
    while True:
        if not connected_clients.empty():
            client_socket = connected_clients.get()
            try:
                received_key = client_socket.recv(1024).decode()
                if received_key == SECRET_KEY:
                    print("Client verified successfully.")
                    verified_clients.append(client_socket)
                    client_socket.send("Verification successful! You can now access services.".encode())
                else:
                    print("Client failed verification.")
                    client_socket.send("Verification failed.".encode())
                    client_socket.close()
            except Exception as e:
                print("Error in verification:", e)
                client_socket.close()

def file_storage_handler():
    while True:
        for client_socket in list(file_storage_clients):
            try:
                client_socket.send("Please enter the filename you want to store:".encode())
                filename = client_socket.recv(1024).decode()

                if filename:
                    # Receive the file size
                    file_size = int(client_socket.recv(1024).decode())
                    client_socket.send("File size received. Start sending the file.".encode())
                    
                    # Receive the actual file content
                    file_content = b''
                    while len(file_content) < file_size:
                        chunk = client_socket.recv(4096)  # Receive in chunks
                        if not chunk:
                            break
                        file_content += chunk
                    
                    # Save the file to the serverFiles directory
                    with open(os.path.join('serverFiles', filename), 'wb') as f:
                        f.write(file_content)

                    print("A new file is added to the local storage")
                    client_socket.send(f"File '{filename}' has been stored successfully.".encode())
                    file_storage_clients.remove(client_socket)  # Remove client from list after storing
                    verified_clients.append(client_socket) # place back to the services
                else:
                    client_socket.send("No filename provided.".encode())
            
            except Exception as e:
                print("Error during file storage:", e)
                file_storage_clients.remove(client_socket)
                verified_clients.append(client_socket) # place back to the services

def file_retrieval_handler():
    while True:
        for client_socket in list(file_retrieval_clients):
            try:
                # List files available on the server
                files = os.listdir('serverFiles')
                if files:
                    file_list = "\n".join(files)
                    client_socket.send(f"Available files:\n{file_list}\nChoose a file to retrieve:".encode())

                    # Client response
                    filename = client_socket.recv(1024).decode()

                    if filename in files:
                        # Send the file size first
                        file_path = os.path.join('serverFiles', filename)
                        file_size = os.path.getsize(file_path)
                        client_socket.send(str(file_size).encode())
                        
                        # Wait for confirmation to send the file
                        confirmation = client_socket.recv(1024).decode()
                        print("Sending file to client")
                        if confirmation == "Start sending the file.":
                            with open(file_path, 'rb') as f:
                                while (chunk := f.read(4096)):
                                    client_socket.send(chunk)

                        print(f"File '{filename}' sent to client.")
                        client_socket.send(f"File '{filename}' has been sent successfully.".encode())
                        file_retrieval_clients.remove(client_socket)  # Remove client from list after retrieving
                        verified_clients.append(client_socket)  # place back to the services
                    else:
                        client_socket.send("File not found.".encode())
                else:
                    client_socket.send("No files available on the server.".encode())
            
            except Exception as e:
                print("Error during file retrieval:", e)
                file_retrieval_clients.remove(client_socket)
                verified_clients.append(client_socket)  # place back to the services

def service_handler():
    while True:
        for client_socket in list(verified_clients):
            try:
                client_socket.send("Choose service: \nStore [1] \nRetrieve [2], \nQuit[3]".encode())
                service_choice = client_socket.recv(1024).decode()

                if service_choice == "1":
                    # Add client to the file storage list
                    print("Client wants to store a file")
                    verified_clients.remove(client_socket)
                    file_storage_clients.append(client_socket)

                elif service_choice == "2":
                    print("Client wants to retrieve a file from the server")
                    # Add client to the file retrieval list
                    verified_clients.remove(client_socket)
                    file_retrieval_clients.append(client_socket)

                elif service_choice == "3":
                    client_socket.send("Connection terminated.".encode())
                    verified_clients.remove(client_socket)
                    client_socket.close()
                    print("Client disconnected.")
                
                else:
                    client_socket.send("Invalid choice. Try again.".encode())

            except Exception as e:
                print("Error interacting with client:", e)
                verified_clients.remove(client_socket)
                client_socket.close()

# Starting the server threads
threading.Thread(target=connection_handler, daemon=True).start()
threading.Thread(target=verification_handler, daemon=True).start()
threading.Thread(target=service_handler, daemon=True).start()
threading.Thread(target=file_storage_handler, daemon=True).start()
threading.Thread(target=file_retrieval_handler, daemon=True).start()

while True:
    time.sleep(1)
