param(
    [string]$pptxFile = "Context_Aware_SDN_Presentation.pptx",
    [string]$pdfFile = "Context_Aware_SDN_Presentation.pdf"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

$fullPptx = Join-Path $scriptDir $pptxFile
$fullPdf = Join-Path $scriptDir $pdfFile

Write-Host "[*] Converting: $fullPptx"
Write-Host "[*] Output PDF: $fullPdf"

if (-not (Test-Path $fullPptx)) {
    Write-Error "PPTX file not found at $fullPptx"
    exit 1
}

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    # Open presentation hidden / read-only (msoFalse = 0)
    $pres = $ppt.Presentations.Open($fullPptx, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    # ppSaveAsPDF format value is 32
    $pres.SaveAs($fullPdf, 32)
    $pres.Close()
    $ppt.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    if (Test-Path $fullPdf) {
        $fileInfo = Get-Item $fullPdf
        Write-Host "[SUCCESS] PDF generated successfully!"
        Write-Host "File: $($fileInfo.FullName)"
        Write-Host "Size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB"
    } else {
        Write-Error "PDF conversion failed: output file not found."
        exit 1
    }
} catch {
    Write-Error "COM Automation error: $_"
    exit 1
}
