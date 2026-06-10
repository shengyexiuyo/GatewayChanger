<#
.SYNOPSIS
Windows 网络网关修改工具

.DESCRIPTION
用于查看和修改Windows系统网络适配器的默认网关地址

.NOTES
需要以管理员身份运行
#>

function Get-NetworkAdapters {
    param(
        [switch]$All
    )
    
    $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -or $All }
    
    $result = @()
    foreach ($adapter in $adapters) {
        $ipConfig = Get-NetIPConfiguration -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue
        
        $gateway = if ($ipConfig.IPv4DefaultGateway) {
            $ipConfig.IPv4DefaultGateway.NextHop
        } else {
            "无"
        }
        
        $ipAddress = if ($ipConfig.IPv4Address) {
            $ipConfig.IPv4Address.IPAddress
        } else {
            "无"
        }
        
        $result += [PSCustomObject]@{
            Index       = $adapter.InterfaceIndex
            Name        = $adapter.Name
            Description = $adapter.InterfaceDescription
            Status      = $adapter.Status
            IPAddress   = $ipAddress
            Gateway     = $gateway
        }
    }
    
    return $result
}

function Set-NetworkGateway {
    param(
        [int]$InterfaceIndex,
        [string]$GatewayIP
    )
    
    try {
        Remove-NetRoute -InterfaceIndex $InterfaceIndex -AddressFamily IPv4 -PrefixDestination '0.0.0.0/0' -Confirm:$false -ErrorAction SilentlyContinue
        
        New-NetRoute -InterfaceIndex $InterfaceIndex -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -NextHop $GatewayIP -Confirm:$false
        
        return $true, $null
    }
    catch {
        return $false, $_.Exception.Message
    }
}

function Test-IPAddress {
    param(
        [string]$IP
    )
    
    $pattern = '^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    
    if ($IP -notmatch $pattern) {
        return $false
    }
    
    foreach ($part in $matches[1..4]) {
        if ([int]$part -gt 255) {
            return $false
        }
    }
    
    return $true
}

function Show-Menu {
    Write-Host "`n"
    Write-Host "="*70
    Write-Host "          Windows 网络网关修改工具 v1.0"
    Write-Host "="*70
    Write-Host "1. 查看所有网络适配器"
    Write-Host "2. 修改网关地址"
    Write-Host "3. 重置网关（自动获取）"
    Write-Host "4. 退出"
    Write-Host "="*70
    Write-Host "请输入选择 [1-4]: " -NoNewline
}

