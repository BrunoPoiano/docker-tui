#!/usr/bin/env python3

import curses
import subprocess
import os
import argparse

def docker_tui_menu(stdscr):
    curses.cbreak()
    stdscr.clear()
    menu_options = [[0, 'shell',"Shell"],[1, 'log',"Log"],[2, 'restart',"Restart"]]
    options = [f"{menu[0]}: {menu[2]}" for menu in menu_options]
    current_selection = 0
    title_space = 3

    title1 = "==================== Choose an Option ====================="

    stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)
            for index, option in enumerate(options):
                if index == current_selection:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(index + title_space, 0, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(index + 3, 0, option)

            footer_position = len(options) + title_space + 2
            stdscr.addstr(footer_position, 0, "Quit: <crtl+c> | move: Arrow-up, Arrow-down | Choose: <enter>")

            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(options) - 1:
                current_selection += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                # Value chosen
                break
    except KeyboardInterrupt:
        stdscr.clear()
        return

    menu_selected = menu_options[current_selection][1]

    docker_tui(stdscr, menu_selected)


def docker_tui(stdscr, mode=None):
    curses.cbreak()
    stdscr.clear()

    command = "docker ps"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)

    output, error = process.communicate()
    output = output.decode('utf-8')
    lines = output.split('\n')

    containers = []

    for index, line in enumerate(lines):
        if index > 0 and line:
            columns = line.split()
            containers.append([index, columns[0], columns[1]])

    options = [f"{container[0]}: {container[2]}" for container in containers]

    current_selection = 0
    title_space = 3

    title1 = "==================== Choose a Docker Container ====================="

    if mode == "shell":
        title1 = "==================== Choose a Docker Container to Shell into ====================="
    elif mode == "log":
        title1 = "==================== Choose a Docker Container to see logs ====================="
    elif mode == "restart":
        title1 = "==================== Choose a Docker Container to restart ====================="

    stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)

    try:
        while True:
            stdscr.clear()
            stdscr.addstr(1, (curses.COLS // 2) - (len(title1) // 2), title1)
            for index, option in enumerate(options):
                if index == current_selection:
                    stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(index + title_space, 0, option)
                    stdscr.attroff(curses.A_REVERSE)
                else:
                    stdscr.addstr(index + 3, 0, option)

            footer_position = len(options) + title_space + 2
            stdscr.addstr(footer_position, 0, "Quit: <crtl+c> | move: Arrow-up, Arrow-down | Choose: <enter>")

            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(options) - 1:
                current_selection += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                # Value chosen
                break
    except KeyboardInterrupt:
        stdscr.clear()
        return

    stdscr.clear()
    stdscr.refresh()

    container_id = containers[current_selection][1]

    if mode == "shell":
        commands = [f"docker exec -it {container_id} bash", f"docker exec -it {container_id} sh"]
    elif mode == "log":
        commands = [f"docker logs -f {container_id}"]
    elif mode == "restart":
        commands = [f"docker restart {container_id}"]
    else:
        stdscr.refresh()
        stdscr.getch()
        return

    if mode == "log":
      curses.endwin()

    for command in commands:
        subprocess.run('clear')
        result = subprocess.run(command.split(), stderr=subprocess.PIPE)
        if result.returncode == 0:
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docker TUI", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("mode", nargs='?', default='menu', help="""Specify the mode:
        'emnu'    - Open options Menu
        'shell'   - Open a shell
        'log'     - Follow container logs
        'restart' - Restart a container
        """)

    args = parser.parse_args()

    if args.mode not in ["shell", "log", 'restart', 'menu']:
        print("==================== Choose a Docker Container =====================")
        print("""Specify the mode:
            'menu'    - Open options Menu
            'shell'   - Open a shell
            'log'     - Follow container logs
            'restart' - Restart a container
            """)
    else:
        try:
            if args.mode == "menu":
              curses.wrapper(docker_tui_menu)
            else:
              curses.wrapper(docker_tui, mode=args.mode)
        except curses.error as e:
            print("")
