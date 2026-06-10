import subprocess
import re
import os
import json
import sys

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError as e:
    print(f"需要安装依赖库: {e}")
    sys.exit(1)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".gateway_changer_config.json")

class GatewayApp:
    def __init__(self):
        self.config = self.load_config()
        self.current_mode = self.detect_current_mode()
    
    def load_config(self):
        default_config = {
            "adapter_index": "",
            "custom_gateway": "192.168.1.1"
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_config
        return default_config
    
    def save_config(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def get_network_adapters(self):
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        adapters = []
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[3:]:
                line = line.strip()
                if not line:
                    continue
                parts = re.split(r'\s+', line)
                if len(parts) >= 5:
                    idx = parts[0]
                    name = ' '.join(parts[4:])
                    gateway = self.get_current_gateway(idx)
                    adapters.append({'index': idx, 'name': name, 'gateway': gateway})
        return adapters
    
    def get_current_gateway(self, adapter_index):
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'config', adapter_index],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        gateway_pattern = re.compile(r'默认网关\s*:\s*(.*)')
        if result.stdout:
            match = gateway_pattern.search(result.stdout)
            if match:
                return match.group(1).strip()
        return '无'
    
    def set_custom_gateway(self):
        if not self.config['adapter_index']:
            messagebox.showwarning("警告", "请先选择网络适配器")
            return
        
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'set', 'address', 
             self.config['adapter_index'], 'gateway=' + self.config['custom_gateway']],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            messagebox.showinfo("成功", f"已切换到自定义网关\n{self.config['custom_gateway']}")
            self.update_ui()
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            messagebox.showerror("错误", f"设置网关失败！\n{error_msg}")
    
    def set_dhcp(self):
        if not self.config['adapter_index']:
            messagebox.showwarning("警告", "请先选择网络适配器")
            return
        
        subprocess.run(
            ['netsh', 'interface', 'ipv4', 'delete', 'route', '0.0.0.0/0', 
             'interface=' + self.config['adapter_index']],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'set', 'address', 
             self.config['adapter_index'], 'dhcp'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            messagebox.showinfo("成功", "已切换到DHCP自动获取")
            self.update_ui()
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            messagebox.showerror("错误", f"切换DHCP失败！\n{error_msg}")
    
    def detect_current_mode(self):
        if not self.config['adapter_index']:
            return 'unknown'
        
        gateway = self.get_current_gateway(self.config['adapter_index'])
        if gateway == self.config['custom_gateway']:
            return 'custom'
        else:
            return 'dhcp'
    
    def is_valid_ip(self, ip):
        pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
        match = pattern.match(ip)
        if not match:
            return False
        for part in match.groups():
            if int(part) > 255:
                return False
        return True
    
    def update_ui(self):
        self.current_mode = self.detect_current_mode()
        
        mode_text = "未知"
        mode_color = '#7f8c8d'
        if self.current_mode == 'custom':
            mode_text = f"自定义网关 ({self.config['custom_gateway']})"
            mode_color = '#0078d4'
        elif self.current_mode == 'dhcp':
            mode_text = "DHCP 自动获取"
            mode_color = '#27ae60'
        
        self.mode_label.config(text=f"当前模式: {mode_text}", foreground=mode_color)
        
        other_mode = "自定义网关" if self.current_mode == 'custom' else "DHCP"
        self.switch_btn.config(text=f"切换到 {other_mode}")
        
        self.adapter_list.delete(0, tk.END)
        adapters = self.get_network_adapters()
        for adapter in adapters:
            self.adapter_list.insert(tk.END, f"{adapter['name']} (网关: {adapter['gateway']})")
            if adapter['index'] == self.config['adapter_index']:
                self.adapter_list.selection_set(tk.END)
    
    def select_adapter(self, event):
        selection = self.adapter_list.curselection()
        if selection:
            index = selection[0]
            adapters = self.get_network_adapters()
            if index < len(adapters):
                adapter = adapters[index]
                self.config['adapter_index'] = adapter['index']
                self.save_config()
                self.update_ui()
    
    def save_gateway(self):
        gateway = self.gateway_entry.get().strip()
        if self.is_valid_ip(gateway):
            self.config['custom_gateway'] = gateway
            self.save_config()
            messagebox.showinfo("保存成功", "网关地址已更新")
        else:
            messagebox.showwarning("无效地址", "请输入有效的IP地址")
    
    def run(self):
        self.root = tk.Tk()
        self.root.title("网络网关修改工具")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', pady=15)
        
        title_label = ttk.Label(header_frame, text="网络网关修改工具", 
                               font=('Segoe UI', 18, 'bold'), foreground='#0078d4')
        title_label.pack()
        
        adapter_frame = ttk.LabelFrame(self.root, text="网络适配器")
        adapter_frame.pack(fill='x', padx=20, pady=5)
        
        self.adapter_list = tk.Listbox(adapter_frame, height=5, font=('Segoe UI', 10))
        self.adapter_list.pack(fill='x', padx=10, pady=10)
        self.adapter_list.bind('<<ListboxSelect>>', self.select_adapter)
        
        gateway_frame = ttk.LabelFrame(self.root, text="自定义网关地址")
        gateway_frame.pack(fill='x', padx=20, pady=5)
        
        gateway_input_frame = ttk.Frame(gateway_frame)
        gateway_input_frame.pack(padx=10, pady=10)
        
        ttk.Label(gateway_input_frame, text="网关:").pack(side='left', padx=5)
        self.gateway_entry = ttk.Entry(gateway_input_frame, width=20, font=('Segoe UI', 11))
        self.gateway_entry.insert(0, self.config['custom_gateway'])
        self.gateway_entry.pack(side='left', padx=5)
        
        save_btn = ttk.Button(gateway_input_frame, text="保存", command=self.save_gateway)
        save_btn.pack(side='left', padx=10)
        
        mode_frame = ttk.Frame(self.root)
        mode_frame.pack(fill='x', padx=20, pady=15)
        
        self.mode_label = ttk.Label(mode_frame, text="", font=('Segoe UI', 12))
        self.mode_label.pack(pady=5)
        
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        self.switch_btn = ttk.Button(btn_frame, text="切换模式", 
                                     command=lambda: self.set_custom_gateway() if self.current_mode != 'custom' else self.set_dhcp())
        self.switch_btn.pack(side='left', padx=5)
        
        refresh_btn = ttk.Button(btn_frame, text="刷新", command=self.update_ui)
        refresh_btn.pack(side='left', padx=5)
        
        self.update_ui()
        
        try:
            result = subprocess.run(['net', 'session'], capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                messagebox.showwarning("权限警告", "建议以管理员身份运行以获得完整功能")
        except:
            pass
        
        self.root.mainloop()

if __name__ == "__main__":
    app = GatewayApp()
    app.run()