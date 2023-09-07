<#
.SYNOPSIS
    Uninstalls all versions of Zoom using information from the Windows Registry.

.DESCRIPTION
    The script queries the Windows Registry for installed versions of Zoom under both the 32-bit and 64-bit uninstall paths,
    as well as for the current user. It then uses the uninstall string provided by the registry to uninstall each found version of Zoom
    and reports the scope of the installation (system-wide or user-specific) along with its version.

.NOTES
    File Name      : Uninstall-Zoom.ps1
    Author         : Dan Clancey
    Prerequisite   : PowerShell V3
    Date           : 28-Aug-2023
    Version        : 1.0

.EXAMPLE
    .\Uninstall-Zoom.ps1

    This will find and uninstall all versions of Zoom present on the system, including those installed just for the current user, and report the scope and version.

#>

# Ensure the target directory exists
$directory = "C:\tmp"
if (-not (Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory -Force
}

$outputFile = "C:\tmp\Uninstall-Zoom.txt"

$uninstallPaths = @{
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall' = 'System-wide'
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall' = 'System-wide'
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall' = 'User-specific'
}

$zoomKeys = @()

foreach ($path in $uninstallPaths.Keys) {
    $zoomKeys += Get-ChildItem -Path $path | Where-Object { (Get-ItemProperty -Path $_.PsPath).DisplayName -like '*Zoom*' } | ForEach-Object {
        [PSCustomObject]@{
            Key          = $_.PsPath
            DisplayName  = (Get-ItemProperty -Path $_.PsPath).DisplayName
            Version      = (Get-ItemProperty -Path $_.PsPath).DisplayVersion
            InstallScope = $uninstallPaths[$path]
            UninstallString = (Get-ItemProperty -Path $_.PsPath).UninstallString
        }
    }
}

function WriteLog {
    param (
        [Parameter(Mandatory=$true)]
        [string]$message
    )

    # Format current date and time
    $currentDateTime = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

    # Prefix message with current date and time
    $logMessage = "[$currentDateTime] $message"

    Write-Output $logMessage
    Add-Content -Path $outputFile -Value $logMessage
}

foreach ($zoom in $zoomKeys) {
    $message = "Uninstalling $($zoom.DisplayName) (Version: $($zoom.Version)) [Install Scope: $($zoom.InstallScope)]..."

    WriteLog $message

    if ($zoom.UninstallString) {
        # Execute the uninstall command
        Start-Process -Wait -FilePath "cmd.exe" -ArgumentList "/c $($zoom.UninstallString) /quiet /norestart"

        $completedMessage = "$($zoom.DisplayName) (Version: $($zoom.Version)) has been uninstalled."

        WriteLog $completedMessage
    }
}

if (-not $zoomKeys) {
    $noZoomMessage = "No Zoom versions found."
    WriteLog $noZoomMessage
}
