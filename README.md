# 📧 Email Forensics & Header Analysis Tool

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

A comprehensive cybersecurity tool for analyzing email headers, detecting phishing attempts, and investigating email-based threats. This tool performs deep forensic analysis including SPF/DKIM/DMARC validation, threat detection, and trust scoring.

## 🎯 Features

### Core Capabilities
- **🔍 Header Parsing**: Extracts and analyzes all email headers
- **🛡️ Authentication Analysis**: SPF, DKIM, DMARC verification
- **🌐 IP Tracking**: Traces email routing path and originating IPs
- **⚠️ Threat Detection**: Identifies spoofing, phishing, and malicious indicators
- **📊 Trust Scoring**: Calculates overall email trustworthiness (0-100)
- **🔗 URL Analysis**: Detects suspicious URLs and shorteners
- **📝 Report Generation**: Exports detailed TXT and JSON reports

### Security Checks
- Email spoofing detection
- SPF/DKIM/DMARC authentication failures
- Suspicious TLDs (.xyz, .top, etc.)
- Phishing keyword detection
- IP-based URLs
- Reply-To mismatches
- Suspicious mailers (PHPMailer, etc.)
- URL shortener detection

## 📋 Requirements

```bash
Python 3.7+
colorama
```

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/email-forensics-tool.git
cd email-forensics-tool
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install colorama
```

## 💻 Usage

### Basic Usage

#### Analyze from File
```bash
python email_forensics.py -f headers.txt
```

#### Interactive Mode (Paste Headers)
```bash
python email_forensics.py
# Paste your email headers
# Press Ctrl+D (Unix/Mac) or Ctrl+Z (Windows) when done
```

### Advanced Usage

#### Export Reports
```bash
# Generate TXT report
python email_forensics.py -f headers.txt -o report.txt

# Generate JSON report
python email_forensics.py -f headers.txt -j results.json

# Generate both
python email_forensics.py -f headers.txt -o report.txt -j results.json
```

#### Verbose Mode
```bash
python email_forensics.py -f headers.txt -v
```

## 📖 How to Get Email Headers

### Gmail
1. Open the email
2. Click the three dots (⋮) → "Show original"
3. Copy all headers from "Original Message" section

### Outlook (Web)
1. Open the email
2. Click the three dots (...) → "View" → "View message source"
3. Copy the entire content

### Outlook (Desktop)
1. Open the email
2. File → Properties
3. Copy content from "Internet headers" box

### Apple Mail
1. Open the email
2. View → Message → All Headers
3. Copy the headers

### Thunderbird
1. Open the email
2. View → Message Source (Ctrl+U)
3. Copy the headers section

## 🔧 Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--file` | `-f` | Input file containing email headers |
| `--output` | `-o` | Output report filename (TXT format) |
| `--json` | `-j` | JSON output filename |
| `--verbose` | `-v` | Enable verbose output |
| `--help` | `-h` | Show help message |

## 📊 Understanding the Results

### Trust Score
- **80-100**: TRUSTED - Email appears legitimate
- **60-79**: QUESTIONABLE - Exercise caution
- **40-59**: SUSPICIOUS - High risk
- **0-39**: DANGEROUS - Likely malicious

### Threat Severity Levels
- **HIGH**: Critical issues requiring immediate action
- **MEDIUM**: Concerning indicators, verify carefully
- **LOW**: Minor anomalies, remain cautious

### Authentication Results
- **✓ PASS**: Authentication successful
- **✗ FAIL**: Authentication failed (red flag)
- **~ SOFTFAIL**: Questionable authentication
- **? NOT FOUND**: No authentication data
