"""Process supervisor using subprocess - Genuine OS process management"""
import subprocess
import os
import time
import signal
from pathlib import Path
from typing import Dict, Optional, List
import logging

class ProcessSupervisor:
    def __init__(self):
        self.processes = {}
        self.lock = __import__('threading').RLock()
    
    def launch_report_generator(self, report_data: Dict, output_path: Path, timeout: int = 60) -> Dict:
        """
        Launch independent helper process for report generation
        Uses subprocess.Popen with lifecycle monitoring
        """
        # Create a helper script
        helper_script = Path(__file__).parent / 'report_helper.py'
        if not helper_script.exists():
            self._create_helper_script(helper_script)
        
        with self.lock:
            try:
                cmd = ['python', str(helper_script), str(output_path)]
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=False  # No shell injection
                )
                self.processes[proc.pid] = {
                    'process': proc,
                    'type': 'report_generator',
                    'started_at': time.time()
                }
                # Send data
                import json
                stdout, stderr = proc.communicate(input=json.dumps(report_data), timeout=timeout)
                
                result = {
                    'pid': proc.pid,
                    'returncode': proc.returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'success': proc.returncode == 0
                }
                del self.processes[proc.pid]
                return result
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                raise TimeoutError(f"Process timed out after {timeout} seconds")
            except Exception as e:
                if 'proc' in locals():
                    try:
                        proc.kill()
                        proc.communicate()
                    except:
                        pass
                raise
    
    def _create_helper_script(self, path: Path):
        script = '''#!/usr/bin/env python
import sys
import json
from pathlib import Path

def main():
    try:
        output_path = sys.argv[1]
        data = json.loads(sys.stdin.read())
        # Generate simple report
        with open(output_path, 'w') as f:
            f.write("SMART CITIZEN SERVICE PORTAL - REPORT\\n")
            f.write("=" * 40 + "\\n\\n")
            for k, v in data.items():
                f.write(f"{k}: {v}\\n")
        print("Report generated successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        path.write_text(script)
    
    def terminate_process(self, pid: int, force: bool = False):
        with self.lock:
            if pid in self.processes:
                proc = self.processes[pid]['process']
                try:
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    proc.wait(timeout=5)
                except:
                    proc.kill()
                finally:
                    del self.processes[pid]
    
    def cleanup_all(self):
        for pid in list(self.processes.keys()):
            self.terminate_process(pid, force=True)
    
    def get_processes(self):
        return [{'pid': pid, **info} for pid, info in self.processes.items()]
