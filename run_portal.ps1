# ============================================================
# CMS BOA EV Access Compliance Portal
# HTTPS Startup Script
# ============================================================

$ProjectPath = "E:\Projects\AccessCompliancePortal"

$LogDirectory = "$ProjectPath\logs"

$LogFile = "$LogDirectory\portal-startup.log"

# HTTPS Certificate Files
$SSLCertificate = "$ProjectPath\evaccesscheck.cisco.com+2.pem"

$SSLKey = "$ProjectPath\evaccesscheck.cisco.com+2-key.pem"

# ============================================================
# CREATE LOG DIRECTORY
# ============================================================

if (-not (Test-Path $LogDirectory)) {

    New-Item `
        -ItemType Directory `
        -Path $LogDirectory `
        -Force | Out-Null
}


# ============================================================
# STARTUP LOG
# ============================================================

"============================================================" |
    Out-File $LogFile -Append

"CMS BOA EV Access Compliance Portal Startup" |
    Out-File $LogFile -Append

"Startup Time: $(Get-Date)" |
    Out-File $LogFile -Append

"============================================================" |
    Out-File $LogFile -Append


try {

    # ========================================================
    # PROJECT DIRECTORY
    # ========================================================

    "Changing directory to: $ProjectPath" |
        Out-File $LogFile -Append

    Set-Location $ProjectPath

    "Current directory: $(Get-Location)" |
        Out-File $LogFile -Append


    # ========================================================
    # PYTHON EXECUTABLE
    # ========================================================

    $Python = "$ProjectPath\venv\Scripts\python.exe"

    if (-not (Test-Path $Python)) {

        throw "Python executable not found: $Python"
    }

    "Python found: $Python" |
        Out-File $LogFile -Append


    # ========================================================
    # SSL CERTIFICATE CHECK
    # ========================================================

    if (-not (Test-Path $SSLCertificate)) {

        throw "SSL certificate not found: $SSLCertificate"
    }

    if (-not (Test-Path $SSLKey)) {

        throw "SSL private key not found: $SSLKey"
    }

    "SSL certificate found: $SSLCertificate" |
        Out-File $LogFile -Append

    "SSL private key found: $SSLKey" |
        Out-File $LogFile -Append


    # ========================================================
    # START HTTPS SERVER
    # ========================================================

    "Starting CMS BOA EV Access Compliance Portal..." |
        Out-File $LogFile -Append

    "HTTPS URL: https://evaccesscheck.cisco.com:8000" |
        Out-File $LogFile -Append

    "============================================================" |
        Out-File $LogFile -Append


    & $Python -m uvicorn app.main:app `
        --host 0.0.0.0 `
        --port 8000 `
        --ssl-certfile $SSLCertificate `
        --ssl-keyfile $SSLKey `
        *>> $LogFile
}


catch {

    "============================================================" |
        Out-File $LogFile -Append

    "ERROR: $($_.Exception.Message)" |
        Out-File $LogFile -Append

    "STACK: $($_.ScriptStackTrace)" |
        Out-File $LogFile -Append

    "============================================================" |
        Out-File $LogFile -Append

    exit 1
}