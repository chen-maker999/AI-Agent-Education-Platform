$ErrorActionPreference = 'Continue'
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/worksheet/ws_1774438445.927106/download' -UseBasicParsing -TimeoutSec 30
    Write-Host "Status: $($r.StatusCode)"
    Write-Host "Content-Type: $($r.ContentType)"
    Write-Host "Size: $($r.Content.Length)"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)"
}
