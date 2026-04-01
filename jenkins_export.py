#!/usr/bin/env python3
"""
Download all Jenkins job configurations and export to a text file.
Useful for searching across all jobs for specific build steps, triggers, or configurations.
"""

import requests
import json
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from datetime import datetime

def get_jenkins_jobs(jenkins_url, username=None, password=None):
    """Fetch list of all jobs from Jenkins"""
    try:
        jobs_url = urljoin(jenkins_url, '/api/json?tree=jobs[name,url]&depth=10')
        auth = (username, password) if username and password else None
        response = requests.get(jobs_url, auth=auth, timeout=30)
        response.raise_for_status()
        return response.json().get('jobs', [])
    except Exception as e:
        print(f"❌ Error fetching jobs list: {e}")
        sys.exit(1)

def get_job_config(jenkins_url, job_name, username=None, password=None):
    """Fetch XML configuration for a specific job"""
    try:
        config_url = urljoin(jenkins_url, f'/job/{job_name}/config.xml')
        auth = (username, password) if username and password else None
        response = requests.get(config_url, auth=auth, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"⚠️  Could not fetch config for {job_name}: {e}")
        return None

def extract_build_steps(xml_config):
    """Extract human-readable build steps from Jenkins job XML"""
    steps = []
    try:
        root = ET.fromstring(xml_config)
        
        # Look for builder elements (build steps)
        for builder in root.findall('.//builder'):
            tag = builder.tag
            
            # Shell script builder
            if 'Shell' in tag:
                command = builder.findtext('command', '')
                if command:
                    steps.append(f"[Shell] {command[:200]}")
            
            # Batch script builder (Windows)
            elif 'BatchFile' in tag:
                command = builder.findtext('command', '')
                if command:
                    steps.append(f"[Batch] {command[:200]}")
            
            # Execute shell (alternative)
            elif tag == 'hudson.tasks.Shell':
                command = builder.findtext('command', '')
                if command:
                    steps.append(f"[Execute Shell] {command[:200]}")
            
            # Invoke top-level job
            elif 'Trigger' in tag or 'InvokeTopLevel' in tag:
                job = builder.findtext('job', '')
                if job:
                    steps.append(f"[Trigger Job] {job}")
            
            # Generic fallback - grab all text
            else:
                text_content = ET.tostring(builder, encoding='unicode')[:300]
                steps.append(f"[{tag}] {text_content}")
    
    except Exception as e:
        steps.append(f"[Error parsing XML: {e}]")
    
    return steps

def extract_triggers(xml_config):
    """Extract trigger configurations from Jenkins job XML"""
    triggers = []
    try:
        root = ET.fromstring(xml_config)
        
        # Cron/Poll SCM triggers
        for trigger in root.findall('.//trigger'):
            tag = trigger.tag
            
            if 'TimerTrigger' in tag:
                spec = trigger.findtext('spec', '')
                if spec:
                    triggers.append(f"[Timer] {spec}")
            
            elif 'PollSCM' in tag:
                spec = trigger.findtext('spec', '')
                if spec:
                    triggers.append(f"[Poll SCM] {spec}")
            
            elif 'CronTrigger' in tag:
                spec = trigger.findtext('spec', '')
                if spec:
                    triggers.append(f"[Cron] {spec}")
    
    except Exception as e:
        triggers.append(f"[Error parsing triggers: {e}]")
    
    return triggers

def main():
    print("🔍 Jenkins Job Configuration Exporter")
    print("=" * 60)
    
    # Get Jenkins server details
    jenkins_url = input("Enter Jenkins URL (e.g., http://jenkins.example.com): ").strip()
    if not jenkins_url:
        print("❌ Jenkins URL is required")
        sys.exit(1)
    
    use_auth = input("Does Jenkins require authentication? (y/n): ").strip().lower() == 'y'
    username = password = None
    
    if use_auth:
        username = input("Enter username: ").strip()
        password = input("Enter API token or password: ").strip()
    
    # Fetch all jobs
    print(f"\n📥 Fetching job list from {jenkins_url}...")
    jobs = get_jenkins_jobs(jenkins_url, username, password)
    print(f"✅ Found {len(jobs)} jobs")
    
    # Download and parse configurations
    output_lines = [
        f"Jenkins Job Configuration Export",
        f"Generated: {datetime.now().isoformat()}",
        f"Server: {jenkins_url}",
        f"Total Jobs: {len(jobs)}",
        "=" * 80,
        ""
    ]
    
    for idx, job in enumerate(jobs, 1):
        job_name = job.get('name', 'Unknown')
        print(f"\r[{idx}/{len(jobs)}] Processing: {job_name[:50]:<50}", end='', flush=True)
        
        config = get_job_config(jenkins_url, job_name, username, password)
        if not config:
            continue
        
        output_lines.append(f"\n{'='*80}")
        output_lines.append(f"JOB: {job_name}")
        output_lines.append(f"{'='*80}")
        
        # Extract triggers
        triggers = extract_triggers(config)
        if triggers:
            output_lines.append("\n📅 TRIGGERS:")
            for trigger in triggers:
                output_lines.append(f"  {trigger}")
        
        # Extract build steps
        steps = extract_build_steps(config)
        if steps:
            output_lines.append("\n🔨 BUILD STEPS:")
            for step in steps:
                output_lines.append(f"  {step}")
        
        # Full XML config (optional, for detailed inspection)
        output_lines.append("\n📄 FULL XML CONFIG:")
        output_lines.append("<config>")
        output_lines.extend(config.split('\n')[:50])  # First 50 lines
        output_lines.append("</config>")
    
    # Write to file
    output_file = f"jenkins_configs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    print(f"\n\n💾 Writing to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"✅ Done! File saved to {output_file}")
    print(f"\n🔎 To find the credit card job, try:")
    print(f'   grep -i "credit\|20 min\|checkup\|checkip" {output_file}')

if __name__ == '__main__':
    main()