import pathlib
import socket
import sys
from sys import argv

FORMAT = 'utf-8'


def check_alphanumeric_str(text: str) -> bool:
    # Check the empty string
    if not text:
        return False

    # Check each character in text
    for char in text:
        if not (char.isalnum() or char == '-'):
            return False

    return True


def check_other_materials_of_str(text: str) -> bool:

    # Check the empty string
    if not text:
        return False

    if text[0] == '.' or text[-1] == '.':
        return False

    # Check each character in text
    for char in text:
        if not (char.isalnum() or char in ['-', '.']):
            return False

    return True


def check_hostname(name_server):
    """Validate a hostname."""
    if not isinstance(name_server, str):
        return False

    parts = name_server.split('.')

    if len(parts) == 1:
        # A
        return check_alphanumeric_str(parts[-1])

    elif len(parts) == 2:
        # B.A
        return check_alphanumeric_str(parts[-1]) and check_alphanumeric_str(parts[-2])

    elif len(parts) >= 3:
        # C.B.A
        return (check_alphanumeric_str(parts[-1]) and
                check_alphanumeric_str(parts[-2]) and
                check_other_materials_of_str('.'.join(parts[:-2])))


def load_config(fobj):
    try:  # extract file and read it
        with open(fobj, 'r') as filename:
            lines = filename.readlines()

        # check if the file has only one line containing the port of the server
        if len(lines) == 1:
            print('NXDOMAIN')
            return
        # extract each information from the file
        # Step 1: extract port of server and check invalid port number
        if not lines:
            raise ValueError("INVALID CONFIGURATION")

        port_of_server_str = lines[0].strip()

        try:
            port_of_server = int(port_of_server_str)
            if not (1024 <= port_of_server <= 65535):
                raise ValueError("INVALID CONFIGURATION")
        except ValueError:
            raise ValueError("INVALID CONFIGURATION")
        # create a dictionary to attach each port number of a domain
        record = {}
        # loop through the list containing all information we extracted before except the first line
        for each_line in lines[1:]:
            # split the line and check if it's valid
            if len(each_line.strip().split(',')) != 2:
                return
            domain, port_identifier_str = each_line.strip().split(',')
            if not check_hostname(domain):
                raise ValueError("INVALID CONFIGURATION")

            try:
                port_identifier = int(port_identifier_str)
                if not (1024 <= port_identifier <= 65535):
                    raise ValueError("INVALID CONFIGURATION")
            except ValueError:
                raise ValueError("INVALID CONFIGURATION")

            # check for contradicting records
            if domain in record:  # access to dictionary
                if record.get(domain) != int(port_identifier):  # check if the domain get 2 port then print Invalid
                    raise ValueError("INVALID CONFIGURATION")
            # set the pair < key, value > in dictionary with each domain and port identifier
            record[domain] = port_identifier

        return record, port_of_server
    except Exception:
        print('INVALID CONFIGURATION')
        sys.exit()


# TODO: ADD Command -->> this is format !ADD HOSTNAME PORT\n
def add_cmd(client_socket, message: str, record: dict):
    # extract information to 3 parts domain, port, \n (because the msg u send from client need to have '\n' at the end)
    each_part = message.split()
    if len(each_part) != 3:
        return
    # check valid domain
    if not check_hostname(each_part[1]):
        # do nothing
        pass

    # check valid port as well
    if not (1024 <= int(each_part[2]) <= 65535) or not each_part[2].isdigit():
        # do nothing
        pass
    # After finishing checking, we assign each value to each placeholder
    domain, port_of_domain = each_part[1], each_part[2]
    # Overwrite if there exist a value
    record[domain] = int(port_of_domain)
    client_socket.close()


# TODO: DEL Command -->> This is format: !DEL HOSTNAME\n
def del_cmd(client_socket, message: str, record: dict):
    # extract information from client input
    each_part = message.split()
    if len(each_part) != 2:
        return

    domain = each_part[1]
    # check if domain is in file configuration
    if not (domain in record):
        pass
    # check valid domain
    if not check_hostname(each_part[1]):
        # do nothing
        pass

    # after finishing checking, we delete the domain
    record.pop(domain, None)
    client_socket.close()


# TODO: EXIT Command
def exit_cmd(client_socket):
    client_socket.close()
    sys.exit(0)


# TODO: Handle Query with some functionalities
def process_message(client_socket, message: str, record: dict):
    # attribute to server
    if message.startswith('!EXIT'):
        exit_cmd(client_socket)

    # another attribute to server
    elif message.startswith('!ADD'):
        add_cmd(client_socket, message, record)

    # final attribute to server
    elif message.startswith('!DEL'):
        del_cmd(client_socket, message, record)
    else:
        port = record.get(message, None)
        # If the hostname exists, log and send the corresponding port
        if port:
            response = str(port) + '\n'
            print(f'resolve {message} to {str(port)}')
        # If the hostname doesn't exist, log NXDOMAIN and send NXDOMAIN\n
        else:
            response = "NXDOMAIN" + '\n'
            print(f'resolve {message} to NXDOMAIN')
        try:
            client_socket.sendall(response.encode(FORMAT))
        except Exception:
            return


# TODO: Handle incomplete message
def handle_incomplete_msg(buffer, client_socket, data_from_sender, record):
    # flag = True # set the flag to extract each part of buffer
    buffer += data_from_sender
    # check if '\n' in incomplete_msg
    while "\n" in buffer:
        line, buffer = buffer.split('\n', 1)
        process_message(client_socket, line, record)


def main(args: list[str]) -> None:
    # TODO
    if not args or len(args) != 1:
        print('INVALID ARGUMENTS')
        sys.exit()

    configuration_file = args[0]
    # check configuration file does not exist, cannot be read or is invalid
    if not pathlib.Path(configuration_file).is_file():  # use pathlib module
        print("INVALID CONFIGURATION")
        sys.exit()

    # Load configuration file

    record, port_of_server = load_config(args[0])

    # create a server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # using TCP connection
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # REUSEADDR FOR MULTIPLE USER ACCESS
    server_socket.bind(("localhost", port_of_server))
    server_socket.listen()  # accept multiple connection

    while True:
        CONN, ADDR = server_socket.accept()
        buffer = ""

        while True:
            try:
                msg = CONN.recv(1024).decode(FORMAT)
                if not msg:
                    break  # Connection was closed by client
                handle_incomplete_msg(buffer, CONN, msg, record)
            except Exception:
                break
        CONN.close()


if __name__ == "__main__":
    main(argv[1:])