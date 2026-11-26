# Measure whole-device DC battery discharge during the local V2 paced benchmark.
# Launch from PowerShell on Windows. No administrator access or settings changes.
[CmdletBinding()]
param(
    [ValidateRange(1, 100000)] [int] $Count = 225,
    [ValidateRange(1, 60000)] [int] $IntervalMs = 100,
    [string] $OutputPath = (Join-Path $PSScriptRoot '../docs/benchmarks/power.json')
)

$ErrorActionPreference = 'Stop'
$workerPath = Join-Path $PSScriptRoot 'benchmark_v2.js'
$nodePath = (Get-Command node -CommandType Application | Select-Object -First 1).Source
$armMs = [long] $Count * $IntervalMs
$pollMs = 2000
$warmupMs = 6000
if ($armMs -lt 15000) { throw 'Allow at least 15 seconds per arm for battery sampling.' }
if (!(Test-Path -LiteralPath $workerPath -PathType Leaf)) { throw "Missing $workerPath" }

# Each active arm occurs once in position 1, twice in 2, and once in 3.
# Classic precedes hybrid in two blocks and follows it in the other two.
$orders = @(
    @('idle', 'classic', 'hybrid'),
    @('idle', 'hybrid', 'classic'),
    @('hybrid', 'classic', 'idle'),
    @('classic', 'hybrid', 'idle')
)

function Read-Battery($watch, $targetMs, $instanceName) {
    $before = $watch.Elapsed.TotalMilliseconds
    $time = [datetime]::UtcNow.ToString('o')
    $sample = [ordered]@{
        utc = $time; target_ms = $targetMs; elapsed_ms = $null; query_ms = $null
        power_online = $null; charging = $null; discharging = $null
        rate_mw = $null; capacity_mwh = $null; valid = $false; issue = $null
    }
    try {
        $query = 'SELECT Active, InstanceName, PowerOnline, Charging, Discharging, DischargeRate, RemainingCapacity FROM BatteryStatus'
        $batteries = @(Get-CimInstance -Namespace root/wmi -Query $query -OperationTimeoutSec 3 |
            Where-Object Active)
        if ($batteries.Count -ne 1 -or $batteries[0].InstanceName -ne $instanceName) {
            throw 'Expected the same single active battery throughout.'
        }
        $b = $batteries[0]
        $sample.power_online = $b.PowerOnline
        $sample.charging = $b.Charging
        $sample.discharging = $b.Discharging
        $sample.rate_mw = $b.DischargeRate
        $sample.capacity_mwh = $b.RemainingCapacity
        if ($b.PowerOnline -ne $false -or $b.Charging -ne $false -or $b.Discharging -ne $true) {
            throw 'Battery is not continuously discharging offline.'
        }
        if ($null -eq $b.DischargeRate -or $b.DischargeRate -le 0 -or $b.DischargeRate -ge [int]::MaxValue) {
            throw 'Missing, zero, or sentinel discharge rate.'
        }
        $sample.valid = $true
    } catch { $sample.issue = $_.Exception.Message }
    $after = $watch.Elapsed.TotalMilliseconds
    $sample.elapsed_ms = [math]::Round(($before + $after) / 2, 2)
    $sample.query_ms = [math]::Round($after - $before, 2)
    [pscustomobject] $sample
}

