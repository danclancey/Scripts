<#
.SYNOPSIS
    This script disables all computer objects in Active Directory that have been inactive for over 365 days and writes their Distinguished Names (DN) to a text file.

.DESCRIPTION
    The script searches for computer accounts in Active Directory that have not been active for more than 365 days. For each such computer, it:
    1. Disables the account.
    2. Writes the DN of the disabled computer to a file named "DisabledComputers-DATE.txt" in the C:\tmp directory, where DATE is the current date.

.PARAMETERS
    None. Values are hardcoded into the script.

.NOTES
    File Name      : AD-stalecomps.ps1
    Author         : Dan Clancey
    Prerequisite   : PowerShell with ActiveDirectory Module
                     Sufficient permissions to disable computer objects in AD and write to C:\tmp.
    Date           : 28-Aug-2023
    Version        : 2.0

.EXAMPLE
    .\AD-stalecomps.ps1]

    This will search for inactive computer accounts older than 365 days, disable them, and write their DN to a file in C:\tmp.
#>

# Script begins

Import-Module ActiveDirectory

$date = Get-Date -Format "yyyyMMdd"
$outputFilePath = "C:\tmp\DisabledComputers-$date.txt"

# Search for computer accounts that have been inactive for over 365 days
$inactiveComputers = Search-ADAccount -ComputersOnly -AccountInactive -TimeSpan 365.00:00:00

# Disable the inactive computer accounts and write their DN to the specified file
foreach ($computer in $inactiveComputers) {
    # Disable the computer account
#    Disable-ADAccount -Identity $computer.SamAccountName

    # Write the computer's DN to the file
    $computer.DistinguishedName | Out-File -Append -FilePath $outputFilePath
}

Write-Output "Inactive computer accounts older than 365 days have been disabled and their DN written to $outputFilePath."
