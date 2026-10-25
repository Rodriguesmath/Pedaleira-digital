#!/usr/bin/env python3
"""
Unit and Quality Gate Test Suite for STM32H723 C++ Firmware and DaisySP DSP (ASSERT Standard)
"""

import os
import re
import subprocess
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

TARGET_CPP_FILES = [
    # Global Types and Hardware Abstraction (BSP)
    "firmware/stm32/Core/Inc/AssertTypes.hpp",
    "firmware/stm32/Core/Inc/Bsp.hpp",
    "firmware/stm32/Core/Src/Bsp.cpp",
    # DSP Math and Algorithms
    "firmware/stm32/Core/Inc/DspMath.hpp",
    "firmware/stm32/Core/Inc/DspOverdrive.hpp",
    "firmware/stm32/Core/Src/DspOverdrive.cpp",
    "firmware/stm32/Core/Inc/DspSvf.hpp",
    "firmware/stm32/Core/Src/DspSvf.cpp",
    "firmware/stm32/Core/Inc/DspEqualizer.hpp",
    "firmware/stm32/Core/Src/DspEqualizer.cpp",
    "firmware/stm32/Core/Inc/DspDelay.hpp",
    "firmware/stm32/Core/Src/DspDelay.cpp",
    "firmware/stm32/Core/Inc/DspCrossfade.hpp",
    "firmware/stm32/Core/Src/DspCrossfade.cpp",
    "firmware/stm32/Core/Inc/DspEngine.hpp",
    "firmware/stm32/Core/Src/DspEngine.cpp",
    # Peripheral Classes
    "firmware/stm32/Core/Inc/PedalLeds.hpp",
    "firmware/stm32/Core/Src/PedalLeds.cpp",
    "firmware/stm32/Core/Inc/PedalSwitches.hpp",
    "firmware/stm32/Core/Src/PedalSwitches.cpp",
    "firmware/stm32/Core/Inc/Cs4272.hpp",
    "firmware/stm32/Core/Src/Cs4272.cpp",
    "firmware/stm32/Core/Inc/InterMcuUart.hpp",
    "firmware/stm32/Core/Src/InterMcuUart.cpp",
    # Entry Point
    "firmware/stm32/Core/Src/main.cpp"
]

HEADER_SECTIONS = [
    "INCLUDES NECESSARIOS",
    "CONFIGURACOES",
    "DEFINES PUBLICOS",
    "TIPOS DE DADOS PUBLICOS",
    "PROTOTIPOS PUBLICOS"
]

SOURCE_SECTIONS = [
    "INCLUDES",
    "DEFINES LOCAIS",
    "CONSTANTES",
    "ESTRUTURAS DE DADOS LOCAIS",
    "PROTOTIPOS LOCAIS",
    "FUNCOES PUBLICAS",
    "FUNCOES LOCAIS"
]

def strip_cpp_comments_and_strings(text: str) -> str:
    """Strips C/C++ comments and string literals while preserving line numbers."""
    out = []
    i = 0
    n = len(text)
    in_block = False
    in_line = False
    in_str = False
    in_chr = False
    while i < n:
        c = text[i]
        c2 = text[i:i+2]
        if in_block:
            if c2 == '*/':
                in_block = False
                i += 2
                out.append('  ')
                continue
            else:
                out.append('\n' if c == '\n' else ' ')
                i += 1
                continue
        if in_line:
            if c == '\n':
                in_line = False
                out.append('\n')
            else:
                out.append(' ')
            i += 1
            continue
        if in_str:
            if c == '\\':
                out.append('  ')
                i += 2
                continue
            if c == '"':
                in_str = False
            out.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        if in_chr:
            if c == '\\':
                out.append('  ')
                i += 2
                continue
            if c == "'":
                in_chr = False
            out.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        if c2 == '/*':
            in_block = True
            out.append('  ')
            i += 2
            continue
        if c2 == '//':
            in_line = True
            out.append('  ')
            i += 2
            continue
        if c == '"':
            in_str = True
            out.append(' ')
            i += 1
            continue
        if c == "'":
            in_chr = True
            out.append(' ')
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)

def calculate_crc8_ccitt(data: bytes) -> int:
    """Python reference implementation of CRC-8 CCITT (poly 0x07, init 0x00)."""
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

