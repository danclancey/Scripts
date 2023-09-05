<#
.SYNOPSIS
This PowerShell script lists files from a remote SFTP server and writes their names and last modified dates to an output file.

.DESCRIPTION
The script uses the WinSCP .NET assembly to connect to an SFTP server. It lists all files in a specified remote directory and writes each file's name and last modified time to an output text file named "SFTP-Files.txt".

.PARAMETERS
    -server     [string]  : The remote server address
    -username   [string]  : The username for SFTP authentication.
    -password   [string]  : The password for SFTP authentication.
    -port       [string]  : (Optional) The port number to use for the SFTP connection. The default is 22.
    -remotePath [string]  : The path of the remote directory on the SFTP server to list files from.

.NOTES
    File Name      : Get-SFTPFiles.ps1
    Author         : Dan Clancey
    Prerequisite   : PowerShell 
                     WinSCPnet.dll - WinSCP by default installs it at C:\Program Files (x86)\WinSCP\WinSCPnet.dll
                     Sufficient permissions to connect via SFTP and read files.
    Date           : 05-Sept-2023
    Version        : 1.0

.EXAMPLE
.\Get-SFTPFiles.ps1 -server example.com -username myUsername -password myPassword -remotePath /remote/path/

.NOTES
Make sure to replace the SSH host key fingerprint with your server's fingerprint. The WinSCP .NET assembly (WinSCPnet.dll) should be placed in "C:\Program Files (x86)\WinSCP\" or specified correctly in the Add-Type -Path parameter(Line 52).
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$server,

    [Parameter(Mandatory=$true)]
    [string]$username,

    [Parameter(Mandatory=$true)]
    [string]$password,

    [Parameter(Mandatory=$false)]
    [int]$port = 22,  # Default SFTP port is 22

    [Parameter(Mandatory=$true)]
    [string]$remotePath  # Remote directory path
)

# Output file
$outputFile = "SFTP-Files.txt"

# Load WinSCP .NET assembly
Add-Type -Path "C:\Program Files (x86)\WinSCP\WinSCPnet.dll" #Set to location of WinSCPnet.dll if not default (included with WinSCP install)

# Set up session options
$sessionOptions = New-Object WinSCP.SessionOptions -Property @{
    Protocol = [WinSCP.Protocol]::Sftp
    HostName = $server
    UserName = $username
    Password = $password
    PortNumber = $port
    SshHostKeyFingerprint = "ssh-rsa 2048 iMLID..." # Replace with server fingerprint
}

$session = New-Object WinSCP.Session

try {
    $session.Open($sessionOptions)
    $directoryInfo = $session.ListDirectory($remotePath)

    # Clear the output file if it exists
    if (Test-Path $outputFile) {
        Clear-Content $outputFile
    }

    # Iterate over files and pull names and dates
    foreach ($file in $directoryInfo.Files) {
        $outputLine = "File Name: " + $file.Name + " - Last Modified: " + $file.LastWriteTime
        $outputLine | Out-File -Append $outputFile
    }
}
catch {
    Write-Host ("Error: " + $_.Exception.Message)
}
finally {
    # Disconnect, if connected
    if ($session -ne $null) {
        $session.Dispose()
    }
}
