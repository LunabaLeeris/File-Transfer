import socket
import os

host = input("Enter Server Name To Connect Unto: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((host, 22222))
    print("Connected to server")
    
    request = client_socket.recv(1024).decode()
    print("Server:", request)
    secret_key = input("Secret key: ")
    client_socket.send(secret_key.encode())
    
    result = client_socket.recv(1024).decode()
    print("Server:", result)
    
    if "Verification successful" in result:
        while True:
            service_prompt = client_socket.recv(1024).decode()
            print("Server:", service_prompt)
            
            choice = input("Enter your choice (1, 2, or 3 to quit): ")
            client_socket.send(choice.encode())

            if choice == "1":
                # Server response
                result = client_socket.recv(1024).decode()
                print("Server:", result)

                # Enter file storage mode
                filename = input("Enter the filename you want to store: ")
                file_path = os.path.join('clientFiles', filename)

                if os.path.isfile(file_path):
                    client_socket.send(filename.encode())
                    # Send the file size first
                    file_size = os.path.getsize(file_path)
                    client_socket.send(str(file_size).encode())

                    # Wait for confirmation to send the file
                    response = client_socket.recv(1024).decode()
                    print("Server: " + response)
                    if "Start sending the file" in response:
                        with open(file_path, 'rb') as f:
                            while (chunk := f.read(4096)):
                                client_socket.send(chunk)
                    
                    # Receive confirmation from the server
                    confirmation = client_socket.recv(1024).decode()
                    print("Server:", confirmation)
                else:
                    print("File does not exist in clientFiles.")
                
            elif choice == "2":
                # Wait for the list of available files
                file_list = client_socket.recv(1024).decode()
                print("Available files:\n", file_list)

                filename = input("Enter the name of the file you want to retrieve: ")
                client_socket.send(filename.encode())

                # Receive file size
                print("file size received, waiting for the server to send the file...")
                file_size = int(client_socket.recv(1024).decode())
                client_socket.send("Start sending the file.".encode())

                # Receive the actual file content
                file_content = b''
                while len(file_content) < file_size:
                    chunk = client_socket.recv(4096)  # Receive in chunks
                    if not chunk:
                        break
                    file_content += chunk

                # Save the received file
                with open(os.path.join('clientFiles', filename), 'wb') as f:
                    f.write(file_content)
                
                print(f"File '{filename}' has been retrieved and saved.")

            elif choice == "3":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please try again.")

finally:
    client_socket.close()
