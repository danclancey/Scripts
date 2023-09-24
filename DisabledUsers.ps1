<#
.SYNOPSIS
    Queries Active Directory for disabled user accounts and exports the information to a CSV file.

.DESCRIPTION
    This script queries Active Directory to find all disabled user accounts within a specified Organizational Unit (OU).
    It gathers various details such as first name, last name, email address, and group memberships for each disabled user.
    The gathered data is displayed in a table format and also exported to a CSV file.

.NOTES
    File Name      : Query-DisabledUsers.ps1
    Author         : Dan Clancey
    Prerequisite   : PowerShell V3, Active Directory PowerShell Module
    Date           : 10-Aug-2023
    Version        : 1.0

.EXAMPLE
    .\Query-DisabledUsers.ps1

    This will query the Active Directory for disabled users within the specified OU, gather relevant information, display it in a table, and export it to a CSV file.

#>


Import-Module ActiveDirectory

$outputFile = ".\DisabledUsers.csv"
$Filter = "Enabled -eq `$False"
$userData = New-Object System.Collections.ArrayList

Get-ADUser -SearchBase "OU=MyOU,DC=DOMAIN,DC=local" -Filter $Filter -Properties EmailAddress,Surname,GivenName | ForEach-Object {
    
    $firstName = $_.GivenName
    $lastName = $_.Surname
    $email = $_.EmailAddress
    $groups = ""

    try {
        $groups = (Get-ADPrincipalGroupMembership $_ | ForEach-Object { $_.Name }) -join ', '
    }
    catch {
        $groups = "Error retrieving group membership for $($_.SamAccountName)"
    }

    $userDetails = New-Object PSObject
    Add-Member -inputObject $userDetails -memberType NoteProperty -name "First Name" -value $firstName
    Add-Member -inputObject $userDetails -memberType NoteProperty -name "Last Name" -value $lastName
    Add-Member -inputObject $userDetails -memberType NoteProperty -name "Email Address" -value $email
    Add-Member -inputObject $userDetails -memberType NoteProperty -name "Group Memberships" -value $groups

    $null = $userData.Add($userDetails)
}

$userData | Format-Table
$userData | Export-Csv -Path $outputFile -NoTypeInformation
