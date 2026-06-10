import subprocess
import re
import sys
import os
import customtkinter as ctk
from tkinter import messagebox, ttk

# 设置Win11风格主题
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Windows隐藏子进程窗口
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes
    
    def hide_console_windows():
        """隐藏所有子进程的窗口"""
        kernel32 = ctypes.windll.kernel32
        
        startupinfo = ctypes.Structure(ctypes.c_void_p)
        class STARTUPINFO(ctypes.Structure):
            _fields_ = [
                ('cb', wintypes.DWORD),
                ('lpReserved', wintypes.LPWSTR),
                ('lpDesktop', wintypes.LPWSTR),
                ('lpTitle', wintypes.LPWSTR),
                ('dwX', wintypes.DWORD),
                ('dwY', wintypes.DWORD),
                ('dwXSize', wintypes.DWORD),
                ('dwYSize', wintypes.DWORD),
                ('dwXCountChars', wintypes.DWORD),
                ('dwYCountChars', wintypes.DWORD),
                ('dwFillAttribute', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD),
                ('wShowWindow', wintypes.WORD),
                ('cbReserved2', wintypes.WORD),
                ('lpReserved2', ctypes.c_void_p),
                ('hStdInput', wintypes.HANDLE),
                ('hStdOutput', wintypes.HANDLE),
                ('hStdError', wintypes.HANDLE),
            ]
        
        si = STARTUPINFO()
        si.cb = ctypes.sizeof(STARTUPINFO)
        si.dwFlags = 0x00000001 | 0x00000080  # STARTF_USESHOWWINDOW | STARTF_FORCEONFEEDBACK
        si.wShowWindow = 0  # SW_HIDE
        
        return si
    
    def get_startup_info():
        try:
            return hide_console_windows()
        except:
            return None
else:
    def get_startup_info():
        return None

class GatewayChangerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("网络配置修改工具")
        self.root.geometry("700x750")
        self.root.resizable(False, False)
        
        # 检查管理员权限
        self.check_admin_rights()
        
        # 创建主框架
        self.main_frame = ctk.CTkFrame(root, corner_radius=12, fg_color="#f8f9fa")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 创建标题区域
        self.create_header()
        
        # 创建网络适配器列表
        self.create_adapter_list()
        
        # 创建网关设置区域
        self.create_gateway_panel()
        
        # 刷新适配器列表
        self.refresh_adapters()
    
    def check_admin_rights(self):
        try:
            result = subprocess.run(
                ['net', 'session'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=get_startup_info()
            )
            if result.returncode != 0:
                messagebox.showwarning(
                    "权限警告",
                    "当前程序未以管理员身份运行，部分功能可能受限。\n建议右键选择'以管理员身份运行'。"
                )
        except:
            pass
    
    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_frame, corner_radius=8, fg_color="#0078d4")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="网络网关修改工具",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        )
        title_label.pack(padx=20, pady=15)
    
    def create_adapter_list(self):
        list_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
        list_frame.pack(fill="x", padx=10, pady=5)
        
        list_header = ctk.CTkFrame(list_frame, corner_radius=6, fg_color="#f1f3f4")
        list_header.pack(fill="x", padx=8, pady=8)
        
        ctk.CTkLabel(
            list_header,
            text="网络适配器",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f1f1f"
        ).pack(side="left", padx=12, pady=8)
        
        self.refresh_btn = ctk.CTkButton(
            list_header,
            text="刷新",
            command=self.refresh_adapters,
            width=80,
            height=28,
            corner_radius=6,
            fg_color="#0078d4",
            hover_color="#005a9e"
        )
        self.refresh_btn.pack(side="right", padx=8)
        
        # 树视图
        self.tree = ttk.Treeview(list_frame, columns=("name", "index", "gateway"), show="headings", height=6)
        self.tree.heading("name", text="适配器名称")
        self.tree.heading("index", text="索引")
        self.tree.heading("gateway", text="当前网关")
        self.tree.column("name", width=250)
        self.tree.column("index", width=80, anchor="center")
        self.tree.column("gateway", width=180)
        
        # 设置Win11风格样式
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#ffffff",
                        foreground="#1f1f1f",
                        rowheight=28,
                        fieldbackground="#ffffff")
        style.configure("Treeview.Heading",
                        background="#f1f3f4",
                        foreground="#1f1f1f",
                        font=('Segoe UI', 10, 'bold'))
        style.map("Treeview",
                  background=[('selected', '#0078d4')],
                  foreground=[('selected', 'white')])
        
        self.tree.pack(fill="x", padx=8, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self.on_adapter_select)
        
        self.selected_adapter = None
    
    def create_gateway_panel(self):
        panel_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
        panel_frame.pack(fill="x", padx=10, pady=10)
        
        panel_label = ctk.CTkLabel(
            panel_frame,
            text="网络配置设置",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f1f1f"
        )
        panel_label.pack(padx=12, pady=(10, 5), anchor="w")
        
        # IP地址输入
        ip_frame = ctk.CTkFrame(panel_frame, corner_radius=6, fg_color="#f8f9fa")
        ip_frame.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            ip_frame,
            text="IP 地址:",
            font=ctk.CTkFont(size=12),
            text_color="#333333"
        ).pack(side="left", padx=12, pady=12)
        
        self.ip_entry = ctk.CTkEntry(
            ip_frame,
            width=200,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            placeholder_text="例如: 192.168.1.100"
        )
        self.ip_entry.pack(side="left", padx=10)
        
        # 子网掩码输入
        subnet_frame = ctk.CTkFrame(panel_frame, corner_radius=6, fg_color="#f8f9fa")
        subnet_frame.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            subnet_frame,
            text="子网掩码:",
            font=ctk.CTkFont(size=12),
            text_color="#333333"
        ).pack(side="left", padx=12, pady=12)
        
        self.subnet_entry = ctk.CTkEntry(
            subnet_frame,
            width=200,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            placeholder_text="例如: 255.255.255.0",
            state="readonly"
        )
        self.subnet_entry.insert(0, "255.255.255.0")
        self.subnet_entry.pack(side="left", padx=10)
        
        # 网关输入
        gateway_frame = ctk.CTkFrame(panel_frame, corner_radius=6, fg_color="#f8f9fa")
        gateway_frame.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            gateway_frame,
            text="网关地址:",
            font=ctk.CTkFont(size=12),
            text_color="#333333"
        ).pack(side="left", padx=12, pady=12)
        
        self.gateway_entry = ctk.CTkEntry(
            gateway_frame,
            width=200,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            placeholder_text="例如: 192.168.1.1"
        )
        self.gateway_entry.pack(side="left", padx=10)
        
        # DNS输入
        dns_frame = ctk.CTkFrame(panel_frame, corner_radius=6, fg_color="#f8f9fa")
        dns_frame.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            dns_frame,
            text="首选DNS:",
            font=ctk.CTkFont(size=12),
            text_color="#333333"
        ).pack(side="left", padx=12, pady=12)
        
        self.dns_entry = ctk.CTkEntry(
            dns_frame,
            width=200,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            placeholder_text="例如: 8.8.8.8"
        )
        self.dns_entry.insert(0, "8.8.8.8")
        self.dns_entry.pack(side="left", padx=10)
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(panel_frame, corner_radius=6, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        self.set_btn = ctk.CTkButton(
            btn_frame,
            text="设置网络配置",
            command=self.set_gateway,
            width=140,
            height=36,
            corner_radius=8,
            fg_color="#0078d4",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.set_btn.pack(side="left", padx=5)
        self.set_btn.configure(state="disabled")
        
        self.reset_btn = ctk.CTkButton(
            btn_frame,
            text="重置为自动获取",
            command=self.reset_gateway,
            width=140,
            height=36,
            corner_radius=8,
            fg_color="#6c757d",
            hover_color="#5a6268",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.reset_btn.pack(side="left", padx=5)
        self.reset_btn.configure(state="disabled")
        
        # 状态显示
        self.status_label = ctk.CTkLabel(
            panel_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#6c757d"
        )
        self.status_label.pack(padx=12, pady=(0, 10), anchor="w")
    
    def get_network_adapters(self):
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'interfaces'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=get_startup_info()
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
                    gateway, ip, subnet = self.get_current_gateway(idx)
                    adapters.append({'index': idx, 'name': name, 'gateway': gateway, 'ip': ip, 'subnet': subnet})
        
        return adapters
    
    def get_current_gateway(self, adapter_index):
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'show', 'config', adapter_index],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=get_startup_info()
        )
        
        gateway_pattern = re.compile(r'默认网关\s*:\s*(.*)')
        ip_pattern = re.compile(r'IP 地址\s*:\s*(.*)')
        
        # 匹配子网掩码的格式："子网前缀: 192.168.31.0/24 (掩码 255.255.255.0)"
        subnet_pattern = re.compile(r'子网前缀\s*:\s*\d+\.\d+\.\d+\.\d+/\d+\s*\(\s*掩码\s*(\d+\.\d+\.\d+\.\d+)\s*\)')
        
        gateway = '无'
        ip = '192.168.1.100'
        subnet = '255.255.255.0'
        
        if result.stdout:
            match = gateway_pattern.search(result.stdout)
            if match:
                gateway = match.group(1).strip()
            
            match = ip_pattern.search(result.stdout)
            if match:
                ip = match.group(1).strip()
            
            match = subnet_pattern.search(result.stdout)
            if match:
                subnet = match.group(1).strip()
        
        return gateway, ip, subnet
    
    def is_valid_ip(self, ip):
        pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
        match = pattern.match(ip)
        if not match:
            return False
        for part in match.groups():
            if int(part) > 255:
                return False
        return True
    
    def run_netsh_command(self, args):
        """执行netsh命令，处理权限问题"""
        # 构建命令字符串用于日志
        cmd_str = ' '.join(args)
        print(f"执行命令: {cmd_str}")
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=get_startup_info()
        )
        
        print(f"返回码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"错误输出: {result.stderr}")
        
        # 如果命令失败，显示详细错误信息
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            if not error_msg:
                error_msg = "未知错误"
            
            # 检查权限错误
            if '权限' in error_msg or 'access denied' in error_msg.lower():
                messagebox.showerror("权限错误", "需要管理员权限！\n请右键点击启动文件选择'以管理员身份运行'")
            else:
                # 显示详细错误信息
                detail_msg = f"命令执行失败！\n\n命令: {cmd_str}\n\n错误信息:\n{error_msg}"
                messagebox.showerror("设置失败", detail_msg)
        
        return result
    
    def refresh_adapters(self):
        # 清空树视图
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取适配器列表
        self.adapters_data = self.get_network_adapters()
        
        # 添加到树视图
        for adapter in self.adapters_data:
            self.tree.insert("", "end", values=(adapter['name'], adapter['index'], adapter['gateway']))
        
        self.selected_adapter = None
        self.set_btn.configure(state="disabled")
        self.reset_btn.configure(state="disabled")
        self.ip_entry.delete(0, "end")
        self.subnet_entry.configure(state="normal")
        self.subnet_entry.delete(0, "end")
        self.subnet_entry.insert(0, "255.255.255.0")
        self.subnet_entry.configure(state="readonly")
        self.gateway_entry.delete(0, "end")
        self.status_label.configure(text="")
    
    def on_adapter_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            values = self.tree.item(item, "values")
            
            # 从保存的适配器数据中查找完整信息
            adapter_info = None
            for adapter in self.adapters_data:
                if adapter['index'] == values[1]:
                    adapter_info = adapter
                    break
            
            if adapter_info:
                self.selected_adapter = adapter_info
            else:
                self.selected_adapter = {
                    'name': values[0],
                    'index': values[1],
                    'gateway': values[2],
                    'ip': '',
                    'subnet': '255.255.255.0'
                }
            
            self.set_btn.configure(state="normal")
            self.reset_btn.configure(state="normal")
            
            # 自动填充当前的IP地址、子网掩码和网关
            self.ip_entry.delete(0, "end")
            self.ip_entry.insert(0, self.selected_adapter.get('ip', ''))
            
            # 子网掩码只读，显示当前值但不允许修改
            self.subnet_entry.configure(state="normal")
            self.subnet_entry.delete(0, "end")
            self.subnet_entry.insert(0, self.selected_adapter.get('subnet', '255.255.255.0'))
            self.subnet_entry.configure(state="readonly")
            
            self.gateway_entry.delete(0, "end")
            if self.selected_adapter['gateway'] != '无':
                self.gateway_entry.insert(0, self.selected_adapter['gateway'])
            
            self.status_label.configure(text=f"已选择: {self.selected_adapter['name']}")
        else:
            self.selected_adapter = None
            self.set_btn.configure(state="disabled")
            self.reset_btn.configure(state="disabled")
    
    def set_gateway(self):
        if not self.selected_adapter:
            messagebox.showwarning("警告", "请先选择一个网络适配器")
            return
        
        # 获取输入值
        ip_address = self.ip_entry.get().strip()
        gateway_ip = self.gateway_entry.get().strip()
        dns_server = self.dns_entry.get().strip()
        
        # 验证输入
        if not ip_address:
            messagebox.showwarning("警告", "请输入IP地址")
            return
        
        if not self.is_valid_ip(ip_address):
            messagebox.showwarning("警告", "无效的IP地址格式")
            return
        
        if not gateway_ip:
            messagebox.showwarning("警告", "请输入网关地址")
            return
        
        if not self.is_valid_ip(gateway_ip):
            messagebox.showwarning("警告", "无效的网关地址格式")
            return
        
        if not dns_server:
            messagebox.showwarning("警告", "请输入DNS服务器地址")
            return
        
        if not self.is_valid_ip(dns_server):
            messagebox.showwarning("警告", "无效的DNS服务器格式")
            return
        
        # 使用保存的子网掩码，不修改它
        subnet_mask = self.selected_adapter.get('subnet', '255.255.255.0')
        
        self.status_label.configure(text=f"正在设置网络配置...", text_color="#0078d4")
        self.root.update()
        
        # 使用正确的命令格式设置IP和网关，保留原有的子网掩码
        result = self.run_netsh_command(
            ['netsh', 'interface', 'ipv4', 'set', 'address', self.selected_adapter['index'], 'static', ip_address, subnet_mask, gateway_ip]
        )
        
        if result.returncode == 0:
            # 设置DNS服务器
            self.status_label.configure(text=f"正在设置DNS服务器...", text_color="#0078d4")
            self.root.update()
            
            dns_result = self.run_netsh_command(
                ['netsh', 'interface', 'ipv4', 'set', 'dns', self.selected_adapter['index'], 'static', dns_server]
            )
            
            if dns_result.returncode == 0:
                self.status_label.configure(text=f"✓ 网络配置设置成功！", text_color="#28a745")
                self.refresh_adapters()
            else:
                error_msg = dns_result.stderr if dns_result.stderr else "未知错误"
                self.status_label.configure(text=f"✗ DNS设置失败: {error_msg}", text_color="#dc3545")
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            self.status_label.configure(text=f"✗ 设置失败: {error_msg}", text_color="#dc3545")
    
    def reset_gateway(self):
        if not self.selected_adapter:
            messagebox.showwarning("警告", "请先选择一个网络适配器")
            return
        
        if not messagebox.askyesno("确认", "确定要将网络配置重置为自动获取吗？"):
            return
        
        self.status_label.configure(text="正在重置网络配置...", text_color="#0078d4")
        self.root.update()
        
        # 启用DHCP获取IP地址
        result = subprocess.run(
            ['netsh', 'interface', 'ipv4', 'set', 'address', self.selected_adapter['index'], 'dhcp'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=get_startup_info()
        )
        
        if result.returncode == 0:
            # 同时重置DNS为自动获取
            dns_result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'set', 'dns', self.selected_adapter['index'], 'dhcp'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=get_startup_info()
            )
            
            if dns_result.returncode == 0:
                self.status_label.configure(text=f"✓ 网络配置已重置为自动获取", text_color="#28a745")
                self.refresh_adapters()
            else:
                error_msg = dns_result.stderr if dns_result.stderr else "未知错误"
                self.status_label.configure(text=f"✗ DNS重置失败: {error_msg}", text_color="#dc3545")
        else:
            error_msg = result.stderr if result.stderr else "未知错误"
            self.status_label.configure(text=f"✗ 重置失败: {error_msg}", text_color="#dc3545")
            messagebox.showerror("错误", f"重置网络配置失败！\n{error_msg}")

if __name__ == "__main__":
    app = ctk.CTk()
    gateway_app = GatewayChangerApp(app)
    app.mainloop()