import hashlib
import logging
import os
import sys
from socket import *
from struct import calcsize, unpack


class FileTransferServer:
    def __init__(self, port):
        """
        Initializes the FileTransferServer on a specified port.

        This constructor sets up the logging configuration for the server, creates a
        directory for storing received files if it doesn't already exist, and initializes
        the server with the provided port. It sets the server's running status to True.

        Parameters:
            port (int): The port number on which the server will listen for incoming connections.

        Note:
            The logger setup provided should not be modified and is used for outputting server
            status and debugging messages. The 'received_files' directory is created in the
            current working directory of the script.
        """
        # Do not modify this logger code. You can continue to use print() commands for your code.
        # The logger is in place to ensure that you receive proper output and debugging messages from the tester
        self.logger = logging.getLogger("SERVER")
        self.handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False
        self.logger.info("Initializing server...")
        # End of logger code

        # Create a directory to store received files
        if not os.path.exists("received_files"):
            os.makedirs("received_files")

        self.port = port
        self.server_socket = None
        self.is_running = True

    def start(self):
        """
        Starts the server, binding it to the specified host and port, and begins listening
        for incoming connections.

        This method sets up a TCP/IP socket, binds it to the specified port,
        and sets the server to listen for incoming connections. It also sets a
        socket timeout of 1.0 seconds and marks the server as running by setting
        self.is_running to True.

        Do NOT attempt to accept a connection or receive any messages from the client in
        this function. That will be done in the run() function.

        Returns:
            bool: True if the server successfully starts and False if an error occurs during
            socket creation or binding, indicating the server is not ready to accept connections.

        Exceptions:
            - OSError: Indicates a problem with socket creation, binding, or listening, which
            is logged for debugging purposes.

        Usage Example:
            server = FileTransferServer(port=12345)
            if server.start():
                ... do something ...

        Note:
            - This method must be called before the server begins to accept connections with
            the run() method.
        """
        try:
            self.server_socket = socket(AF_INET, SOCK_STREAM)
            self.server_socket.bind(("", self.port))
            self.server_socket.listen(5)
            print(f"Server started and listening on port {self.port}")
            return True
        except OSError as e:
            print(f"Failed to start server: {e}")
            return False

    def write_file(self, filename, data):
        """
        Saves the provided data to a file with the specified name.

        This is a helper function. You do not need to modify it. You can use it in the send_file
        method to read the contents of a file and return the data as a byte object.
        """
        with open(os.path.join("received_files", filename), "wb") as file:
            file.write(data)

    def receive_data(self, client_socket):
        """
        Receives data from the client socket in chunks until all expected data is received.

        Parameters:
            client_socket (socket): The client socket from which data is to be received.

        Returns:
            bytes: The received data.
        """
        try:
            # First, receive the size of the data, first 4 bytes contain this information
            data_size_bytes = client_socket.recv(4)
            if not data_size_bytes:
                print("Failed to receive data size.")
                return None

            data_size = unpack("!I", data_size_bytes)[0]
            print(f"Data size: {str(data_size)[:50]}")

            # Initialize an empty bytes object to hold the received data
            received_data = b""

            # Loop until all data is received
            while len(received_data) < data_size:
                # Calculate the size of the next chunk
                chunk_size = min(4096, data_size - len(received_data))
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    # If an empty chunk is received, it means the connection has been closed
                    print("Connection closed before all data was received.")
                    break
                received_data += chunk

            print(
                f"Received data: {str(received_data)[:50]}...{str(received_data)[-50:]}"
            )

            if len(received_data) == data_size:

                print("All data received successfully.")
            else:
                print("Did not receive all expected data.")

            return received_data
        except Exception as e:
            print(f"An error occurred while receiving data: {e}")
            self.shutdown()
        return None

    def run(self):
        """
        Continuously accepts client connections and handles file transfers.

        After starting the server with start(), this method listens for and accepts client
        connections. For each connection, it enters a loop to receive metadata and file data,
        computes a hash for integrity verification, save the file, and sends the hash back to
        the client. It continues accepting new connections on client disconnection until the
        server is stopped.

        As the files are often larger than a single recv() call can handle, you will need to
        repeatedly receive data from the client until the entire file is received. You will need
        to keep track of how much data you have received and compare it to the expected file size.
        Be careful not to request too MUCH data when calling receive as this could cause you
        to receive some of the next file's metadata.

        Exceptions:
            - TimeoutError: Occurs when accepting a connection times out, handled internally
            to allow the server to check if it should continue running or shut down.
            - OSError: Indicates an issue with handling the socket connection, logged for
            debugging.
            - Exception: Catches and logs any unforeseen errors to avoid crashing the server.

        Usage Example:
            server = FileTransferServer(5000)
            if server.start():
                server.run()

        Note:
            - The server must be successfully started with start() before calling run().
            - This method is blocking; it will continuously run until the server is explicitly
            shutdown with the shutdown() method.
        """
        while self.is_running:
            try:

                client_socket, address = self.server_socket.accept()
                print(f"Connection from {address} has been established.")

                while self.is_running:
                    # Step 2: Receive Data
                    received_data = self.receive_data(client_socket)
                    if not received_data:
                        # No more data, client likely closed the connection
                        self.shutdown()
                        return

                    # Step 3: Unpack Metadata
                    (
                        filename,
                        file_extension,
                        created,
                        file_size,
                        hash_length,
                        file_data,
                    ) = self.unpack_metadata(received_data)

                    # Step 4: Verify Integrity
                    # The client calculates the has from the metadata + file data and sends it to the server, so we need to do the same
                    received_hash = received_data[-hash_length:]

                    combined_data = received_data[:-hash_length]
                    computed_hash = self.compute_hash(combined_data, hash_length)

                    if computed_hash == received_hash:
                        # Step 5: Save File
                        self.write_file(filename, file_data)

                        # Step 6: Send Hash Back
                        client_socket.sendall(computed_hash)
                        print(f"Hash sent back to client. {computed_hash.hex()}")
                    else:
                        print("Data integrity verification failed.")

            except Exception as e:
                print(f"An error occurred: {e}")
                self.shutdown()

    def unpack_metadata(self, data):
        """
        Extracts file metadata from a byte sequence received from a client.

        This method parses the received metadata to extract details such as the file name,
        file type, creation date, file size, and hash length. These details are used to
        process and store the incoming file appropriately.

        Packed Data Format:
            [filename_length(ushort)] - the length of the filename
            [file_extension_length(ubyte)] - the length of the file extension
            [created_length(ubyte)] - the length of the created time string
            [filename(varchar)] - a variable length string with the name of the file
            [file_extension(varchar)] - a variable length string with the file extension
            [created(varchar)] - a variable length string with the created time string
            [file_size(uint)]  - a variable length string with the unit type being requested
            [hash_length(ubyte)]  - a variable length string with the unit type being requested
            [file_data(varchar)] - a variable length string with the file data
            [hash(varchar)] - a variable length string with the hash of the file data

        Parameters:
            - data (bytes): The byte sequence containing the encoded file metadata.

        Returns:
            - tuple: Contains the filename, file type, creation date, file size, hash length,
            and any remaining file data after the metadata. This tuple is used to handle the
            file transfer and verification process.

        Note:
            - This method is a utility function called by run() to process the incoming file
            metadata. The metadata format is expected to be consistent with the client's
            sending format.
        """
        print("---------- Unpacking Metadata -------------")

        # The client encodes like provides:
        # ---------- Encoding Metadata -------------
        # Metadata size: 45
        # Metadata format: !HBB9s3s24sIB
        # Filename length: 9
        # File extension length: 3
        # Created length: 24
        # File size: 89877
        # Hash length: 8
        # Variable part size: 36
        # Filename: test2.jpg
        # File extension: jpg
        # Created date: Fri Feb 23 11:38:47 2024
        # Hash length type: <class 'int'>
        # unpack the initial part of the metadata to get the lengths
        metadata_size = calcsize("!HBB")

        filename_length, file_extension_length, created_length = unpack(
            "!HBB", data[:metadata_size]
        )

        # Unpack the rest of the metadata to get the variable length parts
        filename = data[metadata_size : metadata_size + filename_length].decode("utf-8")

        file_extension = data[
            metadata_size
            + filename_length : metadata_size
            + filename_length
            + file_extension_length
        ].decode("utf-8")

        created = data[
            metadata_size
            + filename_length
            + file_extension_length : metadata_size
            + filename_length
            + file_extension_length
            + created_length
        ].decode("utf-8")

        file_size, hash_length = unpack(
            "!IB",
            data[
                metadata_size
                + filename_length
                + file_extension_length
                + created_length : metadata_size
                + filename_length
                + file_extension_length
                + created_length
                + 5
            ],
        )

        # Extract the file data and hash from the remaining data
        file_data = data[
            metadata_size
            + filename_length
            + file_extension_length
            + created_length
            + 5 : -hash_length
        ]

        hash_data = data[-hash_length:]

        # Return the expected tuple format
        return (filename, file_extension, created, file_size, hash_length, file_data)

    def compute_hash(self, data, hash_length):
        """
        Generates a hash of the provided data using the SHAKE-128 algorithm.

        In this assignment, we'll use the hashlib library to compute a hash of the data
        being shared between the client and the server. A hash is a fixed-length string
        generated based on arbitrary input data. The same data will result in the same
        hash, and any change to the data will result in a different hash.  We're using this
        very simplistically to introduce the idea of hashing and integrity checking, which
        we'll be exploring in more detail later in the semester.

        1. Import hashlib and call hashlib.shake_128() to create a new SHAKE-128 hash object.
        2. Use the update() method to add the data to the hash object.
        3. Use the digest() method to retrieve the hash value and return it.

        The shake_128 algorithm is convenient for us since we can specify the length of the
        hash it produces. This allows us to generate a short hash for use in our tests.

        Parameters:
            - data (bytes): Data for which the hash will be computed.
            - hash_length (int): Specifies the desired length of the hash output in bytes.

        Returns:
            - bytes: The computed hash of the data, which can be used for integrity checks.

        Note:
            - This method is used within the file transfer process to ensure the integrity
            of received data by comparing the computed hash with one provided by the client.
        """
        print("---------- Computing Hash -------------")
        hash_obj = hashlib.shake_128()
        hash_obj.update(data)

        print(f"Hash length: {hash_length}")
        print(f"Hash: {hash_obj.digest(hash_length).hex()}")
        print(f"File data in compute hash: {str(data)[:50]}...{str(data)[-50:]}")
        return hash_obj.digest(hash_length)

    def shutdown(self):
        """
        Shuts down the server by stopping its operation and closing the socket.

        This method safely terminates the server's operation. It stops the server from
        running, removes the logger handler, and closes the server socket if it is open.

        The method logs the shutdown process, providing visibility into the client's
        state transitions. It's designed to be safely callable even if the socket is
        already closed or not initialized, preventing any unexpected exceptions during
        the shutdown process.

        Usage Example:
            server.shutdown()

        Note:
            - Call this method to cleanly shut down the server after use or in case of an error.
            - Do NOT set server_socket to None in this method. The autograder will examine
                server_socket to ensure it is closed properly.
        """
        self.logger.info("Server is shutting down...")

        if self.server_socket:
            self.server_socket.close()

        self.is_running = False
        self.logger.removeHandler(self.handler)


if __name__ == "__main__":
    server = FileTransferServer(9876)
    if server.start():
        server.run()
