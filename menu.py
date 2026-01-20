import inspect
from abc import ABC
from typing import Callable

from utils import async_input, async_print, clear_screen

# TODO no output does not clear previous output ?
# TODO dynamic command cascades (cool) (m3 -> m .. 3)


class BaseMenu(ABC):
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
        self.prompt = (
            ("(q)uit, " + ", ".join(f"({s[0]}){s[1:]}" for s in actions) + ": ")
            if action_string == ""
            else "(q)uit, " + action_string + ": "
        )
        self.path = name
        self.output = self.initial_output

    def _set_path(self, path: str):
        self.path = path + " > " + self.path

    def _render_menu(self) -> str:
        clear_screen()
        screen = "-" * 8 + "\n"
        screen += self.output + "\n"
        screen += ("-" * 8) + "\n"
        screen += self.path + "\n"

        self.output = ""

        return screen


class AsyncMenu(BaseMenu):
    async def loop(self) -> None:
        while True:
            await async_print(self._render_menu())
            cmd = await async_input(self.prompt)
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
                    self.output = result

                if self.is_single:
                    break

            except KeyError:
                self.output = f"'{cmd}' does not specify an action"


class Menu(BaseMenu):
    def loop(self) -> None:
        self.output = self.initial_output

        while True:
            print(self._render_menu())
            cmd = input(self.prompt)
            if cmd == "q":
                break
            try:
                action = self.actions[cmd]
                result = action()
                if isinstance(result, AsyncMenu):
                    raise Exception("cannot use AsyncMenu within Menu, only otherwise")

                if isinstance(result, Menu):
                    result._set_path(self.path)
                    result.loop()

                elif isinstance(result, str):
                    self.output = result

                if self.is_single:
                    break

            except KeyError:
                self.output = f"'{cmd}' does not specify an action"


# Tests
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
