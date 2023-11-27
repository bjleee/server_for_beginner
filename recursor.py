import socket
import time
from sys import argv
from server import check_hostname

FORMAT = 'UTF-8'
HOST = 'localhost'  # local


def check_valid_port(port: str) -> int:
    try:
        if not port:
            return False

        # Convert string to integer
        port_number = int(port)

        # Ensure it's a valid integer and within the valid port number range (1024 to 65535)
        if 1024 <= port_number <= 65535:
            return port_number
        else:
            return False

    except ValueError:
        return False


def send_query(server_port, query, timeout):
    try:
        # Create a socket to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Set a timeout for the socket operations
            sock.settimeout(timeout)

            # Connect to the server
            server_address = ('localhost', server_port)
            sock.connect(server_address)

            # Send the query
            sock.sendall(query.encode(FORMAT))

            # Receive and return the response
            response = sock.recv(1024).decode(FORMAT)
            return response

    except socket.error:
        return False  # Handle connection errors


def handle_timeout(start_time, timeout):
    # Find diff between start time and end time
    calculate_to = time.time() - start_time

    if calculate_to > timeout:
        return True  # Indicate that a timeout occurred
    else:
        return False  # No timeout occurred


def resolve_check_each_part(hostname, root_port, timeout):
    # Start timing
    start_time = time.time()
    try:
        # Check the last part of the hostname before querying the root server
        if not check_hostname(hostname.split('.')[-1]):
            print('INVALID')
            return

        # Step 1: Query the root server
        root_response = send_query(root_port, f"{hostname.split('.')[-1]}\n", timeout)
        if handle_timeout(start_time, timeout):
            print('NXDOMAIN')
            return  # Exit if timeout occurred
        if root_response == 'NXDOMAIN\n':
            print('NXDOMAIN')
            return
        if not root_response:
            print("FAILED TO CONNECT TO ROOT")
            return

        # Parse the response to get the TLD server port
        tld_port = check_valid_port(root_response.strip())

        # Check the last two parts of the hostname before querying the TLD server
        if not check_hostname(hostname.split('.')[-2]):
            print('INVALID')
            return
        auth_domain = '.'.join(hostname.split('.')[-2:])
        if not check_hostname(auth_domain):
            print('INVALID')
            return

        # Step 2: Query the TLD server
        tld_response = send_query(tld_port, f"{auth_domain}\n", timeout)
        if handle_timeout(start_time, timeout):
            print('NXDOMAIN')
            return  # Exit if timeout occurred
        if tld_response == 'NXDOMAIN\n':
            print('NXDOMAIN')
            return
        if not tld_response:
            print("FAILED TO CONNECT TO TLD")
            return

        # Parse the response to get the authoritative server port
        authoritative_port = check_valid_port(tld_response.strip())

        # Check the entire hostname before querying the authoritative server
        hostname_true = '.'.join(hostname.split('.')[0:-2])
        if not check_hostname(hostname_true):
            print('INVALID')
            return
        # Step 3: Query the authoritative server
        resolved_response = send_query(authoritative_port, f"{hostname.strip()}\n", timeout)
        if handle_timeout(start_time, timeout):
            print('NXDOMAIN')
            return  # Exit if timeout occurred
        if resolved_response == 'NXDOMAIN\n':
            print('NXDOMAIN')
            return
        if not resolved_response:
            print("FAILED TO CONNECT TO AUTH")
            return

        # Step 4: Print the resolved port
        print(resolved_response.strip())
    except Exception:
        print('INVALID')


def main(args: list[str]) -> None:
    # Check the number of command-line arguments
    if len(args) != 2:
        print("INVALID ARGUMENTS")
        return

    # Parse command-line arguments
    root_port = check_valid_port(args[0])
    timeout = float(args[1])

    # Validate the root port and timeout values
    if not root_port or timeout <= 0:
        print("INVALID ARGUMENTS")
        return

    while True:
        try:
            # Read user input
            hostname = input()
            # check length of domain
            length_domain = hostname.split('.')
            if len(length_domain) < 3 or not check_hostname(hostname):
                print('INVALID')
                continue
            # Call the resolve function to resolve the hostname
            resolve_check_each_part(hostname, root_port, timeout)

        except EOFError:
            # Handle Ctrl-D to exit gracefully
            break
        except Exception:
            print('NXDOMAIN')


if __name__ == "__main__":
    main(argv[1:])