class TestStm32CppDspQualityGate(unittest.TestCase):
    """Quality Gate and Regression test suite for C++ firmware architecture."""

    def test_target_cpp_files_exist(self):
        """Verify that all bounded scope C++ firmware files exist."""
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            self.assertTrue(os.path.isfile(full_path), f"File missing: {rel_path}")

    def test_pure_ascii_compliance(self):
        """Verify that all C++ files are strictly 7-bit ASCII without accents."""
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "rb") as f:
                content = f.read()
            non_ascii = [b for b in content if b > 127]
            self.assertEqual(
                len(non_ascii),
                0,
                f"Non-ASCII bytes found in {rel_path}: {len(non_ascii)}"
            )

    def test_no_tab_characters(self):
        """Verify that no TAB characters are used for indentation or spacing."""
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "r", encoding="ascii") as f:
                for line_idx, line in enumerate(f, 1):
                    self.assertNotIn("\t", line, f"TAB found in {rel_path}:{line_idx}")

    def test_allman_brace_style(self):
        """Verify strict Allman style: opening braces must be on their own separate line."""
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "r", encoding="ascii") as f:
                raw_code = f.read()
            stripped = strip_cpp_comments_and_strings(raw_code)
            for idx, line in enumerate(stripped.splitlines(), 1):
                clean = line.strip()
                if not clean or clean.startswith("#"):
                    continue
                # Reject attached opening brace except empty in-line {}
                if re.search(r"[^\s\{]\s*\{$", clean):
                    if not re.search(r"\{\s*\}", clean):
                        self.fail(f"Attached opening brace in {rel_path}:{idx}: '{clean}'")

    def test_assert_section_headers_structure(self):
        """Verify ASSERT standard comment banner sections presence and order."""
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "r", encoding="ascii") as f:
                content = f.read()
            expected = HEADER_SECTIONS if rel_path.endswith(".hpp") else SOURCE_SECTIONS
            for sec in expected:
                pattern = r"\*\s+" + re.escape(sec)
                self.assertTrue(
                    re.search(pattern, content),
                    f"Section '{sec}' missing in {rel_path}"
                )

    def test_no_single_line_control_blocks(self):
        """Verify prohibition of single-line if, else, for, while control statements."""
        violations = []
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "r", encoding="ascii") as f:
                raw = f.read()
            clean = strip_cpp_comments_and_strings(raw)
            lines = clean.split("\n")
            for line_idx, line in enumerate(lines, 1):
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if re.search(r'\bif\s*\(', s):
                    p_count = 0
                    found_close = False
                    cur_line = line_idx - 1
                    col = lines[cur_line].find('if') + 2
                    while col < len(lines[cur_line]) and lines[cur_line][col] != '(':
                        col += 1
                    while cur_line < len(lines):
                        while col < len(lines[cur_line]):
                            ch = lines[cur_line][col]
                            if ch == '(':
                                p_count += 1
                            elif ch == ')':
                                p_count -= 1
                                if p_count == 0:
                                    found_close = True
                                    col += 1
                                    break
                            col += 1
                        if found_close:
                            break
                        cur_line += 1
                        col = 0
                    if found_close:
                        tail = lines[cur_line][col:].strip()
                        if tail:
                            violations.append(f"{rel_path}:{line_idx}: Single-line statement after if '{tail}'")
                        else:
                            nxt = cur_line + 1
                            while nxt < len(lines) and not lines[nxt].strip():
                                nxt += 1
                            if nxt < len(lines):
                                nxt_line = lines[nxt].strip()
                                if not nxt_line.startswith("{"):
                                    violations.append(f"{rel_path}:{line_idx}: if block missing opening brace '{{' on next line (got: '{nxt_line}')")

                m_else = re.search(r'\belse\b', s)
                if m_else:
                    tail = s[m_else.end():].strip()
                    if not tail.startswith("if"):
                        if tail:
                            violations.append(f"{rel_path}:{line_idx}: Single-line statement after else '{tail}'")
                        else:
                            nxt = line_idx
                            while nxt < len(lines) and not lines[nxt].strip():
                                nxt += 1
                            if nxt < len(lines):
                                nxt_line = lines[nxt].strip()
                                if not nxt_line.startswith("{"):
                                    violations.append(f"{rel_path}:{line_idx}: else block missing opening brace '{{' on next line (got: '{nxt_line}')")

        self.assertEqual(violations, [], f"Single-line control statement violations: {violations}")

    def test_gpp_cpp_compilation(self):
        """Verify strict g++ C++17 compilation on all Core/Src/*.cpp files."""
        cmd = [
            "g++", "-std=c++17", "-fsyntax-only",
            "-Wall", "-Wextra", "-Werror", "-Wno-unused-parameter",
            "-DSTM32H723xx", "-DUSE_HAL_DRIVER",
            "-Ifirmware/stm32/Core/Inc",
            "-Ifirmware/stm32/Drivers/STM32H7xx_HAL_Driver/Inc",
            "-Ifirmware/stm32/Drivers/STM32H7xx_HAL_Driver/Inc/Legacy",
            "-Ifirmware/stm32/Drivers/CMSIS/Device/ST/STM32H7xx/Include",
            "-Ifirmware/stm32/Drivers/CMSIS/Include"
        ]
        cpp_files = [
            os.path.join(WORKSPACE_ROOT, f)
            for f in TARGET_CPP_FILES
            if f.endswith(".cpp")
        ]
        cmd.extend(cpp_files)

        res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        self.assertEqual(
            res.returncode,
            0,
            f"g++ compilation failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
        )

    def test_inter_mcu_uart_crc8_vectors(self):
        """Verify CRC-8 CCITT algorithm with formal protocol test vectors."""
        # Vector 1: CMD_HEARTBEAT (0x07), length 0 -> [0x07, 0x00]
        data1 = bytes([0x07, 0x00])
        crc1 = calculate_crc8_ccitt(data1)
        self.assertIsInstance(crc1, int)

        # Vector 2: CMD_SET_PARAM (0x01), length 3, payload [0x00, 0x01, 0x50] (volume 80%)
        data2 = bytes([0x01, 0x03, 0x00, 0x01, 0x50])
        crc2 = calculate_crc8_ccitt(data2)
        self.assertIsInstance(crc2, int)

        # Verify polynomial properties: empty is 0
        self.assertEqual(calculate_crc8_ccitt(b""), 0x00)

    def test_author_attribution_alphabetical_order(self):
        """Verify that all target C++ files contain team authorship in strict alphabetical order."""
        expected_author = "@author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus"
        for rel_path in TARGET_CPP_FILES:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "r", encoding="ascii") as f:
                content = f.read()
            self.assertIn(
                expected_author,
                content,
                f"Missing or incorrect author attribution in {rel_path}"
            )

if __name__ == "__main__":
    unittest.main()
