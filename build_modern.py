#!/usr/bin/env python3
"""
Build the MODERN desktop version
"""

import sys

import PyInstaller.__main__


def build():
    print("=" * 70)
    print("Building DNS Benchmark Pro - MODERN VERSION")
    print("=" * 70)
    print("Features:")
    print("  - Clean, modern interface")
    print("  - Horizontal bar charts for easy comparison")
    print("  - 30+ reputable DNS servers")
    print("  - Working DNSSEC security check")
    print("  - Better data presentation")
    print()

    args = [
        "bench_my_dns_fixed.py",
        "--name=DNS_Benchmark_Modern_v9",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--hidden-import=dns.resolver",
        "--hidden-import=dns.query",
        "--hidden-import=dns.message",
        "--hidden-import=dns.rdatatype",
        "--hidden-import=dns.dnssec",
        "--hidden-import=aiohttp",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
    ]

    PyInstaller.__main__.run(args)

    print()
    print("=" * 70)
    print("SUCCESS! Build complete!")
    print("=" * 70)
    print()
    print("Your modern DNS Benchmark is at:")
    print("  dist/DNS_Benchmark_Modern_v9.exe")
    print()
    print("This version features:")
    print("  ✓ Clean, modern UI")
    print("  ✓ Horizontal bar charts (green=cached, red=uncached)")
    print("  ✓ 30+ DNS servers from reputable providers")
    print("  ✓ Working DNSSEC security analysis")
    print("  ✓ Better organized results")
    print("  ✓ Professional look and feel")
    print()


if __name__ == "__main__":
    build()
    sys.exit(0)
