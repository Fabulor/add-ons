"""Focused tests for the ZNC Buffers Fabulor add-on."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import patch


PLUGIN_PATH = Path(__file__).resolve().parents[1] / "zncbuffer.py"


class FakeFabulor(ModuleType):
    EAT_NONE = 0
    EAT_ALL = 3
    PRI_HIGH = 64

    def __init__(self):
        super().__init__("fabulor")
        self.info = {"channel": "#test"}
        self.commands = []
        self.server_hooks = {}
        self.command_hooks = {}
        self.unload_hooks = []

    def get_info(self, name):
        return self.info.get(name)

    def command(self, command):
        self.commands.append(command)

    def prnt(self, message):
        self.messages = getattr(self, "messages", []) + [message]

    def hook_server(self, name, callback, userdata=None, priority=0):
        self.server_hooks[name] = callback

    def hook_command(self, name, callback, userdata=None, priority=0, help=None):
        self.command_hooks[name] = callback

    def hook_unload(self, callback, userdata=None):
        self.unload_hooks.append(callback)


class ZNCBuffersTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeFabulor()
        self.module_name = "_zncbuffer_test"
        with patch.dict(sys.modules, {"fabulor": self.api}):
            spec = importlib.util.spec_from_file_location(
                self.module_name, PLUGIN_PATH
            )
            self.module = importlib.util.module_from_spec(spec)
            sys.modules[self.module_name] = self.module
            spec.loader.exec_module(self.module)
        self.addCleanup(sys.modules.pop, self.module_name, None)

    def test_registers_menu_and_removes_it_on_unload(self):
        self.assertIn('MENU ADD "ZNC Buffers/Clear Buffer" "ZNCBUFFER CLEAR"', self.api.commands)
        self.assertIn('MENU ADD "ZNC Buffers/Play Buffer" "ZNCBUFFER PLAY"', self.api.commands)

        self.api.unload_hooks[0](None)

        self.assertEqual(
            self.api.commands[-3:],
            [
                'MENU DEL "ZNC Buffers/Play Buffer"',
                'MENU DEL "ZNC Buffers/Clear Buffer"',
                'MENU DEL "ZNC Buffers"',
            ],
        )

    def test_menu_commands_target_the_current_buffer(self):
        callback = self.api.command_hooks["ZNCBUFFER"]

        self.assertEqual(
            callback(["ZNCBUFFER", "CLEAR"], [], None),
            self.api.EAT_ALL,
        )
        self.assertEqual(self.api.commands[-1], "znc clearbuffer #test")
        self.assertEqual(self.module._recently_cleared, ["#test"])

        self.assertEqual(
            callback(["ZNCBUFFER", "PLAY"], [], None),
            self.api.EAT_ALL,
        )
        self.assertEqual(self.api.commands[-1], "znc playbuffer #test")

    def test_ignores_star_prefixed_tabs(self):
        self.api.info["channel"] = "*status"
        callback = self.api.command_hooks["ZNCBUFFER"]

        result = callback(["ZNCBUFFER", "CLEAR"], [], None)

        self.assertEqual(result, self.api.EAT_ALL)
        self.assertFalse(any(command.startswith("znc ") for command in self.api.commands))
        self.assertFalse(self.module._recently_cleared)

    def test_hides_only_matching_clear_confirmation_once(self):
        self.api.command_hooks["ZNCBUFFER"](["ZNCBUFFER", "CLEAR"], [], None)
        callback = self.api.server_hooks["PRIVMSG"]
        words = [
            ":*status!znc@znc.in",
            "PRIVMSG",
            "Me",
            "some",
            "confirmation",
            "tokens",
            "[#test]",
        ]
        word_eol = ["", "", "", "", "buffers matching #test"]

        self.assertEqual(callback(words, word_eol, None), self.api.EAT_ALL)
        self.assertEqual(callback(words, word_eol, None), self.api.EAT_NONE)

    def test_leaves_unrelated_privmsgs_untouched(self):
        callback = self.api.server_hooks["PRIVMSG"]

        result = callback(
            [":Other!user@host", "PRIVMSG", "Me", "hello", "world", "again", "[#test]"],
            ["", "", "", "", "buffers matching #test"],
            None,
        )

        self.assertEqual(result, self.api.EAT_NONE)


if __name__ == "__main__":
    unittest.main()
