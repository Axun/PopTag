$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$csc = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$framework = Split-Path $csc
$references = @('System.dll','System.Core.dll','System.Drawing.dll','System.Windows.Forms.dll','System.Management.dll','System.Web.Extensions.dll','System.Net.Http.dll','System.IO.Compression.dll','System.IO.Compression.FileSystem.dll')
$arguments = @('/nologo','/target:winexe','/optimize+',('/out:' + (Join-Path $root 'PopTagLauncher.exe')))
$arguments += $references | ForEach-Object { '/reference:' + (Join-Path $framework $_) }
$arguments += (Join-Path $root 'UpdateCore.cs'),(Join-Path $root 'Launcher.cs')
& $csc @arguments
if($LASTEXITCODE -ne 0) { throw 'Launcher compilation failed' }
Write-Output 'Built PopTagLauncher.exe'
