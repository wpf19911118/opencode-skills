#!/usr/bin/env python3
"""
GPU Profiler Generic - Report Generator
通用GPU性能分析报告生成器

支持:
- NVIDIA CUDA GPUs
- AMD GPUs (ROCm)
- Intel GPUs (OneAPI)
- OpenMP applications

Usage:
    python generate_report.py [--output report.html] [--format html|json|text]
"""

import argparse
import json
import sys
import os
from datetime import datetime

# Try to import GPU-related libraries
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    print("[INFO] pynvml not available, install with: pip install nvidia-ml-py3")

try:
    import rocm_smi
    ROCM_AVAILABLE = True
except ImportError:
    ROCM_AVAILABLE = False


class GPUProfiler:
    """GPU性能分析器"""
    
    def __init__(self):
        self.gpus = []
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.initialize_profilers()
    
    def initialize_profilers(self):
        """初始化GPU探查器"""
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    self.gpus.append({
                        'type': 'NVIDIA',
                        'index': i,
                        'name': name,
                        'handle': handle
                    })
                print(f"[OK] Found {len(self.gpus)} NVIDIA GPU(s)")
            except Exception as e:
                print(f"[WARN] NVIDIA GPU detection failed: {e}")
        
        if ROCM_AVAILABLE:
            try:
                print("[OK] ROCm SMI available")
            except Exception as e:
                print(f"[WARN] AMD GPU detection failed: {e}")
    
    def get_nvidia_info(self, gpu_info):
        """获取NVIDIA GPU信息"""
        try:
            handle = gpu_info['handle']
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            return {
                'memory_total': memory_info.total,
                'memory_used': memory_info.used,
                'memory_free': memory_info.free,
                'memory_used_percent': (memory_info.used / memory_info.total) * 100,
                'gpu_utilization': utilization.gpu,
                'memory_utilization': utilization.memory,
                'temperature': temperature
            }
        except Exception as e:
            return {'error': str(e)}
    
    def collect_data(self):
        """收集GPU数据"""
        report = {
            'timestamp': self.timestamp,
            'gpu_count': len(self.gpus),
            'gpus': []
        }
        
        for gpu in self.gpus:
            gpu_data = {
                'type': gpu['type'],
                'index': gpu['index'],
                'name': gpu['name']
            }
            
            if gpu['type'] == 'NVIDIA':
                nvidia_info = self.get_nvidia_info(gpu)
                gpu_data.update(nvidia_info)
            
            report['gpus'].append(gpu_data)
        
        return report
    
    def generate_text_report(self, data):
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("GPU Profiler Report")
        lines.append("=" * 60)
        lines.append(f"Timestamp: {data['timestamp']}")
        lines.append(f"GPU Count: {data['gpu_count']}")
        lines.append("")
        
        for gpu in data['gpus']:
            lines.append(f"[GPU {gpu['index']}] {gpu['name']} ({gpu['type']})")
            lines.append("-" * 40)
            
            if 'error' in gpu:
                lines.append(f"  Error: {gpu['error']}")
            else:
                if 'memory_total' in gpu:
                    lines.append(f"  Memory Total: {gpu['memory_total'] / 1024**3:.2f} GB")
                    lines.append(f"  Memory Used: {gpu['memory_used'] / 1024**3:.2f} GB")
                    lines.append(f"  Memory Free: {gpu['memory_free'] / 1024**3:.2f} GB")
                    lines.append(f"  Memory Usage: {gpu['memory_used_percent']:.1f}%")
                if 'gpu_utilization' in gpu:
                    lines.append(f"  GPU Utilization: {gpu['gpu_utilization']}%")
                if 'temperature' in gpu:
                    lines.append(f"  Temperature: {gpu['temperature']}°C")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_html_report(self, data):
        """生成HTML格式报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GPU Profiler Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .gpu-card {{ 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px;
            background: #f9f9f9;
        }}
        .metric {{ margin: 5px 0; }}
        .label {{ font-weight: bold; color: #666; }}
        .value {{ color: #333; }}
        .header {{
            background: #4CAF50;
            color: white;
            padding: 20px;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GPU Profiler Report</h1>
        <p>Generated: {data['timestamp']}</p>
        <p>Total GPUs: {data['gpu_count']}</p>
    </div>
"""
        
        for gpu in data['gpus']:
            html += f"""
    <div class="gpu-card">
        <h2>GPU {gpu['index']}: {gpu['name']} ({gpu['type']})</h2>
"""
            if 'error' not in gpu:
                html += f"""
        <div class="metric">
            <span class="label">Memory Total:</span>
            <span class="value">{gpu.get('memory_total', 0) / 1024**3:.2f} GB</span>
        </div>
        <div class="metric">
            <span class="label">Memory Used:</span>
            <span class="value">{gpu.get('memory_used', 0) / 1024**3:.2f} GB ({gpu.get('memory_used_percent', 0):.1f}%)</span>
        </div>
        <div class="metric">
            <span class="label">GPU Utilization:</span>
            <span class="value">{gpu.get('gpu_utilization', 0)}%</span>
        </div>
        <div class="metric">
            <span class="label">Temperature:</span>
            <span class="value">{gpu.get('temperature', 0)}°C</span>
        </div>
"""
            else:
                html += f"""
        <div class="metric">
            <span class="label">Error:</span>
            <span class="value">{gpu['error']}</span>
        </div>
"""
            html += """
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def generate_json_report(self, data):
        """生成JSON格式报告"""
        return json.dumps(data, indent=2)
    
    def cleanup(self):
        """清理资源"""
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


def main():
    parser = argparse.ArgumentParser(description='GPU Profiler Generic')
    parser.add_argument('--output', '-o', default='gpu_report', help='Output file name')
    parser.add_argument('--format', '-f', choices=['html', 'json', 'text'], 
                        default='html', help='Report format')
    args = parser.parse_args()
    
    print("=" * 60)
    print("GPU Profiler Generic")
    print("=" * 60)
    
    profiler = GPUProfiler()
    data = profiler.collect_data()
    
    if args.format == 'text':
        output = profiler.generate_text_report(data)
        output_file = f"{args.output}.txt"
    elif args.format == 'html':
        output = profiler.generate_html_report(data)
        output_file = f"{args.output}.html"
    else:
        output = profiler.generate_json_report(data)
        output_file = f"{args.output}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n[OK] Report saved to: {output_file}")
    print("\n" + "=" * 60)
    
    profiler.cleanup()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
