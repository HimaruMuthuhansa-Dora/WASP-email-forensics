#!/usr/bin/env python3

import re
import sys
import argparse
import json
from datetime import datetime
from urllib.parse import urlparse
from colorama import Fore, Style, init
import ipaddress

init(autoreset=True)

class EmailForensics:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.headers = {}
        self.analysis = {}
        self.suspicious_tlds = [
            '.xyz', '.top', '.work', '.click', '.link', '.loan',
            '.gq', '.ml', '.ga', '.cf', '.tk', '.win', '.bid',
            '.racing', '.download', '.stream', '.science'
        ]
        self.suspicious_mailers = [
            'phpmailer', 'swiftmailer', 'python-requests',
            'python-urllib', 'curl', 'wget'
        ]
        self.phishing_keywords = [
            'verify', 'suspend', 'urgent', 'immediate action',
            'confirm your', 'update your', 'verify your account',
            'suspended account', 'unusual activity', 'click here',
            'act now', 'limited time'
        ]

    def banner(self):
        print(f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
║         EMAIL FORENSICS & HEADER ANALYSIS TOOL v2.0          ║
║          Comprehensive Cybersecurity Investigation            ║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.YELLOW}[!] For authorized security analysis and investigation only{Style.RESET_ALL}
""")

    def parse_headers(self, header_text):
        lines = header_text.split('\n')
        current_header = None
        for line in lines:
            if line and not line[0].isspace() and ':' in line:
                idx = line.index(':')
                key = line[:idx].strip()
                value = line[idx + 1:].strip()
                current_header = key
                self.headers.setdefault(key, []).append(value)
            elif current_header and line.strip():
                self.headers[current_header][-1] += ' ' + line.strip()

        if self.verbose:
            print(f"{Fore.GREEN}[+] Parsed {len(self.headers)} unique header fields{Style.RESET_ALL}\n")

    def get_header(self, key, default=''):
        return self.headers.get(key, [default])[0]

    def extract_basic_info(self):
        self.analysis['basic'] = {
            'from': self.get_header('From', 'Not found'),
            'to': self.get_header('To', 'Not found'),
            'subject': self.get_header('Subject', 'Not found'),
            'date': self.get_header('Date', 'Not found'),
            'message_id': self.get_header('Message-ID', 'Not found'),
            'return_path': self.get_header('Return-Path', 'Not found'),
            'reply_to': self.get_header('Reply-To', 'Not found'),
            'x_mailer': self.get_header('X-Mailer', 'Not found'),
            'user_agent': self.get_header('User-Agent', 'Not found')
        }

    def extract_email_address(self, text):
        m = re.search(r'<(.+?)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        return m.group(1) if m and m.group(1) else m.group(2) if m else text

    def analyze_authentication(self):
        auth = {'spf': 'NOT FOUND', 'dkim': 'NOT FOUND', 'dmarc': 'NOT FOUND', 'details': []}
        spf = self.get_header('Received-SPF', '').lower()
        if 'pass' in spf:
            auth['spf'] = 'PASS'
        elif 'fail' in spf:
            auth['spf'] = 'FAIL'
        elif 'softfail' in spf:
            auth['spf'] = 'SOFTFAIL'

        ar = self.get_header('Authentication-Results', '').lower()
        if 'dkim=pass' in ar:
            auth['dkim'] = 'PASS'
        elif 'dkim=fail' in ar:
            auth['dkim'] = 'FAIL'

        if 'dmarc=pass' in ar:
            auth['dmarc'] = 'PASS'
        elif 'dmarc=fail' in ar:
            auth['dmarc'] = 'FAIL'

        if self.get_header('ARC-Authentication-Results', ''):
            auth['details'].append(('ARC', 'FOUND'))

        self.analysis['authentication'] = auth

    def extract_routing_info(self):
        received = self.headers.get('Received', [])
        routing = {'ips': [], 'hops': [], 'total_hops': len(received)}
        ip_re = re.compile(r'\[?(\d{1,3}(?:\.\d{1,3}){3})\]?')

        for i, r in enumerate(received):
            hop = {'hop_number': len(received) - i, 'header': r, 'ips': [], 'timestamp': None}
            for ip in ip_re.findall(r):
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if not ip_obj.is_private and not ip_obj.is_loopback:
                        if ip not in routing['ips']:
                            routing['ips'].append(ip)
                        hop['ips'].append(ip)
                except:
                    pass
            t = re.search(r';\s*(.+)$', r)
            if t:
                hop['timestamp'] = t.group(1).strip()
            routing['hops'].append(hop)

        self.analysis['routing'] = routing

    def extract_urls(self):
        urls = []
        url_re = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
        for values in self.headers.values():
            for v in values:
                for u in url_re.findall(v):
                    if u not in urls:
                        urls.append(u)
        self.analysis['urls'] = urls

    def detect_threats(self):
        threats, warnings = [], []
        b = self.analysis.get('basic', {})
        a = self.analysis.get('authentication', {})
        urls = self.analysis.get('urls', [])

        f = self.extract_email_address(b.get('from', ''))
        rp = self.extract_email_address(b.get('return_path', ''))
        if f != rp and rp != 'Not found':
            threats.append({'type': 'SPOOFING', 'severity': 'HIGH'})

        if a.get('spf') == 'FAIL':
            threats.append({'type': 'SPF FAILURE', 'severity': 'HIGH'})
        if a.get('dkim') == 'FAIL':
            threats.append({'type': 'DKIM FAILURE', 'severity': 'HIGH'})
        if a.get('dmarc') == 'FAIL':
            threats.append({'type': 'DMARC FAILURE', 'severity': 'HIGH'})

        for url in urls:
            if re.search(r'https?://\d+\.\d+\.\d+\.\d+', url):
                threats.append({'type': 'IP URL', 'severity': 'HIGH'})
            d = urlparse(url).netloc.lower()
            if any(d.endswith(t) for t in self.suspicious_tlds):
                warnings.append({'type': 'SUSPICIOUS TLD', 'severity': 'MEDIUM'})

        self.analysis['threats'] = threats
        self.analysis['warnings'] = warnings

    def calculate_trust_score(self):
        score = 100
        for t in self.analysis.get('threats', []):
            score -= 15
        for w in self.analysis.get('warnings', []):
            score -= 5
        self.analysis['trust_score'] = max(0, score)

    def analyze(self, headers):
        self.parse_headers(headers)
        self.extract_basic_info()
        self.analyze_authentication()
        self.extract_routing_info()
        self.extract_urls()
        self.detect_threats()
        self.calculate_trust_score()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-f', '--file')
    p.add_argument('-o', '--output')
    p.add_argument('-j', '--json')
    p.add_argument('-v', '--verbose', action='store_true')
    a = p.parse_args()

    ef = EmailForensics(a.verbose)
    ef.banner()

    if a.file:
        with open(a.file, encoding='utf-8') as f:
            headers = f.read()
    else:
        headers = sys.stdin.read()

    if not headers.strip():
        sys.exit(1)

    ef.analyze(headers)

    if a.output:
        with open(a.output, 'w', encoding='utf-8') as f:
            f.write(json.dumps(ef.analysis, indent=2))

    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(ef.analysis, f, indent=2)


if __name__ == '__main__':
    main()
