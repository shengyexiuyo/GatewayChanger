import subprocess
import re
import os
import json
import sys
import threading
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
except ImportError as e:
    print(f"需要安装依赖库: {e}")
    sys.exit(1)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".gateway_changer_config.json")

class GatewayManager:
    def __init__(self):
        self.config = self.load_config()
        self.tray = None
        self.settings_window = None
        self.current_mode = self.detect_current_mode()
    
    def load_config(self):
        default_config = {
            "adapter_index": "",
            "adapter_name": "",
            "custom_gateway": "192.168.1.1",
            "last_mode": "dhcp"
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
            self.show_notification("错误", "请先选择网络适配器")
            return False
        
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'set', 'address', 
             self.config['adapter_index'], 'gateway=' + self.config['custom_gateway']],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            self.config['last_mode'] = 'custom'
            self.save_config()
            self.current_mode = 'custom'
            self.update_tray_icon()
            self.show_notification("成功", f"已切换到自定义网关\n{self.config['custom_gateway']}")
            return True
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            self.show_notification("失败", f"设置网关失败:\n{error_msg}")
            return False
    
    def set_dhcp(self):
        if not self.config['adapter_index']:
            self.show_notification("错误", "请先选择网络适配器")
            return False
        
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
            self.config['last_mode'] = 'dhcp'
            self.save_config()
            self.current_mode = 'dhcp'
            self.update_tray_icon()
            self.show_notification("成功", "已切换到DHCP自动获取")
            return True
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            self.show_notification("失败", f"切换DHCP失败:\n{error_msg}")
            return False
    
    def detect_current_mode(self):
        if not self.config['adapter_index']:
            return 'unknown'
        
        gateway = self.get_current_gateway(self.config['adapter_index'])
        if gateway == self.config['custom_gateway']:
            return 'custom'
        else:
            return 'dhcp'
    
    def show_notification(self, title, message):
        if self.tray:
            self.tray.notify(title, message)
    
    def create_icon(self, color):
        image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        center = (32, 32)
        radius = 22
        
        draw.ellipse([center[0]-radius, center[1]-radius, 
                      center[0]+radius, center[1]+radius], 
                     fill=color)
        
        draw.arc([center[0]-radius+6, center[1]-radius+6, 
                  center[0]+radius-6, center[1]+radius-6], 
                 0, 270, fill='white', width=4)
        
        draw.point([center[0]+8, center[1]-8], fill='white')
        
        return image
    
    def update_tray_icon(self):
        if self.tray:
            if self.current_mode == 'custom':
                self.tray.icon = self.create_icon((0, 120, 215))
            elif self.current_mode == 'dhcp':
                self.tray.icon = self.create_icon((39, 174, 96))
            else:
                self.tray.icon = self.create_icon((149, 165, 166))
    
    def switch_mode(self):
        if self.current_mode == 'custom':
            self.set_dhcp()
        else:
            self.set_custom_gateway()
    
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        
        self.settings_window = tk.Toplevel()
        self.settings_window.title("网关切换器设置")
        self.settings_window.geometry("500x400")
        self.settings_window.resizable(False, False)
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings)
        
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        
        ttk.Label(self.settings_window, text="网络适配器", style='Header.TLabel').pack(pady=(15, 5), anchor='w', padx=20)
        
        adapters = self.get_network_adapters()
        if adapters:
            adapter_frame = ttk.Frame(self.settings_window)
            adapter_frame.pack(fill='x', padx=20, pady=5)
            
            for adapter in adapters:
                is_selected = adapter['index'] == self.config['adapter_index']
                btn = ttk.Button(
                    adapter_frame,
                    text=f"{adapter['name']} (网关: {adapter['gateway']})",
                    command=lambda a=adapter: self.select_adapter_from_settings(a)
                )
                btn.pack(fill='x', pady=2)
                if is_selected:
                    btn.config(style='Accent.TButton')
        else:
            ttk.Label(self.settings_window, text="未找到网络适配器").pack(pady=5, padx=20)
        
        ttk.Label(self.settings_window, text="自定义网关地址", style='Header.TLabel').pack(pady=(15, 5), anchor='w', padx=20)
        
        gateway_frame = ttk.Frame(self.settings_window)
        gateway_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(gateway_frame, text="网关:").pack(side='left', padx=5)
        self.gateway_entry = ttk.Entry(gateway_frame, width=20, font=('Segoe UI', 11))
        self.gateway_entry.insert(0, self.config['custom_gateway'])
        self.gateway_entry.pack(side='left', padx=5)
        
        save_btn = ttk.Button(self.settings_window, text="保存设置", command=self.save_settings)
        save_btn.pack(pady=15)
        
        ttk.Label(self.settings_window, text=f"当前模式: {self.get_mode_text()}", 
                  foreground=self.get_mode_color()).pack(pady=5)
        
        switch_btn = ttk.Button(self.settings_window, text=f"切换到{self.get_other_mode_text()}", 
                               command=self.switch_mode)
        switch_btn.pack(pady=5)
    
    def get_mode_text(self):
        if self.current_mode == 'custom':
            return f"自定义网关 ({self.config['custom_gateway']})"
        elif self.current_mode == 'dhcp':
            return "DHCP 自动获取"
        return "未知"
    
    def get_mode_color(self):
        if self.current_mode == 'custom':
            return '#0078d4'
        elif self.current_mode == 'dhcp':
            return '#27ae60'
        return '#7f8c8d'
    
    def get_other_mode_text(self):
        if self.current_mode == 'custom':
            return "DHCP"
        return "自定义网关"
    
    def select_adapter_from_settings(self, adapter):
        self.config['adapter_index'] = adapter['index']
        self.config['adapter_name'] = adapter['name']
        self.save_config()
        self.current_mode = self.detect_current_mode()
        self.update_tray_icon()
        messagebox.showinfo("已选择", f"适配器: {adapter['name']}")
        self.open_settings()
    
    def save_settings(self):
        gateway = self.gateway_entry.get().strip()
        if self.is_valid_ip(gateway):
            self.config['custom_gateway'] = gateway
            self.save_config()
            messagebox.showinfo("保存成功", "网关地址已更新")
        else:
            messagebox.showwarning("无效地址", "请输入有效的IP地址")
    
    def close_settings(self):
        self.settings_window.destroy()
        self.settings_window = None
    
    def is_valid_ip(self, ip):
        pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
        match = pattern.match(ip)
        if not match:
            return False
        for part in match.groups():
            if int(part) > 255:
                return False
        return True
    
    def quit_program(self):
        if self.settings_window:
            self.settings_window.destroy()
        self.tray.stop()
    
    def setup_tray(self):
        self.icon = self.create_icon((149, 165, 166))
        
        menu = (
            item(f'当前: {self.get_mode_text()}', None, enabled=False),
            item('切换模式', self.switch_mode, default=True),
            item('设置', self.open_settings),
            item('退出', self.quit_program)
        )
        
        self.tray = pystray.Icon(
            "gateway_changer",
            self.icon,
            "网络网关切换器",
            menu
        )
        
        self.update_tray_icon()
        self.check_admin_rights()
    
    def check_admin_rights(self):
        try:
            result = subprocess.run(
                ['net', 'session'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode != 0:
                self.show_notification("权限警告", "建议以管理员身份运行")
        except:
            pass
    
    def run(self):
        self.setup_tray()
        self.tray.run()

if __name__ == "__main__":
    app = GatewayManager()
    app.run()