#!/usr/bin/env python3
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import PosixPath
from typing import List, Optional, Tuple

import requests
from pip._internal.operations.freeze import freeze
from yaspin import yaspin
from yaspin.spinners import Spinners

from mmpm.constants import color
from mmpm.logger import MMPMLogger

logger = MMPMLogger.get_logger(__name__)


def get_host_ip() -> str:
    address: str = "localhost"

    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        _socket.connect(("8.8.8.8", 80))
        address = _socket.getsockname()[0]
    except socket.gaierror as error:
        logger.error(f"Failed to determine host IP address: {error}")
    finally:
        _socket.close()

    return address


def run_cmd(command: List[str], progress=True, background=False, message: str = "") -> Tuple[int, str, str]:
    """
    Executes shell command and captures errors

    Parameters:
        command (List[str]): The command string to be executed

    Returns:
        Tuple[returncode (int), stdout (str), stderr (str)]
    """

    if background:
        logger.debug(f"Executing process `{' '.join(command)}` in background")
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0, "", ""

    logger.debug(f'Executing process `{" ".join(command)}`')

    with subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        if progress:
            with yaspin(text=message, color="green") as spinner:
                spinner.spinner = Spinners.bouncingBar

                while process.poll() is None:
                    time.sleep(0.1)

        stdout, stderr = process.communicate()

        return process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8")


def get_pids(process_name: str) -> List[str]:
    """
    Kills all processes of given name

    Parameters:
        process (str): the name of the process

    Returns:
        processes (List[str]): list of the processes IDs found
    """

    logger.info(f"Getting process IDs for {process_name} proceses")

    with subprocess.Popen(["pgrep", process_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as pids:
        stdout, _ = pids.communicate()
        processes = stdout.decode("utf-8")

        logger.info(f"Found processes: {processes}")

        return [proc_id for proc_id in processes.split("\n") if proc_id]


def kill_pids_of_process(process: str) -> None:
    """
    Kills all processes of given name

    Parameters:
        process (str): the name of the process

    Returns:
        processes (str): the processes IDs found
    """
    os.system(f"for process in $(pgrep {process}); do kill -9 $process; done")
    logger.info(f"Stopped all processes of type {process}")


def prompt(user_prompt: str, valid_ack: List[str] = ["yes", "y"], valid_nack: List[str] = ["no", "n"]) -> bool:
    """
    Prompts user with the `user_prompt` until a response matches a value in the
    `valid_ack` or `valid_nack` lists, or a KeyboardInterrupt is caught. If
    `assume_yes` is true, the `user_prompt` is printed followed by a 'yes', and
    function returns True

    Parameters:
        user_prompt (str): the text that will be presented to the user
        valid_ack (List[str]): valid 'yes' responses
        valid_nack (List[str]): valid 'no' responses
        assume_yes (bool): if True, the `user_prompt` is printed followed by 'yes'

    Returns:
        response (bool): True if the response is in the `valid_ack` list, False if in `valid_nack` or KeyboardInterrupt
    """
    response = None

    try:
        while response not in (valid_ack, valid_nack):
            response = input(f"{user_prompt} [{'/'.join(valid_ack)}] or [{'/'.join(valid_nack)}]: ")

            if response in valid_ack:
                return True
            elif response in valid_nack:
                return False
            else:
                logger.warning(f"Respond with [{'/'.join(valid_ack)}] or [{'/'.join(valid_nack)}]")

    except KeyboardInterrupt:
        print()

    return False


def validate_input(message: str, forbidden_responses: List[str] = [], reason: str = "") -> str:
    """
    Continues to prompt user with given input until the response provided is of
    non-zero length and not found in the list forbidden responses

    Parameters:
        message (str): the message given to the user
        forbidden_responses (List[str]): a list of responses the user may not supply
        reason (str): a reason why the user may not supply one of the 'forbidden_responses'

    Returns:
        user_response (str): valid, user provided input
    """
    while True:
        user_response = input(message)
        if not user_response:  # pylint: disable=no-else-continue
            logger.warning("A non-empty response must be given")
            continue
        elif user_response in forbidden_responses:
            logger.warning(f"Invalid response, {user_response} {reason}")
            continue
        return user_response


def safe_get_request(url: str) -> requests.Response:
    """
    Wrapper method around the 'requests.get' call, containing a try, except block

    Parameters:
        url (str): the url used for the API request

    Returns:
        response (requests.Response): the Reponse object, which may be empty if the request failed
    """
    try:
        data = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as error:
        logger.error(str(error))
        return requests.Response()
    return data


def update() -> bool:
    url = "https://pypi.org/pypi/mmpm/json"
    print(f"Retrieving: https://pypi.org/pypi/mmpm [{color.n_cyan('mmpm')}]")
    current_version = ""

    for requirement in freeze(local_only=False):
        info = requirement.split("==")

        if info[0] == "mmpm":
            current_version = info[1]

    contents = urllib.request.urlopen(url).read()
    latest_version = json.loads(contents)["info"]["version"]

    return latest_version == current_version


def systemctl(subcmd: str, services: List[str] = []) -> subprocess.CompletedProcess:
    """
    A wrapper around a subprocess.run call to target systemctl

    Parameters:
        subcmd (str): the systemctl subcommand, ie. stop, start, restart, status, etc
        services (List[str]): the systemd service(s) being queried

    Returns:
        process (subprocess.CompletedProcess): the completed subprocess following execution
    """
    return subprocess.run(["sudo", "systemctl", subcmd] + services, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
