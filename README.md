# dohprobe

Ultra-fast DNS-over-HTTPS (DoH) probe tool.

## Installation

```bash
uv tool install https://github.com/ogpourya/dohprobe.git
```

## Usage

Reads from `stdin` and outputs working DoH URLs to `stdout`.

```bash
# Basic usage
echo "8.8.8.8" | dohprobe

# Advanced usage
cat providers.txt | dohprobe -t 0.5 -c 3 -w 200
```

### Options
- `-t, --timeout`: Timeout per request in seconds (default: `0.5`)
- `-c, --count`: Number of successful probes required (default: `3`)
- `-w, --workers`: Number of concurrent workers (default: `100`)
