# script.ps1

$ALLOWED_DIRS = "members", "public", "shared", "backend", "server"
$IGNORE_DIRS = "content"  # Directories to ignore
$FILE_TYPES = "*.css", "*.js", "*.html", "*.py", "*.env"
$EXTRA_FILES = "members/js/referrals.js"

# Loop through each file type in the current directory
foreach ($fileType in $FILE_TYPES) {
    Get-ChildItem -Filter $fileType | ForEach-Object {
        if ($_.Exists) {
            Write-Output "===== Contents of $($_.Name) ====="
            Get-Content $_.FullName
            Write-Output "============================="
            Write-Output ""
        }
    }
}

# Loop through each file type in allowed subdirectories
foreach ($dir in $ALLOWED_DIRS) {
    if (Test-Path $dir -PathType Container) {
        Write-Output "===== Directory: $dir ====="
        foreach ($fileType in $FILE_TYPES) {
            # Use -Exclude to skip files in ignored directories
            Get-ChildItem -Path $dir -Filter $fileType -Recurse -File -Exclude $IGNORE_DIRS | ForEach-Object {
                # Additional check to ensure the file path does not contain any ignored directories
                $skip = $false
                foreach ($ignoreDir in $IGNORE_DIRS) {
                    if ($_.FullName -like "*\$ignoreDir\*") {
                        $skip = $true
                        break
                    }
                }
                if (-not $skip) {
                    Write-Output "----- Contents of $($_.FullName) -----"
                    Get-Content $_.FullName
                    Write-Output "-----------------------------"
                    Write-Output ""
                }
            }
        }
    }
}

# Process extra files
foreach ($extraFile in $EXTRA_FILES) {
    if (Test-Path $extraFile -PathType Leaf) {
        Write-Output "===== Extra File: $extraFile ====="
        Get-Content $extraFile
        Write-Output "============================="
        Write-Output ""
    }
}