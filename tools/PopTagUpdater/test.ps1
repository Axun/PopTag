$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$framework = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319'
$arguments=@('/nologo','/target:exe',('/out:'+(Join-Path $root 'CoreTests.exe')))
$arguments+=@('System.dll','System.Core.dll','System.Web.Extensions.dll','System.IO.Compression.dll','System.IO.Compression.FileSystem.dll') | ForEach-Object { '/reference:'+(Join-Path $framework $_) }
$arguments+=(Join-Path $root 'UpdateCore.cs'),(Join-Path $root 'CoreTests.cs')
& (Join-Path $framework 'csc.exe') @arguments
if($LASTEXITCODE -ne 0){throw 'Tests did not compile'}
$testRoot=Join-Path $root ('test-results-'+[guid]::NewGuid().ToString('N'))
& (Join-Path $root 'CoreTests.exe') $testRoot
if($LASTEXITCODE -ne 0){throw 'Core tests failed'}
