#!/usr/bin/env python3
"""
Real-time Monitoring Script for LLM Chatbot
Monitors logs, response times, errors, and LLM classification performance
"""

import subprocess
import re
import sys
from datetime import datetime
from collections import defaultdict
import json

# ANSI Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

class LogMonitor:
    def __init__(self):
        self.stats = {
            "total_messages": 0,
            "llm_classifications": 0,
            "api_transfers": 0,
            "api_failures": 0,
            "api_retries": 0,
            "errors": defaultdict(int),
            "intents": defaultdict(int),
            "response_times": []
        }
        
    def parse_log_line(self, line: str):
        """Parse log line and extract metrics"""
        
        # Extract timestamp
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        # Track LLM classification
        if '[LLM] Classifying intent' in line:
            self.stats["llm_classifications"] += 1
            print(f"{CYAN}[LLM Classification]{RESET} {timestamp} - Intent detection in progress")
        
        # Extract classified intent
        intent_match = re.search(r'\[LLM\] Intent: (\w+)', line)
        if intent_match:
            intent = intent_match.group(1)
            self.stats["intents"][intent] += 1
            confidence_match = re.search(r'confidence: ([\d.]+)', line)
            confidence = confidence_match.group(1) if confidence_match else "N/A"
            print(f"{GREEN}[Intent Detected]{RESET} {timestamp} - Intent: {YELLOW}{intent}{RESET} (confidence: {confidence})")
        
        # Track API transfers
        if '[SalesIQ] Transfer API result' in line:
            self.stats["api_transfers"] += 1
            
        # Track API failures
        if '✗ Transfer failed' in line or 'Transfer failed' in line:
            self.stats["api_failures"] += 1
            print(f"{RED}[API Failure]{RESET} {timestamp} - Transfer failed (see details below)")
            print(f"   {line[line.find('['):].strip()}")
        
        # Track successful transfers
        if '✓ Transfer successful' in line:
            print(f"{GREEN}[Transfer Success]{RESET} {timestamp} - Chat transferred to agent")
        
        # Track API retries
        if '[Retry]' in line:
            self.stats["api_retries"] += 1
            if 'succeeded on attempt' in line:
                print(f"{YELLOW}[Retry Success]{RESET} {timestamp} - API call succeeded after retry")
            elif 'failed' in line:
                print(f"{RED}[Retry Failed]{RESET} {timestamp} - {line.split('[Retry]')[1].strip()[:80]}")
        
        # Track errors
        if '[ERROR]' in line or 'ERROR' in line:
            error_match = re.search(r'\[(.*?)\].*?(ERROR|Error).*', line)
            if error_match:
                error_type = error_match.group(1)
                self.stats["errors"][error_type] += 1
                print(f"{RED}[Error]{RESET} {timestamp} - {line.split('ERROR')[1].strip()[:100]}")
        
        # Track response times
        if 'Response generated' in line or 'Response time' in line:
            time_match = re.search(r'([\d.]+)\s*(ms|s)', line)
            if time_match:
                self.stats["response_times"].append(float(time_match.group(1)))
        
        # Track total messages
        if '[SalesIQ]' in line and 'message' in line.lower():
            self.stats["total_messages"] += 1
    
    def print_live_stats(self):
        """Print live statistics"""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}Live Statistics (Updated in real-time){RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
        
        print(f"Total Messages Processed: {BOLD}{self.stats['total_messages']}{RESET}")
        print(f"LLM Classifications:      {BOLD}{CYAN}{self.stats['llm_classifications']}{RESET}")
        print(f"API Transfers:            {BOLD}{YELLOW}{self.stats['api_transfers']}{RESET}")
        print(f"Transfer Failures:        {BOLD}{RED}{self.stats['api_failures']}{RESET}")
        print(f"Retry Attempts:           {BOLD}{YELLOW}{self.stats['api_retries']}{RESET}\n")
        
        # Intent distribution
        if self.stats["intents"]:
            print(f"{BOLD}Intent Distribution:{RESET}")
            for intent, count in sorted(self.stats["intents"].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / self.stats["llm_classifications"] * 100) if self.stats["llm_classifications"] > 0 else 0
                bar = "█" * int(percentage / 5)
                print(f"  {intent:20s} {count:3d} {CYAN}{bar}{RESET} {percentage:5.1f}%")
        
        # Errors
        if self.stats["errors"]:
            print(f"\n{BOLD}Error Summary:{RESET}")
            for error_type, count in sorted(self.stats["errors"].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {RED}•{RESET} {error_type}: {BOLD}{count}{RESET}")
        
        # Response times
        if self.stats["response_times"]:
            avg_time = sum(self.stats["response_times"]) / len(self.stats["response_times"])
            min_time = min(self.stats["response_times"])
            max_time = max(self.stats["response_times"])
            print(f"\n{BOLD}Response Times:{RESET}")
            print(f"  Average: {BOLD}{avg_time:.2f}ms{RESET}")
            print(f"  Min:     {GREEN}{min_time:.2f}ms{RESET}")
            print(f"  Max:     {RED}{max_time:.2f}ms{RESET}")
        
        print(f"\n{BLUE}{'='*70}{RESET}\n")
    
    def start_monitoring(self):
        """Start live log monitoring"""
        print(f"\n{BOLD}{CYAN}Starting real-time log monitoring...{RESET}")
        print(f"{YELLOW}Press Ctrl+C to stop and view summary{RESET}\n")
        
        try:
            # Command to tail logs from production server
            cmd = [
                'ssh', 'ubuntu@acebuddy',
                'sudo journalctl -u llm-chatbot.service -f --no-pager'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            line_count = 0
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                # Parse and display the line
                self.parse_log_line(line)
                line_count += 1
                
                # Print stats every 50 lines
                if line_count % 50 == 0:
                    self.print_live_stats()
        
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Monitoring stopped by user{RESET}")
            self.print_live_stats()
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            print(f"\nTo manually monitor logs, run:")
            print(f"  {CYAN}ssh ubuntu@acebuddy{RESET}")
            print(f"  {CYAN}sudo journalctl -u llm-chatbot.service -f --no-pager{RESET}")

def main():
    """Main entry point"""
    monitor = LogMonitor()
    
    print(f"\n{BOLD}{BLUE}╔════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{BLUE}║  LLM Chatbot Real-Time Log Monitoring                  ║{RESET}")
    print(f"{BOLD}{BLUE}╚════════════════════════════════════════════════════════╝{RESET}")
    
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
