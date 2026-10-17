#!/usr/bin/env python3

import re
import sys
import time
import argparse
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from colorama import Fore, Style, init
import ipaddress

init(autoreset=True)

URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'buff.ly',
    'short.io', 'rebrand.ly', 'cutt.ly', 'is.gd', 'shorte.st',
    'adf.ly', 'bc.vc', 'tiny.cc', 'ht.ly', 'lnkd.in',
}

HOMOGRAPH_CHARS = re.compile(r'[а-яЀ-Яà-ÿĀ-ſ]')


class EmailForensics:
    def __init__(self, verbose=False, no_animation=False):
        self.verbose = verbose
        self.no_animation = no_animation
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

    def animated_skull_intro(self):
        """Animated Ghost Rider flaming skull. Skipped when stdout is not a TTY."""
        if not sys.stdout.isatty() or self.no_animation:
            return

        R  = Fore.RED
        Y  = Fore.YELLOW
        W  = Fore.WHITE
        DG = '\033[90m'          # dark gray  (hollow eyes default)
        OR = '\033[38;5;208m'    # orange
        RS = Style.RESET_ALL

        skull = [
            f"  {W}      ████████████████      {RS}",
            f"  {W}    ████████████████████    {RS}",
            f"  {W}   ██████████████████████   {RS}",
            f"  {W}  ████  ░░░███████░░░  ████  {RS}",
            f"  {W}  ████  ░░░███████░░░  ████  {RS}",
            f"  {W}  ████  ░░░███████░░░  ████  {RS}",
            f"  {W}   ████████████████████████  {RS}",
            f"  {W}   ████████  ███  █████████  {RS}",
            f"  {W}   ████████  ███  █████████  {RS}",
            f"  {W}   ██████████████████████    {RS}",
            f"  {W}   █ ███ ███ ███ ███ ███ █   {RS}",
            f"  {W}   ██████████████████████    {RS}",
        ]

        # 4 animation frames of 4 flame rows each
        F = [
            [
                f"     {OR}) {R}( ) {Y}(  ) {OR}( ) {R}(  {RS}",
                f"    {Y}( ) {OR}) ( {R}) {Y}( ){OR}( ) {R}) {RS}",
                f"   {R}( ){Y} ( ) {OR}( ){R} ) {Y}( ) {OR}(  {RS}",
                f"   {Y}) {OR}( ) {R}( ) {Y}( ) {OR}( ) {R}( {RS}",
            ],
            [
                f"    {Y}(  ) {OR}( ) {R}({Y}) {OR}( {R}) {Y}(  {RS}",
                f"   {OR}) ({Y} ) {R}( ) {OR}) ({R} ) {Y}( )  {RS}",
                f"   {Y}( ){OR} ( {R}) {Y}({OR} ) {R}( ) {Y}(   {RS}",
                f"  {R}( ) {OR}( ) {Y}( ) {R}( ) {OR}( ) {Y}( {RS}",
            ],
            [
                f"   {R}( ) {Y}({OR} ) {R}( ) {Y}({OR} ) {R}( ) {RS}",
                f"   {Y}) {OR}( ) {R}({Y} ) {OR}( ) {R}({Y} )  {RS}",
                f"  {OR}( ){Y} ( ) {R}( ){OR} ( ) {Y}( ) {OR}( {RS}",
                f"  {Y}) ( {OR}( ) {R}) ({Y} ) {OR}( ) {R})   {RS}",
            ],
            [
                f"   {Y}) {OR}( {R}) {Y}({OR} ) {R}( ) {Y}({OR} ) {RS}",
                f"  {OR}( ) {Y}({R} ) {OR}( {Y}) {R}( {OR}) {Y}(   {RS}",
                f"  {R}) {Y}({OR} ) {R}( {Y}) {OR}({R} ) {Y}( ) {OR}( {RS}",
                f"  {Y}( {OR}) {R}( ) {Y}({OR} ) {R}( {Y}) {OR}( )  {RS}",
            ],
        ]

        n_flame  = len(F[0])
        n_skull  = len(skull)
        n_total  = n_flame + 1 + n_skull   # +1 blank separator line

        def _write_frame(fi, cycle):
            flames = F[fi % len(F)]
            eye_col = Y if (cycle + fi) % 2 == 0 else OR
            for line in flames:
                sys.stdout.write(line + '\n')
            sys.stdout.write('\n')
            for i, line in enumerate(skull):
                if i in (3, 4, 5):          # hollow-eye rows
                    sys.stdout.write(line.replace(DG, eye_col) + '\n')
                else:
                    sys.stdout.write(line + '\n')
            sys.stdout.flush()

        sys.stdout.write('\033[?25l')       # hide cursor
        sys.stdout.flush()
        try:
            _write_frame(0, 0)
            for cycle in range(3):          # 3 full flame cycles = 12 frames
                for fi in range(len(F)):
                    if cycle > 0 or fi > 0:
                        sys.stdout.write(f'\033[{n_total}A')
                    _write_frame(fi, cycle)
                    time.sleep(0.09)
            time.sleep(0.35)
        finally:
            sys.stdout.write('\033[?25h')   # restore cursor
            sys.stdout.flush()

    def banner(self):
        self.animated_skull_intro()
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
            'user_agent': self.get_header('User-Agent', 'Not found'),
            'content_type': self.get_header('Content-Type', 'Not found'),
            'mime_version': self.get_header('MIME-Version', 'Not found'),
        }

    def extract_email_address(self, text):
        m = re.search(r'<(.+?)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        return m.group(1) if m and m.group(1) else m.group(2) if m else text

    def extract_domain(self, email_or_addr):
        addr = self.extract_email_address(email_or_addr)
        if '@' in addr:
            return addr.split('@', 1)[1].lower().strip('>')
        return addr.lower()

    def analyze_authentication(self):
        auth = {'spf': 'NOT FOUND', 'dkim': 'NOT FOUND', 'dmarc': 'NOT FOUND', 'details': []}
        spf = self.get_header('Received-SPF', '').lower()
        if 'pass' in spf:
            auth['spf'] = 'PASS'
        elif 'fail' in spf:
            auth['spf'] = 'FAIL'
        elif 'softfail' in spf:
            auth['spf'] = 'SOFTFAIL'
        elif 'neutral' in spf:
            auth['spf'] = 'NEUTRAL'

        ar = self.get_header('Authentication-Results', '').lower()
        if 'dkim=pass' in ar:
            auth['dkim'] = 'PASS'
        elif 'dkim=fail' in ar:
            auth['dkim'] = 'FAIL'

        if 'dmarc=pass' in ar:
            auth['dmarc'] = 'PASS'
        elif 'dmarc=fail' in ar:
            auth['dmarc'] = 'FAIL'

        if 'spf=pass' in ar and auth['spf'] == 'NOT FOUND':
            auth['spf'] = 'PASS'
        elif 'spf=fail' in ar and auth['spf'] == 'NOT FOUND':
            auth['spf'] = 'FAIL'

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
                except Exception:
                    pass
            t = re.search(r';\s*(.+)$', r)
            if t:
                hop['timestamp'] = t.group(1).strip()
            routing['hops'].append(hop)

        self.analysis['routing'] = routing

    def analyze_hop_delays(self):
        """Parse timestamps from routing hops and flag unusual delays between servers."""
        hops = self.analysis.get('routing', {}).get('hops', [])
        delays = []
        parsed_times = []

        for hop in reversed(hops):
            ts = hop.get('timestamp')
            if not ts:
                continue
            try:
                dt = parsedate_to_datetime(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                parsed_times.append((hop['hop_number'], dt))
            except Exception:
                pass

        for i in range(1, len(parsed_times)):
            hop_num, t_curr = parsed_times[i]
            _, t_prev = parsed_times[i - 1]
            diff_sec = (t_curr - t_prev).total_seconds()
            entry = {
                'between_hops': f"{parsed_times[i-1][0]} -> {hop_num}",
                'delay_seconds': round(diff_sec, 1),
                'suspicious': diff_sec < 0 or diff_sec > 3600,
            }
            delays.append(entry)

        self.analysis['hop_delays'] = delays

    def extract_urls(self):
        urls = []
        url_re = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
        for values in self.headers.values():
            for v in values:
                for u in url_re.findall(v):
                    if u not in urls:
                        urls.append(u)
        self.analysis['urls'] = urls

    def detect_url_shorteners(self):
        """Flag URLs that use known link-shortening services."""
        shortened = []
        for url in self.analysis.get('urls', []):
            host = urlparse(url).netloc.lower().lstrip('www.')
            if host in URL_SHORTENERS:
                shortened.append(url)
        self.analysis['shortened_urls'] = shortened

    def detect_phishing_keywords(self):
        """Scan subject and common header values for phishing keywords."""
        found = []
        subject = self.analysis.get('basic', {}).get('subject', '').lower()
        for kw in self.phishing_keywords:
            if kw in subject:
                found.append({'keyword': kw, 'location': 'Subject'})
        self.analysis['phishing_keywords'] = found

    def check_suspicious_mailer(self):
        """Detect known mass-mailing or scripted sending agents."""
        mailer = (
            self.analysis.get('basic', {}).get('x_mailer', '') + ' ' +
            self.analysis.get('basic', {}).get('user_agent', '')
        ).lower()
        detected = [m for m in self.suspicious_mailers if m in mailer]
        self.analysis['suspicious_mailer'] = detected

    def check_reply_to_mismatch(self):
        """Detect Reply-To domain differing from From domain (common in phishing)."""
        b = self.analysis.get('basic', {})
        from_domain = self.extract_domain(b.get('from', ''))
        reply_to = b.get('reply_to', '')
        rt_domain = self.extract_domain(reply_to) if reply_to not in ('Not found', '') else None
        mismatch = bool(rt_domain and rt_domain != from_domain)
        self.analysis['reply_to_mismatch'] = {
            'from_domain': from_domain,
            'reply_to_domain': rt_domain,
            'mismatch': mismatch,
        }

    def check_homograph_domains(self):
        """Detect lookalike domains using non-ASCII / mixed-script characters."""
        b = self.analysis.get('basic', {})
        candidates = {
            'from': b.get('from', ''),
            'reply_to': b.get('reply_to', ''),
            'return_path': b.get('return_path', ''),
        }
        detected = {}
        for field, value in candidates.items():
            domain = self.extract_domain(value)
            if HOMOGRAPH_CHARS.search(domain):
                detected[field] = domain
        self.analysis['homograph_domains'] = detected

    def extract_mime_info(self):
        """Parse MIME headers: content type, boundary, and attachment indicators."""
        ct = self.get_header('Content-Type', '')
        mime = {
            'content_type': ct,
            'is_multipart': ct.lower().startswith('multipart/'),
            'boundary': None,
            'has_attachments': False,
            'attachment_names': [],
        }
        bm = re.search(r'boundary=["\']?([^"\';\s]+)', ct, re.IGNORECASE)
        if bm:
            mime['boundary'] = bm.group(1)

        for key, values in self.headers.items():
            for v in values:
                is_cd = key.lower() == 'content-disposition'
                has_att = 'attachment' in v.lower()
                if is_cd and has_att:
                    mime['has_attachments'] = True
                    fn = re.search(r'filename=["\']?([^"\';\s]+)', v, re.IGNORECASE)
                    if fn:
                        mime['attachment_names'].append(fn.group(1))

        self.analysis['mime'] = mime

    def detect_threats(self):
        threats, warnings = [], []
        b = self.analysis.get('basic', {})
        a = self.analysis.get('authentication', {})
        urls = self.analysis.get('urls', [])

        # From / Return-Path mismatch
        f = self.extract_email_address(b.get('from', ''))
        rp = self.extract_email_address(b.get('return_path', ''))
        if f != rp and rp not in ('Not found', ''):
            threats.append({'type': 'FROM/RETURN-PATH MISMATCH', 'severity': 'HIGH',
                            'detail': f'{f} vs {rp}'})

        # Reply-To domain mismatch
        rtm = self.analysis.get('reply_to_mismatch', {})
        if rtm.get('mismatch'):
            threats.append({'type': 'REPLY-TO DOMAIN MISMATCH', 'severity': 'HIGH',
                            'detail': f"{rtm['from_domain']} vs {rtm['reply_to_domain']}"})

        # Auth failures
        if a.get('spf') == 'FAIL':
            threats.append({'type': 'SPF FAILURE', 'severity': 'HIGH'})
        elif a.get('spf') == 'SOFTFAIL':
            warnings.append({'type': 'SPF SOFTFAIL', 'severity': 'MEDIUM'})
        if a.get('dkim') == 'FAIL':
            threats.append({'type': 'DKIM FAILURE', 'severity': 'HIGH'})
        if a.get('dmarc') == 'FAIL':
            threats.append({'type': 'DMARC FAILURE', 'severity': 'HIGH'})

        # IP-based URLs
        for url in urls:
            if re.search(r'https?://\d+\.\d+\.\d+\.\d+', url):
                threats.append({'type': 'IP-BASED URL', 'severity': 'HIGH', 'detail': url})
            d = urlparse(url).netloc.lower()
            if any(d.endswith(t) for t in self.suspicious_tlds):
                warnings.append({'type': 'SUSPICIOUS TLD', 'severity': 'MEDIUM', 'detail': d})

        # URL shorteners
        for url in self.analysis.get('shortened_urls', []):
            warnings.append({'type': 'URL SHORTENER', 'severity': 'MEDIUM', 'detail': url})

        # Phishing keywords
        for kw_hit in self.analysis.get('phishing_keywords', []):
            warnings.append({'type': 'PHISHING KEYWORD', 'severity': 'MEDIUM',
                             'detail': f'"{kw_hit["keyword"]}" in {kw_hit["location"]}'})

        # Suspicious mailer
        for m in self.analysis.get('suspicious_mailer', []):
            warnings.append({'type': 'SUSPICIOUS MAILER', 'severity': 'MEDIUM', 'detail': m})

        # Homograph domains
        for field, domain in self.analysis.get('homograph_domains', {}).items():
            threats.append({'type': 'HOMOGRAPH DOMAIN', 'severity': 'HIGH',
                            'detail': f'{field}: {domain}'})

        # Hop time anomalies
        for delay in self.analysis.get('hop_delays', []):
            if delay.get('suspicious'):
                sec = delay['delay_seconds']
                if sec < 0:
                    threats.append({'type': 'NEGATIVE HOP DELAY', 'severity': 'HIGH',
                                    'detail': f"{delay['between_hops']} = {sec}s"})
                else:
                    warnings.append({'type': 'LARGE HOP DELAY', 'severity': 'MEDIUM',
                                     'detail': f"{delay['between_hops']} = {sec}s"})

        self.analysis['threats'] = threats
        self.analysis['warnings'] = warnings

    def calculate_trust_score(self):
        score = 100
        for t in self.analysis.get('threats', []):
            score -= 20
        for w in self.analysis.get('warnings', []):
            score -= 5
        self.analysis['trust_score'] = max(0, score)

    def _trust_color(self, score):
        if score >= 80:
            return Fore.GREEN
        if score >= 60:
            return Fore.YELLOW
        if score >= 40:
            return Fore.MAGENTA
        return Fore.RED

    def _auth_color(self, status):
        c = {'PASS': Fore.GREEN, 'FAIL': Fore.RED, 'SOFTFAIL': Fore.YELLOW, 'NEUTRAL': Fore.CYAN}
        return c.get(status, Fore.WHITE)

    def print_report(self):
        """Print a fully formatted, colored forensic report to stdout."""
        b = self.analysis.get('basic', {})
        a = self.analysis.get('authentication', {})
        r = self.analysis.get('routing', {})
        score = self.analysis.get('trust_score', 0)
        threats = self.analysis.get('threats', [])
        warnings = self.analysis.get('warnings', [])

        sep = f"{Fore.CYAN}{'─' * 65}{Style.RESET_ALL}"

        # ── BASIC INFO ──────────────────────────────────────────────────
        print(f"\n{Fore.CYAN}{'═' * 65}")
        print(f"  BASIC INFORMATION")
        print(f"{'═' * 65}{Style.RESET_ALL}")
        for label, key in [('From', 'from'), ('To', 'to'), ('Subject', 'subject'),
                            ('Date', 'date'), ('Message-ID', 'message_id'),
                            ('Return-Path', 'return_path'), ('Reply-To', 'reply_to'),
                            ('X-Mailer', 'x_mailer')]:
            val = b.get(key, 'Not found')
            print(f"  {Fore.WHITE}{label:<14}{Style.RESET_ALL}: {val}")

        # ── MIME INFO ────────────────────────────────────────────────────
        mime = self.analysis.get('mime', {})
        if mime:
            print(f"\n{sep}")
            print(f"{Fore.CYAN}  MIME / CONTENT INFO{Style.RESET_ALL}")
            print(sep)
            print(f"  {'Content-Type':<16}: {mime.get('content_type', 'N/A')}")
            print(f"  {'Multipart':<16}: {'Yes' if mime.get('is_multipart') else 'No'}")
            if mime.get('boundary'):
                print(f"  {'Boundary':<16}: {mime['boundary']}")
            att_color = Fore.YELLOW if mime.get('has_attachments') else Fore.GREEN
            print(f"  {'Attachments':<16}: {att_color}{'Yes' if mime.get('has_attachments') else 'No'}{Style.RESET_ALL}")
            for name in mime.get('attachment_names', []):
                print(f"    {Fore.YELLOW}⚠ {name}{Style.RESET_ALL}")

        # ── AUTHENTICATION ───────────────────────────────────────────────
        print(f"\n{sep}")
        print(f"{Fore.CYAN}  AUTHENTICATION RESULTS{Style.RESET_ALL}")
        print(sep)
        for proto in ('spf', 'dkim', 'dmarc'):
            status = a.get(proto, 'NOT FOUND')
            col = self._auth_color(status)
            sym = '✓' if status == 'PASS' else ('✗' if status in ('FAIL',) else '~')
            print(f"  {proto.upper():<8}: {col}{sym} {status}{Style.RESET_ALL}")

        # ── ROUTING / IPs ────────────────────────────────────────────────
        print(f"\n{sep}")
        print(f"{Fore.CYAN}  EMAIL ROUTING{Style.RESET_ALL}")
        print(sep)
        print(f"  Total hops  : {r.get('total_hops', 0)}")
        pub_ips = r.get('ips', [])
        print(f"  Public IPs  : {len(pub_ips)}")
        for ip in pub_ips:
            print(f"    {Fore.YELLOW}→ {ip}{Style.RESET_ALL}")

        hop_delays = self.analysis.get('hop_delays', [])
        if hop_delays:
            print(f"\n  {Fore.WHITE}Hop Timing:{Style.RESET_ALL}")
            for d in hop_delays:
                col = Fore.RED if d.get('suspicious') else Fore.GREEN
                print(f"    Hops {d['between_hops']:<12} {col}{d['delay_seconds']}s{Style.RESET_ALL}"
                      + (f"  {Fore.RED}⚠ ANOMALY{Style.RESET_ALL}" if d.get('suspicious') else ''))

        # ── URLS ─────────────────────────────────────────────────────────
        urls = self.analysis.get('urls', [])
        shortened = self.analysis.get('shortened_urls', [])
        if urls:
            print(f"\n{sep}")
            print(f"{Fore.CYAN}  URLS FOUND IN HEADERS ({len(urls)}){Style.RESET_ALL}")
            print(sep)
            for u in urls:
                col = Fore.RED if u in shortened else Fore.WHITE
                tag = f" {Fore.RED}[SHORTENER]{Style.RESET_ALL}" if u in shortened else ''
                print(f"  {col}{u}{Style.RESET_ALL}{tag}")

        # ── PHISHING KEYWORDS ────────────────────────────────────────────
        kw_hits = self.analysis.get('phishing_keywords', [])
        if kw_hits:
            print(f"\n{sep}")
            print(f"{Fore.CYAN}  PHISHING KEYWORDS DETECTED{Style.RESET_ALL}")
            print(sep)
            for hit in kw_hits:
                print(f"  {Fore.YELLOW}⚠ \"{hit['keyword']}\" in {hit['location']}{Style.RESET_ALL}")

        # ── REPLY-TO MISMATCH ────────────────────────────────────────────
        rtm = self.analysis.get('reply_to_mismatch', {})
        if rtm.get('mismatch'):
            print(f"\n{sep}")
            print(f"{Fore.RED}  REPLY-TO DOMAIN MISMATCH{Style.RESET_ALL}")
            print(sep)
            print(f"  From domain     : {rtm['from_domain']}")
            print(f"  Reply-To domain : {Fore.RED}{rtm['reply_to_domain']}{Style.RESET_ALL}")

        # ── HOMOGRAPH DOMAINS ────────────────────────────────────────────
        hg = self.analysis.get('homograph_domains', {})
        if hg:
            print(f"\n{sep}")
            print(f"{Fore.RED}  HOMOGRAPH / LOOKALIKE DOMAINS DETECTED{Style.RESET_ALL}")
            print(sep)
            for field, domain in hg.items():
                print(f"  {Fore.RED}⚠ {field}: {domain}{Style.RESET_ALL}")

        # ── THREATS & WARNINGS ───────────────────────────────────────────
        print(f"\n{sep}")
        print(f"{Fore.CYAN}  THREAT SUMMARY{Style.RESET_ALL}")
        print(sep)
        if threats:
            for t in threats:
                detail = f"  — {t.get('detail', '')}" if t.get('detail') else ''
                print(f"  {Fore.RED}[HIGH] {t['type']}{Style.RESET_ALL}{Fore.RED}{detail}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}No critical threats detected{Style.RESET_ALL}")

        if warnings:
            for w in warnings:
                detail = f"  — {w.get('detail', '')}" if w.get('detail') else ''
                print(f"  {Fore.YELLOW}[MED]  {w['type']}{Style.RESET_ALL}{Fore.YELLOW}{detail}{Style.RESET_ALL}")

        # ── TRUST SCORE ──────────────────────────────────────────────────
        print(f"\n{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}")
        col = self._trust_color(score)
        if score >= 80:
            verdict = "TRUSTED"
        elif score >= 60:
            verdict = "QUESTIONABLE"
        elif score >= 40:
            verdict = "SUSPICIOUS"
        else:
            verdict = "DANGEROUS"
        bar_len = int(score * 40 / 100)
        bar = '█' * bar_len + '░' * (40 - bar_len)
        print(f"  {Fore.WHITE}TRUST SCORE : {col}{score}/100  {verdict}{Style.RESET_ALL}")
        print(f"  {col}[{bar}]{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'═' * 65}{Style.RESET_ALL}\n")

    def generate_txt_report(self):
        """Return the analysis as a plain-text string (no ANSI codes)."""
        b = self.analysis.get('basic', {})
        a = self.analysis.get('authentication', {})
        r = self.analysis.get('routing', {})
        score = self.analysis.get('trust_score', 0)
        lines = []
        lines.append("=" * 65)
        lines.append("  EMAIL FORENSICS REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("=" * 65)

        lines.append("\n[BASIC INFORMATION]")
        for label, key in [('From', 'from'), ('To', 'to'), ('Subject', 'subject'),
                            ('Date', 'date'), ('Message-ID', 'message_id'),
                            ('Return-Path', 'return_path'), ('Reply-To', 'reply_to'),
                            ('X-Mailer', 'x_mailer')]:
            lines.append(f"  {label:<14}: {b.get(key, 'Not found')}")

        mime = self.analysis.get('mime', {})
        if mime:
            lines.append("\n[MIME / CONTENT INFO]")
            lines.append(f"  Content-Type : {mime.get('content_type', 'N/A')}")
            lines.append(f"  Multipart    : {'Yes' if mime.get('is_multipart') else 'No'}")
            lines.append(f"  Attachments  : {'Yes' if mime.get('has_attachments') else 'No'}")
            for name in mime.get('attachment_names', []):
                lines.append(f"    Attachment : {name}")

        lines.append("\n[AUTHENTICATION]")
        for proto in ('spf', 'dkim', 'dmarc'):
            lines.append(f"  {proto.upper():<8}: {a.get(proto, 'NOT FOUND')}")

        lines.append("\n[ROUTING]")
        lines.append(f"  Total hops : {r.get('total_hops', 0)}")
        for ip in r.get('ips', []):
            lines.append(f"  Public IP  : {ip}")

        for d in self.analysis.get('hop_delays', []):
            flag = '  *** ANOMALY' if d.get('suspicious') else ''
            lines.append(f"  Hop delay  : {d['between_hops']} = {d['delay_seconds']}s{flag}")

        kw_hits = self.analysis.get('phishing_keywords', [])
        if kw_hits:
            lines.append("\n[PHISHING KEYWORDS]")
            for hit in kw_hits:
                lines.append(f"  \"{hit['keyword']}\" in {hit['location']}")

        shortened = self.analysis.get('shortened_urls', [])
        if shortened:
            lines.append("\n[URL SHORTENERS DETECTED]")
            for u in shortened:
                lines.append(f"  {u}")

        rtm = self.analysis.get('reply_to_mismatch', {})
        if rtm.get('mismatch'):
            lines.append("\n[REPLY-TO MISMATCH]")
            lines.append(f"  From     : {rtm['from_domain']}")
            lines.append(f"  Reply-To : {rtm['reply_to_domain']}")

        hg = self.analysis.get('homograph_domains', {})
        if hg:
            lines.append("\n[HOMOGRAPH DOMAINS]")
            for field, domain in hg.items():
                lines.append(f"  {field}: {domain}")

        lines.append("\n[THREATS]")
        for t in self.analysis.get('threats', []):
            detail = f" — {t.get('detail', '')}" if t.get('detail') else ''
            lines.append(f"  [HIGH] {t['type']}{detail}")
        if not self.analysis.get('threats'):
            lines.append("  None detected")

        lines.append("\n[WARNINGS]")
        for w in self.analysis.get('warnings', []):
            detail = f" — {w.get('detail', '')}" if w.get('detail') else ''
            lines.append(f"  [MED]  {w['type']}{detail}")
        if not self.analysis.get('warnings'):
            lines.append("  None detected")

        lines.append("\n" + "=" * 65)
        if score >= 80:
            verdict = "TRUSTED"
        elif score >= 60:
            verdict = "QUESTIONABLE"
        elif score >= 40:
            verdict = "SUSPICIOUS"
        else:
            verdict = "DANGEROUS"
        lines.append(f"  TRUST SCORE: {score}/100  [{verdict}]")
        lines.append("=" * 65)
        return '\n'.join(lines)

    def analyze(self, headers):
        self.parse_headers(headers)
        self.extract_basic_info()
        self.analyze_authentication()
        self.extract_routing_info()
        self.analyze_hop_delays()
        self.extract_urls()
        self.detect_url_shorteners()
        self.detect_phishing_keywords()
        self.check_suspicious_mailer()
        self.check_reply_to_mismatch()
        self.check_homograph_domains()
        self.extract_mime_info()
        self.detect_threats()
        self.calculate_trust_score()


def main():
    p = argparse.ArgumentParser(
        description='Email Forensics & Header Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument('-f', '--file', help='Input file containing email headers')
    p.add_argument('-o', '--output', help='Save plain-text report to file')
    p.add_argument('-j', '--json', help='Save JSON analysis to file')
    p.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    p.add_argument('--no-color', action='store_true', help='Disable colored output')
    p.add_argument('--no-animation', action='store_true', help='Skip skull animation')
    a = p.parse_args()

    if a.no_color:
        init(strip=True, autoreset=True)

    ef = EmailForensics(a.verbose, no_animation=a.no_animation)
    ef.banner()

    if a.file:
        try:
            with open(a.file, encoding='utf-8') as f:
                headers = f.read()
        except FileNotFoundError:
            print(f"{Fore.RED}[!] File not found: {a.file}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        print(f"{Fore.YELLOW}[?] Paste email headers below, then press Ctrl+D (Unix) / Ctrl+Z (Windows):{Style.RESET_ALL}\n")
        headers = sys.stdin.read()

    if not headers.strip():
        print(f"{Fore.RED}[!] No headers provided. Exiting.{Style.RESET_ALL}")
        sys.exit(1)

    ef.analyze(headers)
    ef.print_report()

    if a.output:
        try:
            with open(a.output, 'w', encoding='utf-8') as f:
                f.write(ef.generate_txt_report())
            print(f"{Fore.GREEN}[+] TXT report saved to: {a.output}{Style.RESET_ALL}")
        except IOError as e:
            print(f"{Fore.RED}[!] Could not write report: {e}{Style.RESET_ALL}")

    if a.json:
        try:
            with open(a.json, 'w', encoding='utf-8') as f:
                json.dump(ef.analysis, f, indent=2)
            print(f"{Fore.GREEN}[+] JSON analysis saved to: {a.json}{Style.RESET_ALL}")
        except IOError as e:
            print(f"{Fore.RED}[!] Could not write JSON: {e}{Style.RESET_ALL}")


if __name__ == '__main__':
    main()
