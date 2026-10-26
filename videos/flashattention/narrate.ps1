$ErrorActionPreference = 'Stop'
$clipRoot = $PSScriptRoot
$story = Get-Content -LiteralPath (Join-Path $clipRoot 'story.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$audioDir = Join-Path $clipRoot 'audio'
New-Item -ItemType Directory -Path $audioDir -Force | Out-Null
$speaker = New-Object -ComObject SAPI.SpVoice
$chineseVoice = $speaker.GetVoices() | Where-Object { $_.GetDescription() -like '*Huihui*' } | Select-Object -First 1
if (-not $chineseVoice) { throw 'Chinese Huihui voice is unavailable.' }
$speaker.Voice = $chineseVoice
$speaker.Rate = 3
$speaker.Volume = 100
for ($clipIndex = 0; $clipIndex -lt $story.Count; $clipIndex++) {
  $wavePath = Join-Path $audioDir ('{0:D2}.wav' -f $clipIndex)
  $stream = New-Object -ComObject SAPI.SpFileStream
  $stream.Format.Type = 22
  $stream.Open($wavePath, 3, $false)
  $speaker.AudioOutputStream = $stream
  [void]$speaker.Speak($story[$clipIndex].text)
  $stream.Close()
  [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($stream)
}
Write-Output ('Created {0} Chinese narration segments.' -f $story.Count)
