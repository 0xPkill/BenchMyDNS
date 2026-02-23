## DNS Benchmark Tool

A comprehensive, feature-rich DNS performance testing and analysis tool for benchmarking DNS servers. This project was created with assistance from AI Kimi 2.5. Test multiple DNS servers simultaneously with beautiful real-time output and advanced security analysis.

## 🎯 STANDALONE EXECUTABLE AVAILABLE!

**No Python installation needed!** Download the `.exe` file and run it directly!

### 📦 Download Ready-to-Use Version

Go to the `dist/` folder and find:
- **DNS_Benchmark_Pro.exe** - Standalone Windows executable (~250MB)
- **README.txt** - Instructions for the .exe version

**Just double-click and run!** No installation required.

### System Requirements for .exe:
- Windows 10 or later
- 2GB RAM minimum
- ~300MB disk space

---

## 🆕 NEW: Beautiful Web-Based GUI!

**We now have a modern, user-friendly web interface with tabs!** No more switching between files or command line arguments.

### Quick Start with GUI:

```bash
python dns_benchmark_gui.py
```

Then open your browser to `http://localhost:8080`

**GUI Features:**
- **Tabbed Interface**: Benchmark, Results & Charts, Security Analysis, and Export tabs
- **Visual Server Selection**: Easy checkboxes to select which DNS servers to test
- **Real-time Progress**: See benchmark progress with animated progress bars
- **Beautiful Tables**: Sortable tables with all your results
- **Security Analysis**: Built-in DNSSEC checking with visual results
- **One-click Export**: Export to CSV or JSON directly from the interface

## Features

### Core Features
- **Multiple Protocol Support**: Test UDP, TCP, DNS over HTTPS (DoH), and DNS over TLS (DoT)
- **Concurrent Testing**: Test up to 50+ queries simultaneously for maximum speed
- **Beautiful CLI**: Rich terminal output with progress bars, tables, and color-coded results
- **Comprehensive Statistics**: Min, max, average, median, standard deviation, packet loss, and reliability percentages
- **Multiple Query Types**: Support for A, AAAA, MX, TXT, CNAME, NS, SOA, and PTR records

### Advanced Features
- **DNSSEC Validation**: Check if domains have valid DNSSEC signatures
- **DNS Hijacking Detection**: Compare results against trusted resolvers to detect potential hijacking
- **Cache Analysis**: Analyze DNS cache behavior and TTL values
- **Export Options**: Export results to CSV or JSON for further analysis
- **System DNS Detection**: Automatically detect and test your system's configured DNS servers

### Predefined DNS Servers
- Google DNS (8.8.8.8, 8.8.4.4)
- Cloudflare DNS (1.1.1.1, 1.0.0.1)
- Quad9 (9.9.9.9, 149.112.112.112)
- OpenDNS (208.67.222.222, 208.67.220.220)
- NextDNS, AdGuard, CleanBrowsing
- And many more...

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### 🎨 GUI Version (Recommended!)

The GUI version provides a beautiful, tabbed interface that's much easier to use:

```bash
python dns_benchmark_gui.py
```

Then open your browser and go to: **http://localhost:8080**

**GUI Tabs:**
1. **Benchmark**: Select servers, configure settings, and run tests
2. **Results & Charts**: View detailed results with statistics and performance summaries
3. **Security Analysis**: Run DNSSEC validation checks
4. **Export**: Export your results to CSV or JSON

### Command Line Version

### Basic Usage

Run the benchmark with default settings:

```bash
python dns_benchmark.py
```

### Command Line Options

```bash
# Run with 20 queries per test and 2-second timeout
python dns_benchmark.py -q 20 -t 2

# Test only UDP and TCP protocols
python dns_benchmark.py -p udp tcp

# Test specific DNS servers
python dns_benchmark.py -s 1.1.1.1 8.8.8.8 9.9.9.9

# Export results to CSV
python dns_benchmark.py -o results.csv

# Export results to JSON
python dns_benchmark.py -o results.json

# Test only system DNS servers
python dns_benchmark.py --system-only

# Test with custom domains
python dns_benchmark.py --domains google.com github.com reddit.com

# Test multiple query types
python dns_benchmark.py --types A AAAA MX

# Increase concurrent queries for faster testing
python dns_benchmark.py -c 100
```

