import subprocess
import re
import os

def get_network_adapters():
    """获取所有网络适配器及其信息"""
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
    else:
        return adapters
    
    for line in lines[3:]:
        line = line.strip()
        if not line:
            continue
        
        parts = re.split(r'\s+', line)
        if len(parts) >= 5:
            idx = parts[0]
            name = ' '.join(parts[4:])
            adapters.append({'index': idx, 'name': name})
    
    return adapters

def get_current_gateway(adapter_index):
    """获取指定适配器的当前网关"""
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

def set_gateway(adapter_index, gateway_ip):
    """设置指定适配器的网关"""
    result = subprocess.run(
        ['netsh', 'interface', 'ipv4', 'set', 'address', adapter_index, 'gateway=' + gateway_ip],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    stderr = result.stderr if result.stderr else None
    return result.returncode == 0, stderr

def is_valid_ip(ip):
    """验证IP地址格式是否正确"""
    pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
    match = pattern.match(ip)
    
    if not match:
        return False
    
    for part in match.groups():
        if int(part) > 255:
            return False
    
    return True

def main():
    print("=" * 60)
    print("          Windows 网络网关修改工具")
    print("=" * 60)
    print()
    
    adapters = get_network_adapters()
    
    if not adapters:
        print("未找到网络适配器")
        input("按回车键退出...")
        return
    
    print("可用的网络适配器：")
    for i, adapter in enumerate(adapters, 1):
        gateway = get_current_gateway(adapter['index'])
        print(f"{i}. {adapter['name']}")
        print(f"   索引: {adapter['index']}")
        print(f"   当前网关: {gateway}")
        print()
    
    try:
        selection = int(input("请输入要修改的适配器编号: "))
        if selection < 1 or selection > len(adapters):
            print("无效的选择")
            input("按回车键退出...")
            return
        
        selected_adapter = adapters[selection - 1]
        
        while True:
            gateway_ip = input("请输入新的网关地址: ")
            if is_valid_ip(gateway_ip):
                break
            print("无效的IP地址格式，请重新输入")
        
        print(f"\n正在将适配器 '{selected_adapter['name']}' 的网关设置为: {gateway_ip}")
        print("注意：此操作需要管理员权限")
        
        success, error_msg = set_gateway(selected_adapter['index'], gateway_ip)
        
        if success:
            print("\n✓ 网关设置成功！")
            new_gateway = get_current_gateway(selected_adapter['index'])
            print(f"当前网关已更新为: {new_gateway}")
        else:
            print(f"\n✗ 网关设置失败！")
            if error_msg:
                print(f"错误信息: {error_msg}")
            else:
                print("请确保以管理员身份运行此程序")
    
    except ValueError:
        print("输入无效")
    except Exception as e:
        print(f"发生错误: {e}")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()