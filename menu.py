import inspect
from typing import Callable

from utils import clear_screen

# TODO no output does not clear previous output


class AsyncMenu:
    # TODO duplicate keys in submenus, q
    def __init__(
        self,
        name: str,
        actions: dict[str, Callable],
        is_single: bool = False,
        initial_output: str = "",
        action_string: str = "",
    ):
        self.is_single = is_single
        self.initial_output = initial_output
        self.actions = {s[0]: actions[s] for s in actions}
        # TODO: action string as list
        self.action_string = (
            ("(q)uit, " + ", ".join(f"({s[0]}){s[1:]}" for s in actions) + ": ")
            if action_string == ""
            else "(q)uit, " + action_string + ": "
        )
        self.path = name

    def _set_path(self, path: str):
        self.path = path + " > " + self.path

    async def loop(self) -> None:
        output = self.initial_output

        while True:
            clear_screen()
            print("-" * 8)
            print(output)
            print("-" * 8)
            print(self.path)
            cmd = input(self.action_string)
            if cmd == "q":
                break
            try:
                action = self.actions[cmd]
                # TODO: async processing indicator
                result = (
                    await action() if inspect.iscoroutinefunction(action) else action()
                )

                if isinstance(result, AsyncMenu):
                    result._set_path(self.path)
                    await result.loop()

                if isinstance(result, Menu):
                    result._set_path(self.path)
                    result.loop()

                elif isinstance(result, str):
                    output = result

                if self.is_single:
                    break

            except KeyError:
                output = f"'{cmd}' does not specify an action"
        clear_screen()


class Menu:
    # TODO dubplicate keys in submenus
    def __init__(
        self,
        name: str,
        actions: dict[str, Callable],
        is_single: bool = False,
        initial_output: str = "",
        action_string: str = "",
    ):
        self.is_single = is_single
        self.initial_output = initial_output
        self.actions = {s[0]: actions[s] for s in actions}
        self.action_string = (
            ("(q)uit, " + ", ".join(f"({s[0]}){s[1:]}" for s in actions) + ": ")
            if action_string == ""
            else "(q)uit, " + action_string + ": "
        )
        self.path = name

    def _set_path(self, path: str):
        self.path = path + " > " + self.path

    def loop(self) -> None:
        output = self.initial_output

        while True:
            clear_screen()
            print("-" * 8)
            print(output)
            print("-" * 8)
            print(self.path)
            cmd = input(self.action_string)
            if cmd == "q":
                break
            try:
                action = self.actions[cmd]
                result = action()
                if isinstance(result, Menu):
                    result._set_path(self.path)
                    result.loop()
                elif isinstance(result, str):
                    output = result

                if self.is_single:
                    break

            except KeyError:
                output = f"'{cmd}' does not specify an action"
        clear_screen()


async def async_main():
    def with_context() -> Menu:
        x = 10

        def add(y) -> str:
            nonlocal x
            x += y
            return f"x is {x}"

        return Menu(
            name="x-counter",
            actions={"increase x": lambda: add(1), "decrease x": lambda: add(-1)},
            initial_output=add(0),
        )

    async def take_nap() -> str:
        await asyncio.sleep(3)
        return "sleep was refreshing"

    await AsyncMenu(
        name="root",
        actions={
            "normal": lambda: Menu(
                name="menu a",
                actions={
                    "print hello world": lambda: "hello world",
                    "get name": lambda: "root",
                },
            ),
            "unnormal": lambda: AsyncMenu(
                name="menu b",
                actions={
                    "submenu": with_context,
                    "take a nap": take_nap,
                },
            ),
        },
    ).loop()
    print("program finished")


import asyncio

if __name__ == "__main__":
    asyncio.run(async_main())