function Show-Adapters {
    $adapters = Get-NetworkAdapters -All
    
    if (-not $adapters) {
        Write-Host "未找到网络适配器" -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n网络适配器列表:"
    Write-Host "-"*70
    $adapters | Format-Table -AutoSize @{n='索引';e={$_.Index}}, @{n='名称';e={$_.Name}}, @{n='状态';e={$_.Status}}, @{n='IP地址';e={$_.IPAddress}}, @{n='网关';e={$_.Gateway}}
    Write-Host "-"*70
}

function Modify-Gateway {
    $adapters = Get-NetworkAdapters -All
    
    if (-not $adapters) {
        Write-Host "未找到网络适配器" -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n选择要修改的适配器:"
    for ($i = 0; $i -lt $adapters.Count; $i++) {
        $adapter = $adapters[$i]
        Write-Host ("{0}. {1} (索引:{2}, 当前网关:{3})" -f ($i + 1), $adapter.Name, $adapter.Index, $adapter.Gateway)
    }
    
    do {
        $selection = Read-Host "请输入适配器编号"
        if ($selection -match '^\d+$') {
            $index = [int]$selection - 1
            if ($index -ge 0 -and $index -lt $adapters.Count) {
                break
            }
        }
        Write-Host "无效的选择，请重新输入" -ForegroundColor Red
    } while ($true)
    
    $selectedAdapter = $adapters[$index]
    
    do {
        $gatewayIP = Read-Host "请输入新的网关地址"
        if (Test-IPAddress $gatewayIP) {
            break
        }
        Write-Host "无效的IP地址格式，请重新输入" -ForegroundColor Red
    } while ($true)
    
    Write-Host ("`n正在将适配器 '{0}' 的网关设置为: {1}" -f $selectedAdapter.Name, $gatewayIP) -ForegroundColor Cyan
    
    $success, $errorMsg = Set-NetworkGateway -InterfaceIndex $selectedAdapter.Index -GatewayIP $gatewayIP
    
    if ($success) {
        Write-Host "`n✓ 网关设置成功！" -ForegroundColor Green
        Start-Sleep -Seconds 1
        $newGateway = (Get-NetIPConfiguration -InterfaceIndex $selectedAdapter.Index).IPv4DefaultGateway.NextHop
        Write-Host ("当前网关已更新为: {0}" -f $newGateway) -ForegroundColor Green
    }
    else {
        Write-Host "`n✗ 网关设置失败！" -ForegroundColor Red
        if ($errorMsg) {
            Write-Host ("错误信息: {0}" -f $errorMsg) -ForegroundColor Red
        }
        Write-Host "请确保以管理员身份运行此程序" -ForegroundColor Yellow
    }
}

function Reset-Gateway {
    $adapters = Get-NetworkAdapters -All
    
    if (-not $adapters) {
        Write-Host "未找到网络适配器" -ForegroundColor Yellow
        return
    }
    
    Write-Host "`n选择要重置的适配器:"
    for ($i = 0; $i -lt $adapters.Count; $i++) {
        $adapter = $adapters[$i]
        Write-Host ("{0}. {1} (索引:{2}, 当前网关:{3})" -f ($i + 1), $adapter.Name, $adapter.Index, $adapter.Gateway)
    }
    
    do {
        $selection = Read-Host "请输入适配器编号"
        if ($selection -match '^\d+$') {
            $index = [int]$selection - 1
            if ($index -ge 0 -and $index -lt $adapters.Count) {
                break
            }
        }
        Write-Host "无效的选择，请重新输入" -ForegroundColor Red
    } while ($true)
    
    $selectedAdapter = $adapters[$index]
    
    Write-Host ("`n正在重置适配器 '{0}' 的网关为自动获取..." -f $selectedAdapter.Name) -ForegroundColor Cyan
    
    try {
        Remove-NetRoute -InterfaceIndex $selectedAdapter.Index -AddressFamily IPv4 -PrefixDestination '0.0.0.0/0' -Confirm:$false -ErrorAction SilentlyContinue
        
        Set-NetIPInterface -InterfaceIndex $selectedAdapter.Index -Dhcp Enabled
        
        Write-Host "`n✓ 网关重置成功！正在获取DHCP配置..." -ForegroundColor Green
        Start-Sleep -Seconds 2
        
        $newGateway = (Get-NetIPConfiguration -InterfaceIndex $selectedAdapter.Index).IPv4DefaultGateway.NextHop
        Write-Host ("当前网关已更新为: {0}" -f $newGateway) -ForegroundColor Green
    }
    catch {
        Write-Host "`n✗ 重置失败！" -ForegroundColor Red
        Write-Host ("错误信息: {0}" -f $_.Exception.Message) -ForegroundColor Red
        Write-Host "请确保以管理员身份运行此程序" -ForegroundColor Yellow
    }
}

function Main {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host "警告：此程序需要管理员权限才能修改网络配置" -ForegroundColor Yellow
        Write-Host "某些功能可能无法正常工作" -ForegroundColor Yellow
        Write-Host ""
    }
    
    do {
        Show-Menu
        $choice = Read-Host
        
        switch ($choice) {
            '1' { Show-Adapters }
            '2' { Modify-Gateway }
            '3' { Reset-Gateway }
            '4' { Write-Host "`n退出程序..."; break }
            default { Write-Host "无效的选择，请输入1-4" -ForegroundColor Red }
        }
        
        if ($choice -ne '4') {
            Read-Host "`n按回车键继续..."
        }
    } while ($choice -ne '4')
}

Main