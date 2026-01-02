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

### Options
- `-t, --timeout`: Timeout per request (seconds), supports decimals (default: `2.0`)
- `-c, --count`: Number of retries per provider (default: `1`)
- `-w, --workers`: Number of concurrent workers (default: `100`)
- `-v, --verbose`: Show failure details on `stderr`