function Invoke-Arm($mode, $block, $instanceName) {
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = $nodePath
    $start.Arguments = '"{0}" --paced {1} {2} {3}' -f $workerPath, $mode, $Count, $IntervalMs
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardInput = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $p = [System.Diagnostics.Process]::Start($start)
    try {
        $stderr = $p.StandardError.ReadToEndAsync()
        $ready = $p.StandardOutput.ReadLineAsync()
        if (!$ready.Wait(30000) -or $ready.Result -ne 'READY') {
            if ($p.HasExited) { throw "Worker readiness failure: $($stderr.Result)" }
            throw 'Timed out or received unexpected worker output before READY.'
        }
        $stdout = $p.StandardOutput.ReadToEndAsync()
        $started = [datetime]::UtcNow.ToString('o')
        $watch = [System.Diagnostics.Stopwatch]::StartNew()
        $p.StandardInput.WriteLine('')
        $p.StandardInput.Flush()
        $p.StandardInput.Close()
        $samples = @(for ($target = 0; $target -lt $armMs; $target += $pollMs) {
            $wait = [math]::Ceiling($target - $watch.Elapsed.TotalMilliseconds)
            if ($wait -gt 0) { Start-Sleep -Milliseconds $wait }
            Read-Battery $watch $target $instanceName
        })
        if (!$p.WaitForExit([int] [math]::Min([int]::MaxValue, $armMs + 5000))) {
            throw 'Paced worker did not complete.'
        }
        if ($p.ExitCode -ne 0) { throw "Paced worker failed: $($stderr.Result)" }
        $worker = $stdout.Result | ConvertFrom-Json
    } finally {
        if (!$p.HasExited) { $p.Kill(); $p.WaitForExit() }
        $p.Dispose()
    }

    $expected = if ($mode -eq 'idle') { 0 } else { $Count }
    $issues = @()
    if ($worker.count -ne $expected -or $worker.slots -ne $Count -or $null -eq $worker.elapsed_ms -or
        [math]::Abs($worker.elapsed_ms - $armMs) -gt $pollMs / 2) {
        $issues += 'Worker did not match the configured message count, slot count or duration.'
    }
    if (@($samples | Where-Object { !$_.valid }).Count) { $issues += 'Battery readings failed validation.' }
    $window = @($samples | Where-Object { $_.target_ms -ge $warmupMs })
    if (@($window | Where-Object {
        [math]::Abs($_.elapsed_ms - $_.target_ms) -gt $pollMs / 2 -or
        $_.elapsed_ms -ge $worker.elapsed_ms
    }).Count) { $issues += 'A meter sample missed its target or the worker ended before sampling.' }

    $energyMj = 0.0
    $changes = 0
    $capacityDrop = $null
    $meanMw = $null
    $energyJ = $null
    $durationMs = $window[-1].elapsed_ms - $window[0].elapsed_ms
    if ($issues.Count -eq 0) {
        for ($i = 1; $i -lt $window.Count; $i++) {
            $left = $window[$i - 1]
            $right = $window[$i]
            $energyMj += ($left.rate_mw + $right.rate_mw) / 2.0 * ($right.elapsed_ms - $left.elapsed_ms) / 1000
            if ($left.rate_mw -ne $right.rate_mw) { $changes++ }
        }
        $meanMw = [math]::Round(1000 * $energyMj / $durationMs, 2)
        $energyJ = [math]::Round($energyMj / 1000, 4)
        $caps = @($window[0].capacity_mwh, $window[-1].capacity_mwh)
        if (@($caps | Where-Object { $null -eq $_ -or $_ -lt 0 -or $_ -ge [uint32]::MaxValue }).Count -eq 0) {
            $capacityDrop = $caps[0] - $caps[1]
        }
    }
    [pscustomobject]@{
        block = $block; mode = $mode; started_utc = $started; worker = $worker; issues = $issues
        measured_ms = [math]::Round($durationMs, 2); mean_mw = $meanMw; measured_j = $energyJ
        rate_changes_in_window = $changes; capacity_drop_mwh = $capacityDrop; samples = $samples
    }
}

function Get-Spread([double[]] $values) {
    if (!$values -or $values.Count -eq 0) { return $null }
    $stats = $values | Measure-Object -Average -Minimum -Maximum
    $sd = $null
    if ($values.Count -gt 1) {
        $squares = ($values | ForEach-Object { [math]::Pow($_ - $stats.Average, 2) } | Measure-Object -Sum).Sum
        $sd = [math]::Round([math]::Sqrt($squares / ($values.Count - 1)), 2)
    }
    [ordered]@{
        n = $values.Count; mean = [math]::Round($stats.Average, 2); sample_sd = $sd
        min = $stats.Minimum; max = $stats.Maximum
    }
}

