#!/usr/bin/env python3

import curses
import subprocess
import os
import argparse
import threading
import itertools
import time
import sys
import json

padding = 1
title_space = 3
footer_text = "Quit: <ctrl+c> | Move: <arrow-up>, <arrow-down> | Choose: <enter>"

def spinner_animation(stop_event, stdscr, row, col):
  stdscr.clear()
  spinner = itertools.cycle(['|', '/', '-', '\\'])
  while not stop_event.is_set():
    stdscr.addstr(row, col, "Running... " + next(spinner))
    stdscr.refresh()
    time.sleep(0.1)

def run_command_with_loading(command, stdscr):
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner_animation, args=(stop_event, stdscr, 2, 0))
    spinner_thread.start()

    try:
        result = subprocess.run(command.split(), stderr=subprocess.PIPE)
    except KeyboardInterrupt:
        stop_event.set()
        spinner_thread.join()
        raise
    else:
        stop_event.set()
        spinner_thread.join()

    stdscr.clear()
    stdscr.refresh()

    return result

def docker_tui_menu(stdscr):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
    menu_options = [
      [0, 'shell', "Shell"],
      [1, 'log', "Log"],
      [2, 'start', "Start"],
      [3, 'stop', "Stop"],
      [4, 'restart', "Restart"],
    ]
    options = [f"{menu[2]}" for menu in menu_options]
    current_selection = 0

    title1 = "==================== Choose an Option ====================="
    stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)
            for index, option in enumerate(options):
                if index == current_selection:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(index + title_space, padding, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(index + title_space, padding, option)

            footer_position = len(options) + title_space + 2
            stdscr.addstr(footer_position, padding, footer_text)

            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(options) - 1:
                current_selection += 1
            elif key in [10, 13]:
                break

        menu_selected = menu_options[current_selection][1]

        if menu_selected == 'start' or menu_selected == 'stop':
          docker_tui_network(stdscr, menu_selected)
        else:
          docker_tui(stdscr, menu_selected)

    except KeyboardInterrupt:
        sys.exit(0)
        pass

def docker_tui(stdscr, mode=None):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
    stdscr.clear()
    command = "docker ps"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    output = output.decode('utf-8')
    lines = output.split('\n')

    containers = []
    current_selection = 0

    for index, line in enumerate(lines):
        if index > 0 and line:
            columns = line.split()
            containers.append([index, columns[0], columns[1]])

    options = [f"{container[2]}" for container in containers]

    title1 = "==================== Choose a Docker Container ====================="

    if mode == "shell":
        title1 = "==================== Choose a Docker Container to Shell into ====================="
    elif mode == "log":
        title1 = "==================== Choose a Docker Container to see logs ====================="
    elif mode == "restart":
        title1 = "===================== Choose a Docker Container to restart ======================"

    stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)
            for index, option in enumerate(options):
                if index == current_selection:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(index + title_space, padding, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(index + title_space, padding, option)

            footer_position = len(options) + title_space + 3
            stdscr.addstr(footer_position, padding, footer_text)

            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(options) - 1:
                current_selection += 1
            elif key in [10, 13]:
                break
            elif key == 27 or key in [ord('m'), ord('M')]:
                docker_tui_menu(stdscr)

        container_id = containers[current_selection][1]

        if mode == "shell":
            commands = [f"docker exec -it {container_id} bash", f"docker exec -it {container_id} sh"]
        elif mode == "log":
            commands = [f"docker logs -f {container_id}"]
        elif mode == "restart":
            commands = [f"docker restart {container_id}"]
        else:
            return

        curses.endwin()
        for command in commands:
          result = None
          if mode == 'restart':
              result = run_command_with_loading(command, stdscr)
          else:
              result = subprocess.run(command.split(), stderr=subprocess.PIPE)

          if result and result.returncode == 0:
              sys.exit(0)

    except KeyboardInterrupt:
        sys.exit(0)
        pass

def get_container_info(container_id):
  try:
    result = subprocess.run(['docker', 'inspect', container_id], capture_output=True, text=True, check=True)
    container_info = json.loads(result.stdout)
    return container_info
  except subprocess.CalledProcessError as e:
    print(f"Error inspecting container {container_id}: {e}")
    return {}

def docker_tui_network(stdscr, mode=None):
  curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
  stdscr.bkgd(' ', curses.color_pair(1) | curses.A_BOLD)
  stdscr.clear()
  result = subprocess.run(['docker', 'ps', '-a', '-q'], capture_output=True, text=True, check=True)
  container_ids = result.stdout.strip().split('\n')

  if not container_ids:
    print("No containers found.")
    return

  title1 = f"==================== Choose a Docker Network to {mode} ====================="
  containers = []
  seen = {}
  networks = []
  current_selection = 0

  for index, container_id in enumerate(container_ids):
    container_info = get_container_info(container_id)
    if container_info:
      networks_cont = container_info[0].get('NetworkSettings', {}).get('Networks', {})
      network_names = ', '.join(networks_cont.keys())

      containers.append([index, network_names, container_id])

  for sublist in containers:
      key = sublist[1]
      if key not in seen:
          seen[key] = True
          networks.append(sublist)

  try:
    while True:
        stdscr.clear()
        stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)
        for index, option in enumerate(networks):
            if index == current_selection:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(index + title_space, padding, option[1])
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(index + title_space, padding, option[1])

        footer_position = len(networks) + title_space + 3
        stdscr.addstr(footer_position, padding, footer_text)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(networks) - 1:
            current_selection += 1
        elif key in [10, 13]:
            break
        elif key == 27 or key in [ord('m'), ord('M')]:
            docker_tui_menu(stdscr)

    container_network_name = networks[current_selection][1]

    for index, option in enumerate(containers):
      if container_network_name == option[1]:
        command = f"docker {mode} {option[2]}"
        result = run_command_with_loading(command, stdscr)

    sys.exit(0)

  except KeyboardInterrupt:
      sys.exit(0)
      pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docker TUI", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("mode", nargs='?', default='menu', help="""Specify the mode:
        'menu'    - Open options Menu
        'shell'   - Open a shell
        'log'     - Follow container logs
        'restart' - Restart a container
        'start' - Start a container
        'stop' - Stop a container
        """)

    args = parser.parse_args()

    if args.mode not in ["shell", "log", 'restart', 'menu', 'start', 'stop']:
        print("Invalid mode. Use 'menu', 'shell', 'log', or 'restart'.")
    else:
        try:
            if args.mode == "menu":
                curses.wrapper(docker_tui_menu)
            elif args.mode == "start" or args.mode == 'stop':
              curses.wrapper(docker_tui_network, args.mode)
            else:
              curses.wrapper(docker_tui, mode=args.mode)
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit(0)
        except curses.error as e:
          print('')
