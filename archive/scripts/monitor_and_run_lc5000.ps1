# PowerShell Monitor Script - Auto-start Lc=5000 after current test
Write-Host "=" * 80
Write-Host "INTELLIGENT TEST MONITOR - LONG INSTANCE TESTING"
Write-Host "=" * 80
Write-Host ""
Write-Host "This script will:"
Write-Host "  1. Monitor for test_long_lc_sweep.py completion"
Write-Host "  2. Automatically start test_long_lc5000.py when ready"
Write-Host ""
Write-Host "Current time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
Write-Host "=" * 80

# Check if Python test is running
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "✅ Python process detected (PID: $($pythonProcesses.Id))"
    Write-Host ""
    Write-Host "Monitoring every 30 seconds for completion..."
    Write-Host "Press Ctrl+C to abort monitoring"
    Write-Host ""
    
    $checkCount = 0
    
    while ($true) {
        $checkCount++
        
        # Check if checkpoint file shows completion
        $latestDir = Get-ChildItem "outputs\long_lc_sweep_*" -Directory -ErrorAction SilentlyContinue | 
                     Sort-Object LastWriteTime -Descending | 
                     Select-Object -First 1
        
        if ($latestDir) {
            $checkpointFile = Join-Path $latestDir.FullName "checkpoint.txt"
            if (Test-Path $checkpointFile) {
                $content = Get-Content $checkpointFile -ErrorAction SilentlyContinue
                if ($content -match "Testing complete") {
                    Write-Host ""
                    Write-Host "=" * 80
                    Write-Host "✅ FIRST TEST COMPLETED! (Detected in checkpoint file)"
                    Write-Host "=" * 80
                    break
                }
            }
        }
        
        # Check if Python process still exists
        $stillRunning = Get-Process python -ErrorAction SilentlyContinue | 
                        Where-Object { $_.Id -eq $pythonProcesses[0].Id }
        
        if (-not $stillRunning) {
            Write-Host ""
            Write-Host "=" * 80
            Write-Host "✅ FIRST TEST COMPLETED! (Process terminated)"
            Write-Host "=" * 80
            Start-Sleep -Seconds 10
            break
        }
        
        # Still running
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[Check #$checkCount] $timestamp - Test still running... (checking again in 30s)"
        Start-Sleep -Seconds 30
    }
    
} else {
    Write-Host "⚠️  WARNING: No Python process detected!"
    Write-Host "The test may have already finished."
    Write-Host ""
    $response = Read-Host "Do you want to start test_long_lc5000.py anyway? (Y/N)"
    
    if ($response -ne 'Y' -and $response -ne 'y') {
        Write-Host "Exiting..."
        exit
    }
}

# Start Lc=5000 test
Write-Host ""
Write-Host "=" * 80
Write-Host "STARTING: test_long_lc5000.py"
Write-Host "=" * 80
Write-Host "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""
Write-Host "⏱️  Estimated runtime: 8-10 hours"
Write-Host ""

python src/tests/test_long_lc5000.py

Write-Host ""
Write-Host "=" * 80
Write-Host "TEST COMPLETE!"
Write-Host "=" * 80
Write-Host "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""