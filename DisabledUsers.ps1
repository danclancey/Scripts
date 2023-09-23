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