$report = [ordered]@{
    started_utc = [datetime]::UtcNow.ToString('o'); finished_utc = $null; status = 'incomplete'; error = $null
    platform = [Environment]::OSVersion.VersionString; powershell = $PSVersionTable.PSVersion.ToString()
    node = (& $nodePath --version); sensor = 'root/wmi BatteryStatus and BatteryStaticData'
    count = $Count; interval_ms = $IntervalMs; arm_ms = $armMs; poll_ms = $pollMs; excluded_first_ms = $warmupMs
    orders = $orders; arms = @(); paired_mw = @(); paired_hybrid_minus_classic_mw = $null
    nominal_delta_j_per_message = $null; zero_change_windows = $null
    notes = @(
        'Local alternating messages between established sessions. Each arm has its own initialized process. Idle uses the same slots and battery polling schedule.',
        'Rate is whole-device battery discharge. utc is the WMI query start and elapsed_ms its midpoint. Mean power uses trapezoidal integration between the first and last retained samples.',
        'A repeated reading may be a cached value or genuine steady power. WMI does not give the sensor refresh time. Capacity differences are quantized and are not used to infer incremental power.',
        'Screen, background tasks, thermal drift and gauge lag can affect short arms. Blocks from one device are paired descriptive observations. A nominal J/message difference divides the paired mean power delta by the offered messages/s.'
    )
}
try {
    $packs = @(Get-CimInstance -Namespace root/wmi -Query 'SELECT Active, InstanceName, Capabilities FROM BatteryStaticData' | Where-Object Active)
    if ($packs.Count -ne 1 -or $null -eq $packs[0].Capabilities -or
        ([long] $packs[0].Capabilities -band 0x40000000)) {
        throw 'Expected a single active battery reporting absolute mW and mWh units.'
    }
    $instance = $packs[0].InstanceName
    $first = Read-Battery ([System.Diagnostics.Stopwatch]::StartNew()) 0 $instance
    $report['preflight'] = $first
    if (!$first.valid) { throw $first.issue }
    for ($i = 0; $i -lt $orders.Count; $i++) {
        foreach ($mode in $orders[$i]) {
            $arm = Invoke-Arm $mode ($i + 1) $instance
            $report.arms += $arm
            if (@($arm.samples | Where-Object { $_.power_online -eq $true -or $_.charging -eq $true }).Count) {
                throw 'Power source changed during the experiment.'
            }
        }
    }
    foreach ($block in 1..$orders.Count) {
        $group = @($report.arms | Where-Object block -eq $block)
        if (@($group | Where-Object { $_.issues.Count }).Count) { continue }
        $idle = ($group | Where-Object mode -eq 'idle').mean_mw
        $classic = ($group | Where-Object mode -eq 'classic').mean_mw
        $hybrid = ($group | Where-Object mode -eq 'hybrid').mean_mw
        $report.paired_mw += [pscustomobject]@{
            block = $block; classic_minus_idle = [math]::Round($classic - $idle, 2)
            hybrid_minus_idle = [math]::Round($hybrid - $idle, 2)
            hybrid_minus_classic = [math]::Round($hybrid - $classic, 2)
        }
    }
    $report.zero_change_windows = @($report.arms | Where-Object { !$_.issues.Count -and !$_.rate_changes_in_window }).Count
    $report.paired_hybrid_minus_classic_mw = Get-Spread @($report.paired_mw | ForEach-Object hybrid_minus_classic)
    if ($report.paired_hybrid_minus_classic_mw) {
        $report.nominal_delta_j_per_message = [math]::Round($report.paired_hybrid_minus_classic_mw.mean * $IntervalMs / 1000000, 6)
    }
    $report.status = if ($report.paired_mw.Count -ne $orders.Count) { 'incomplete' }
        elseif ($report.zero_change_windows -gt 0) { 'completed_with_meter_resolution_warning' }
        else { 'completed' }
} catch { $report.error = $_.Exception.Message }
$report.finished_utc = [datetime]::UtcNow.ToString('o')
$dest = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($dest)) | Out-Null
[IO.File]::WriteAllText($dest, ($report | ConvertTo-Json -Depth 9), (New-Object Text.UTF8Encoding($false)))
Write-Output "$($report.status) | $($report.paired_mw.Count)/$($orders.Count) paired blocks | $dest"
if ($report.status -eq 'incomplete') { Write-Error "Incomplete battery experiment. $($report.error) See $dest." }