### All Options

- `-q, --queries`: Number of queries per test (default: 10)
- `-t, --timeout`: Query timeout in seconds (default: 5.0)
- `-p, --protocols`: Protocols to test - choices: udp, tcp, doh, dot (default: udp tcp)
- `-s, --servers`: Specific DNS servers to test (IP addresses)
- `--types`: Query types to test - choices: A, AAAA, MX, TXT, CNAME, NS, SOA, PTR (default: A)
- `-c, --concurrent`: Number of concurrent queries (default: 50)
- `-o, --output`: Export results to file (.csv or .json)
- `--no-predefined`: Skip predefined server list, test only system DNS
- `--domains`: Custom domains to query
- `--system-only`: Test only system DNS servers

## Advanced Security Analysis

Run the security audit module separately:

```bash
python advanced_analysis.py
```

This will perform:
- DNSSEC validation checks
- DNS hijacking detection
- Cache behavior analysis

## Example Output

```
DNS Benchmark Results

┌─────────────────────────────────────────────────────────────────────┐
│ Summary                                                             │
├─────────────────────────────────────────────────────────────────────┤
│ Servers Tested: 12                                                  │
│ Total Queries: 480                                                  │
│ Successful: 475 (98.9%)                                             │
│ Failed: 5 (1.1%)                                                    │
└─────────────────────────────────────────────────────────────────────┘

                    Server Performance Ranking
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Rank ┃ Server             ┃ Protocol     ┃ Avg (ms) ┃ Loss %   ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│  1   │ Cloudflare Primary │ UDP          │ 12.34    │ 0.0%     │
│  2   │ Google Primary     │ UDP          │ 15.67    │ 0.0%     │
│  3   │ Quad9 Secure       │ UDP          │ 18.90    │ 1.0%     │
└──────┴────────────────────┴──────────────┴──────────┴──────────┘

Top Performers by Protocol:
  UDP: Cloudflare Primary (12.34ms)
  TCP: Google Primary (18.45ms)
```

## Performance Tips

1. **Increase concurrent queries**: Use `-c 100` or higher for faster testing on fast networks
2. **Test specific servers**: Use `-s` to test only the servers you care about
3. **Adjust timeout**: Lower the timeout with `-t 2` for faster detection of slow servers
4. **Run multiple times**: DNS performance varies, run multiple tests for accurate averages

## Troubleshooting

### Module not found errors
Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Permission errors on Linux/Mac
You may need to run with sudo for some advanced features:
```bash
sudo python dns_benchmark.py
```

### No output or slow performance
- Check your internet connection
- Try reducing concurrent queries with `-c 10`
- Increase timeout with `-t 10`

## Building Standalone Executable

Want to create your own .exe file? Here's how:

### Prerequisites
```bash
pip install pyinstaller
```

### Build the executable
```bash
python build_exe.py
```

This will create `dist/DNS_Benchmark_Pro.exe` (~250-300MB)

### What gets included?
- Python interpreter
- All required libraries (dnspython, aiohttp, nicegui, pandas, plotly)
- Web framework and UI components
- Everything needed to run standalone

### Distribute
Simply share the `.exe` file! Recipients don't need Python installed.

## Requirements

- Python 3.7+
- dnspython >= 2.3.0
- aiohttp >= 3.8.0
- rich >= 13.0.0 (optional, for beautiful output)

## License

This project is open source and available for personal and commercial use.

## Contributing

Feel free to submit issues or pull requests to improve this tool!

## Why This Tool?

This project aims to provide an open, modern, and extensible DNS benchmarking solution:
- **Open Source**: Source code is available for review and improvement
- **Cross-Platform**: Works on Windows, Mac, and Linux
- **Modern**: Uses async I/O for performance and responsiveness
- **Extensible**: Easy to add new features and protocols
- **User-Friendly**: Rich terminal and optional GUI for approachable usage

Enjoy benchmarking your DNS servers! 🚀

This project was created with assistance from AI Kimi 2.5.
