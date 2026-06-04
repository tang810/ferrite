[CmdletBinding()]
param(
    [int]$IntervalSeconds = 600,
    [switch]$Once
)

$ErrorActionPreference = "Stop"

$BaseDir = "D:\ferrite\aaaaaaaaximukeji"
$MonitorDir = Join-Path $BaseDir "round2_working\hybrid_outer_layer\monitor"
$CsvPath = Join-Path $MonitorDir "hybrid_aedt_monitor.csv"
$EventPath = Join-Path $MonitorDir "hybrid_aedt_monitor_events.log"
$LicenseLog = Join-Path $env:TEMP ".ansys\licdebug.$env:COMPUTERNAME.MAXWELLCOMENGINE.EXE.252.out"

if (-not (Test-Path -LiteralPath $MonitorDir)) {
    New-Item -ItemType Directory -Path $MonitorDir | Out-Null
}

function Write-EventLine {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -LiteralPath $EventPath -Value $line
    Write-Host $line
}

function Get-LatestMaxwellEngine {
    Get-Process MAXWELLCOMENGINE -ErrorAction SilentlyContinue |
        Sort-Object StartTime -Descending |
        Select-Object -First 1
}

function Get-LatestFile {
    param([string]$Directory)
    if (-not (Test-Path -LiteralPath $Directory)) {
        return $null
    }
    Get-ChildItem -LiteralPath $Directory -File -Force -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function Read-SafeRetCode {
    param([string]$SolverDir)
    $path = Join-Path $SolverDir "SafeRetCode"
    if (-not (Test-Path -LiteralPath $path)) {
        return ""
    }
    $content = Get-Content -LiteralPath $path -Raw -ErrorAction SilentlyContinue
    if ($content -match "^\s*(\d+)") {
        return $Matches[1]
    }
    return ($content -replace "[\r\n]+", " ").Trim()
}

function Get-NewLicenseErrors {
    param(
        [string]$Path,
        [datetime]$Since
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }
    $file = Get-Item -LiteralPath $Path
    if ($file.LastWriteTime -le $Since) {
        return @()
    }
    $tail = Get-Content -LiteralPath $Path -Tail 120 -ErrorAction SilentlyContinue
    $errors = @()
    foreach ($line in $tail) {
        if ($line -notmatch "^(?<timestamp>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+.*\b(ERROR|DENIED|FAILED)\b") {
            continue
        }
        $timestamp = [datetime]::ParseExact(
            $Matches["timestamp"],
            "yyyy/MM/dd HH:mm:ss",
            [System.Globalization.CultureInfo]::InvariantCulture)
        if ($timestamp -gt $Since) {
            $errors += $line
        }
    }
    return $errors
}

if (-not (Test-Path -LiteralPath $CsvPath)) {
    @(
        "timestamp",
        "engine_pid",
        "engine_start",
        "engine_responding",
        "engine_cpu_s",
        "engine_cpu_delta_s",
        "engine_read_ops",
        "engine_read_ops_delta",
        "engine_write_ops",
        "engine_write_ops_delta",
        "engine_read_bytes",
        "engine_read_bytes_delta",
        "engine_write_bytes",
        "engine_write_bytes_delta",
        "solver_dir",
        "solver_file_count",
        "solver_latest_file",
        "solver_latest_write",
        "safe_ret_code",
        "initial_ngmesh_exists",
        "setup1bef_rec_g3d_exists",
        "license_log_write",
        "new_license_error_count"
    ) -join "," | Set-Content -LiteralPath $CsvPath
}

$previous = $null
$previousLicenseCheck = Get-Date
Write-EventLine "monitor_start interval_seconds=$IntervalSeconds once=$Once"

do {
    $now = Get-Date
    $engine = Get-LatestMaxwellEngine

    if ($null -eq $engine) {
        $row = [pscustomobject]@{
            timestamp                  = $now.ToString("yyyy-MM-dd HH:mm:ss")
            engine_pid                 = ""
            engine_start               = ""
            engine_responding          = ""
            engine_cpu_s               = ""
            engine_cpu_delta_s         = ""
            engine_read_ops            = ""
            engine_read_ops_delta      = ""
            engine_write_ops           = ""
            engine_write_ops_delta     = ""
            engine_read_bytes          = ""
            engine_read_bytes_delta    = ""
            engine_write_bytes         = ""
            engine_write_bytes_delta   = ""
            solver_dir                 = ""
            solver_file_count          = ""
            solver_latest_file         = ""
            solver_latest_write        = ""
            safe_ret_code              = ""
            initial_ngmesh_exists      = ""
            setup1bef_rec_g3d_exists   = ""
            license_log_write          = ""
            new_license_error_count    = ""
        }
        $row | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Append
        Write-EventLine "engine_missing MAXWELLCOMENGINE is not running"
        $previous = $null
    }
    else {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($engine.Id)"
        $solverDir = Join-Path $env:TEMP ("maxwell_{0}_{1}.pjt" -f $env:COMPUTERNAME, $engine.Id)
        $latest = Get-LatestFile -Directory $solverDir
        $files = @()
        if (Test-Path -LiteralPath $solverDir) {
            $files = @(Get-ChildItem -LiteralPath $solverDir -File -Force -ErrorAction SilentlyContinue)
        }

        $cpu = [double]$engine.CPU
        $readOps = [int64]$proc.ReadOperationCount
        $writeOps = [int64]$proc.WriteOperationCount
        $readBytes = [int64]$proc.ReadTransferCount
        $writeBytes = [int64]$proc.WriteTransferCount
        $sameProcess = $null -ne $previous -and $previous.engine_pid -eq $engine.Id

        $licenseLogWrite = ""
        if (Test-Path -LiteralPath $LicenseLog) {
            $licenseLogWrite = (Get-Item -LiteralPath $LicenseLog).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
        $licenseErrors = @(Get-NewLicenseErrors -Path $LicenseLog -Since $previousLicenseCheck)

        $safeRetCode = Read-SafeRetCode -SolverDir $solverDir
        $ngmesh = Test-Path -LiteralPath (Join-Path $solverDir "initial.ngmesh")
        $g3d = Test-Path -LiteralPath (Join-Path $solverDir "Setup1bef_rec.g3d")

        $row = [pscustomobject]@{
            timestamp                  = $now.ToString("yyyy-MM-dd HH:mm:ss")
            engine_pid                 = $engine.Id
            engine_start               = $engine.StartTime.ToString("yyyy-MM-dd HH:mm:ss")
            engine_responding          = $engine.Responding
            engine_cpu_s               = [math]::Round($cpu, 3)
            engine_cpu_delta_s         = if ($sameProcess) { [math]::Round($cpu - $previous.engine_cpu_s, 3) } else { "" }
            engine_read_ops            = $readOps
            engine_read_ops_delta      = if ($sameProcess) { $readOps - $previous.engine_read_ops } else { "" }
            engine_write_ops           = $writeOps
            engine_write_ops_delta     = if ($sameProcess) { $writeOps - $previous.engine_write_ops } else { "" }
            engine_read_bytes          = $readBytes
            engine_read_bytes_delta    = if ($sameProcess) { $readBytes - $previous.engine_read_bytes } else { "" }
            engine_write_bytes         = $writeBytes
            engine_write_bytes_delta   = if ($sameProcess) { $writeBytes - $previous.engine_write_bytes } else { "" }
            solver_dir                 = $solverDir
            solver_file_count          = $files.Count
            solver_latest_file         = if ($latest) { $latest.Name } else { "" }
            solver_latest_write        = if ($latest) { $latest.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss") } else { "" }
            safe_ret_code              = $safeRetCode
            initial_ngmesh_exists      = $ngmesh
            setup1bef_rec_g3d_exists   = $g3d
            license_log_write          = $licenseLogWrite
            new_license_error_count    = $licenseErrors.Count
        }
        $row | Export-Csv -LiteralPath $CsvPath -NoTypeInformation -Append

        if (-not $sameProcess) {
            Write-EventLine "engine_detected pid=$($engine.Id) solver_dir=$solverDir"
        }
        if ($licenseErrors.Count -gt 0) {
            Write-EventLine "license_error_detected count=$($licenseErrors.Count)"
        }
        if ($ngmesh -and (-not $sameProcess -or -not $previous.initial_ngmesh_exists)) {
            Write-EventLine "milestone initial.ngmesh detected"
        }
        if ($g3d -and (-not $sameProcess -or -not $previous.setup1bef_rec_g3d_exists)) {
            Write-EventLine "milestone Setup1bef_rec.g3d detected"
        }
        if ($safeRetCode -eq "0" -and (-not $sameProcess -or $previous.safe_ret_code -ne "0")) {
            Write-EventLine "milestone SafeRetCode=0"
        }

        Write-Host ("{0} pid={1} cpu_delta={2}s read_ops_delta={3} write_ops_delta={4} files={5} latest={6} safe={7} ngmesh={8}" -f `
            $row.timestamp, $row.engine_pid, $row.engine_cpu_delta_s, $row.engine_read_ops_delta, `
            $row.engine_write_ops_delta, $row.solver_file_count, $row.solver_latest_file, `
            $row.safe_ret_code, $row.initial_ngmesh_exists)

        $previous = $row
    }

    $previousLicenseCheck = $now
    if (-not $Once) {
        Start-Sleep -Seconds $IntervalSeconds
    }
} while (-not $Once)

Write-EventLine "monitor_stop"
