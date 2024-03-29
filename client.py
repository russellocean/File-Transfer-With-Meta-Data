import hashlib
import logging
import os
import sys
import time
from socket import *
from struct import calcsize, pack


class FileTransferClient:
    def __init__(self, host, port, hash_length=8):
        # Do not modify this logger code. You can continue to use print() commands for your code.
        # The logger is in place to ensure that you receive proper output and debugging messages from the tester
        self.logger = logging.getLogger("CLIENT")
        self.handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        self.logger.propagate = False
        self.logger.info("Initializing client...")
        # End of logger code

        self.host = host
        self.port = port
        self.client_socket = None
        self.hash_length = hash_length

    def start(self):
        """
        Initiates a connection to the server and marks the client as running. This function
        does not attempt to send or receive any messages to or from the server.

        This method is responsible for establishing a socket connection to the specified
        server using the host and port attributes set during the client's initialization.
        It creates a TCP socket object, attempts to connect to the server, and sets the
        self.is_running attribute to True upon a successful connection. It logs
        the connection attempt and reports any errors encountered during the process.

        Returns:
            True or false depending on whether the connection was successful.

        Exceptions:
            - OSError: Raised if the socket encounters a problem (e.g., network
              issue, invalid host/port).

        Usage Example:
            client = FileTransferClient(host='192.168.1.10', port=12345, hash_length=8)
            if client.start():
                ... do something ...

        Note:
            - It is important to call this method before attempting to send or receive
              messages using the client.
            - Ensure that the server is up and running at the specified host and port
              before calling this method.
        """
        try:
            self.client_socket = socket(AF_INET, SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
            self.is_running = True
            return True
        except OSError as e:
            print(f"Failed to connect to server at {self.host}:{self.port}. Error: {e}")
            return False

    def read_file(self, filepath):
        """
        Reads the contents of a file and returns the data as a byte object.

        This is a helper function. You do not need to modify it. You can use it in the send_file
        method to read the contents of a file and return the data as a byte object.
        """
        with open(filepath, "rb") as file:
            data = file.read()
            return data

    def send_file(self, filepath):
        """
        Sends a file to the server using the established connection.

        File Transfer Protocol:
        1. Pack the metadata into a bytes object using the format below, up to but not including
           the file data.
        2. Concatenate the file data to the metadata bytes object (e.g. metadata + file_data).
        3. Compute the hash of the metadata + file data and append it to the bytes object
           containing the metadata and the file data (metadata + file data + hash).
        4. Send the bytes object (i.e. metadata + file data + hash) to the server.
        5. Wait for a response from the server containing the hash of the data the server received.
        6. If the server's hash matches the hash of the data sent, the file was sent successfully.
           Return whether the file was sent successfully or not.

        Parameters:
            filepath (str): The path to the file to be sent.

        Returns:
            bool: True if the file was sent successfully, False otherwise.

        Exceptions:
            - TimeoutError: Raised if the socket times out while waiting for a response.
            - ConnectionResetError: Raised if the server resets the connection.
            - ConnectionAbortedError: Raised if the server aborts the connection.
            - OSError: Raised if the socket encounters a problem (e.g., network
              issue, invalid host/port).

        Usage Example:
            client = FileTransferClient("localhost", 5000)
            if client.start():
                client.send_file("source/test1.jpg")
        """
        print("-----------------------------------")
        print(f"Sending file: {filepath}")

        # Step 1: Encode Metadata
        print("Encoding metadata for the file.")
        metadata = self.encode_metadata(filepath)
        print(f"Metadata: {metadata}")

        # Step 2: Read File Data
        print(f"Reading file data from {filepath}.")
        file_data = self.read_file(filepath)
        print(f"File data: {str(file_data)[:50]}...{str(file_data)[-50:]}")
        print(f"File data length: {len(file_data)}")

        # Step 3: Compute Hash
        print("Computing hash for the combined metadata and file data.")
        combined_data = metadata + file_data
        hash_value = self.compute_hash(combined_data)
        print(f"Hash: {hash_value}")

        # Calculate the total size of the data packet (metadata + file data + hash)
        total_data_size = len(metadata) + len(file_data) + len(hash_value)

        # Pack the total size as a 4-byte integer
        total_size_packed = pack("!I", total_data_size)
        print(f"Total data size: {total_data_size}")

        # Prepend the total size to the data packet
        data_packet = total_size_packed + metadata + file_data + hash_value

        print(f"Data packet: {str(data_packet)[:50]}...{str(data_packet)[-50:]}")

        # Step 4: Send Data
        print(
            "Sending combined data (size + metadata + file data + hash) to the server."
        )
        self.client_socket.sendall(data_packet)
        print(f"File {filepath} sent to the server.")

        # Step 5: Receive and Verify Hash
        print("Waiting for hash verification from the server.")
        server_hash = self.client_socket.recv(self.hash_length)

        print(f"Server hash: {server_hash.hex()}")
        if server_hash == hash_value:
            print("File sent and verified successfully.")
            return True
        else:
            print("File verification failed.")
            return False

    def encode_metadata(self, filepath):
        """
        Encodes file metadata into a byte format for transmission.

        Extracts and packs file metadata, including the name, extension, creation date,
        and size, into a structured byte format. This metadata precedes the file data
        in the transmission to the server, allowing the server to reconstruct and
        verify the file upon receipt.

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
            filepath (str): The path to the file for which metadata is being encoded.

        Returns:
            bytes: The encoded metadata in bytes format ready for transmission.

        Note:
            The encoded format is designed to be unpacked by the corresponding server
            method which expects the same structure.
        """
        print("---------- Encoding Metadata -------------")

        # The following code gets the various file information you need to complete this function
        filename = os.path.basename(filepath)
        file_extension = os.path.splitext(filename)[1].replace(".", "")
        created_date = time.ctime(os.path.getctime(filepath))
        file_size = os.path.getsize(filepath)

        # Encode the metadata
        filename_bytes = filename.encode("utf-8")
        file_extension_bytes = file_extension.encode("utf-8")
        created_date_bytes = created_date.encode("utf-8")

        # Pack the metadata into a byte format
        metadata_format = "!H"  # filename length (ushort)
        metadata_format += "B"  # file extension length (ubyte)
        metadata_format += "B"  # created length (ubyte)
        metadata_format += f"{len(filename_bytes)}s"  # filename (varchar)
        metadata_format += f"{len(file_extension_bytes)}s"  # file extension (varchar)
        metadata_format += f"{len(created_date_bytes)}s"  # created (varchar)
        metadata_format += "I"  # file size (uint)
        metadata_format += "B"  # hash length (ubyte)

        print(f"Metadata size: {calcsize(metadata_format)}")
        print(f"Metadata format: {metadata_format}")
        print(f"Filename length: {len(filename_bytes)}")
        print(f"File extension length: {len(file_extension_bytes)}")
        print(f"Created length: {len(created_date_bytes)}")
        print(f"File size: {file_size}")
        print(f"Hash length: {self.hash_length}")
        print(
            f"Variable part size: {len(filename_bytes) + len(file_extension_bytes) + len(created_date_bytes)}"
        )
        print(f"Filename: {filename}")
        print(f"File extension: {file_extension}")
        print(f"Created date: {created_date}")
        print(f"Hash length type: {type(self.hash_length)}")

        metadata = pack(
            metadata_format,
            len(filename_bytes),
            len(file_extension_bytes),
            len(created_date_bytes),
            filename_bytes,
            file_extension_bytes,
            created_date_bytes,
            file_size,
            self.hash_length,
        )

        print("-----------------------------------")
        return metadata

    def compute_hash(self, data):
        """
        Computes a hash for given data using the SHAKE-128 algorithm.

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
            data (bytes): The data to be hashed.
            hash_length (int): The desired length of the hash output.

        Returns:
            bytes: The computed hash.
        """
        hash_obj = hashlib.shake_128()
        hash_obj.update(data)

        print(f"Hash length: {self.hash_length}")
        print(f"Hash: {hash_obj.digest(self.hash_length).hex()}")
        print(f"File data in compute hash: {str(data)[:50]}...{str(data)[-50:]}")
        return hash_obj.digest(self.hash_length)

    def shutdown(self):
        """
        Shuts down the client by stopping its operation and closing the socket.

        This method is responsible for cleanly terminating the client's operation.
        It indicates that the client is no longer in operation. If the client has an
        active socket connection, it closes the socket to ensure proper release of
        resources and network cleanup.

        The method logs the shutdown process, providing visibility into the client's
        state transitions. It's designed to be safely callable even if the socket is
        already closed or not initialized, preventing any unexpected exceptions during
        the shutdown process.

        Usage Example:
            client = FileTransferClient('192.168.1.10', 12345)
            if client.start():
                client.run()
                client.shutdown()

        Note:
            - Call this method to cleanly shut down the client after use or in case of an error.
            - Do NOT set client_socket to None in this method. The autograder will examine
                client_socket to ensure it is closed properly.
        """
        self.logger.info("Client is shutting down...")

        if self.client_socket:
            self.client_socket.close()

        self.is_running = False
        self.logger.removeHandler(self.handler)


if __name__ == "__main__":
    client = FileTransferClient("localhost", 9876)
    if client.start():
        client.send_file("source/test1.jpg")
        client.send_file("source/test2.jpg")
        client.shutdown()
