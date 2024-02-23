from socket import *
from struct import pack, unpack
import os, hashlib, sys, logging


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
        # TODO: Implement the functionality described in this function's docstring
        pass


    def write_file(self, filename, data):
        """
        Saves the provided data to a file with the specified name.

        This is a helper function. You do not need to modify it. You can use it in the send_file
        method to read the contents of a file and return the data as a byte object.
        """
        with open(os.path.join("received_files", filename), "wb") as file:
            file.write(data)


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
        # TODO: Implement the functionality described in this function's docstring
        pass


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
        # TODO: Implement the functionality described in this function's docstring
        pass


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
        # TODO: Implement the functionality described in this function's docstring
        pass


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
        self.logger.info('Server is shutting down...')

        # TODO: Implement the functionality described in this function's docstring

        self.logger.removeHandler(self.handler)


if __name__ == "__main__":
    server = FileTransferServer(5000)
    if server.start():
        server.run()
