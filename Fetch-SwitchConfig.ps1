<#
.SYNOPSIS
    This script fetches the running configuration from a remote device over SSH and saves it to a text file.

.DESCRIPTION
    The script uses PuTTY's plink utility to connect to a remote device via SSH. It executes the command "show running-config" and saves the output to a text file named "IPADDRESS-DATE.txt", where IPADDRESS is the device's IP address and DATE is the current date and time in the format "yyyyMMddHHmmss".

.PARAMETERS
    -ipAddress  [string]  : The IP address of the remote device.
    -username   [string]  : The username for SSH authentication.
    -password   [string]  : The password for SSH authentication.

.NOTES
    File Name      : Fetch-RemoteConfig.ps1
    Author         : Dan Clancey
    Prerequisite   : PowerShell 
                     PuTTY's plink installed at "C:\Program Files\PuTTY\plink.exe" [or change path for $plinkPath]
                     Sufficient permissions to execute SSH commands and write to the local filesystem.
    Date           : 11-Feb-2019
    Version        : 1.0

.EXAMPLE
    .\Fetch-SwitchConfig.ps1 -ipAddress 192.168.1.1 -username admin -password secret

    This will SSH into the device at 192.168.1.1 using the username "admin" and password "secret", fetch the running configuration, and save it to a text file.
    *** You may need to hit "enter" if prompted for Keyboard-interactive Authentication ***
#>


param(
    [string]$ipAddress,
    [string]$username,
    [string]$password
)

# Check if parameters are set
if (-Not $ipAddress -Or -Not $username -Or -Not $password) {
    Write-Host "Usage: .\fetch-SwitchConfig.ps1 -ipAddress [IP_ADDRESS] -username [USERNAME] -password [PASSWORD]"
    exit 1
}

$plinkPath = "C:\Program Files\PuTTY\plink.exe"
$date = Get-Date -Format "yyyyMMddHHmmss"
$outputFile = "$ipAddress-$date.txt"
$sshCommand = "show running-config"

# Execute SSH and save output to file
& $plinkPath -ssh $ipAddress -l $username -pw $password $sshCommand > $outputFile

# Check if file has been created
if (Test-Path $outputFile) {
    Write-Host "Configuration has been saved to $outputFile"
} else {
    Write-Host "Failed to save configuration."
}
