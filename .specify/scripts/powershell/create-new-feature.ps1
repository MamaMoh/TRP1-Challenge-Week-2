param(
    [Parameter(Mandatory=$false)]
    [string]$Json = "",
    
    [Parameter(Mandatory=$false)]
    [int]$Number = 1,
    
    [Parameter(Mandatory=$false)]
    [string]$ShortName = "feature",
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Description
)

$descriptionText = $Description -join " "

# Calculate branch name and paths
$branchName = "$Number-$ShortName"
$specDir = "specs\$branchName"
$specFile = "$specDir\spec.md"

# Create directory structure
New-Item -ItemType Directory -Force -Path $specDir | Out-Null
New-Item -ItemType Directory -Force -Path "$specDir\checklists" | Out-Null

# Create branch
git checkout -b $branchName 2>&1 | Out-Null

# Create empty spec file
New-Item -ItemType File -Force -Path $specFile | Out-Null

# Output JSON with paths
$output = @{
    BRANCH_NAME = $branchName
    SPEC_FILE = $specFile
    FEATURE_DIR = $specDir
    NUMBER = $Number
    SHORT_NAME = $ShortName
    DESCRIPTION = $descriptionText
} | ConvertTo-Json -Compress

Write-Output $output
