import random
import sys

from ubos.webapptest import find_commands

def main(argv):
    commands = find_commands()
    if not argv:
        synopsis_help_quit()

    command = argv[0]
    print(command)

    if command == '--help' or command == '-h':
        synopsis_help_quit(long=1)

    try:
        cls = commands[command]

        for arg in argv:
            if arg == '--help' or arg == '-h':
                synopsis_help_quit(cmd=command, long=1)

        print("Invoking webapptest command", cls)

        result = cls.run(argv[1:])

        sys.exit(not result)
    except KeyError:
        synopsis_help_quit(long=1)


def synopsis_help_quit(cmd="", help_for=None, long=False):
    commands = find_commands()
    if help_for is None:
        if long:
            print("""
            The central testing script for UBOS web application testing.
It may be invoked in the following ways:""")
        else:
            print("Synopsis:\n")

    for command in sorted(commands.keys()):
        if not help_for or command is help_for:
            cls = commands[command]
            if not hasattr(cls, "synopsis_help"):
                continue

            synopsis_help = cls.synopsis_help()

            for synopsis in sorted(synopsis_help.keys()):
                hlp = synopsis_help[synopsis]

                print(cmd + " " + command + synopsis if synopsis else "" + "\n")

                if long or help_for:
                    print(hlp + "\n\n")

    if not help_for:
        print(cmd + "--help\n")
        if long:
            print("Display help text\n\n")

        print(cmd+" <command> [<args>...] --help\n")

        if long:
            print("Display help text for this command.\n")

    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])
