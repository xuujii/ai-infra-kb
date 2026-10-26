$ErrorActionPreference = 'Stop'
$lessons = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'lessons.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$speaker = New-Object -ComObject SAPI.SpVoice
$speaker.Voice = $speaker.GetVoices() | Where-Object { $_.GetDescription() -like '*Huihui*' } | Select-Object -First 1
$speaker.Rate = 3
$speaker.Volume = 100
foreach ($lesson in $lessons) {
  $audioRoot = Join-Path (Join-Path $PSScriptRoot $lesson.slug) 'audio'
  New-Item -ItemType Directory -Path $audioRoot -Force | Out-Null
  for ($clipIndex=0; $clipIndex -lt $lesson.story.Count; $clipIndex++) {
    $stream = New-Object -ComObject SAPI.SpFileStream
    $stream.Format.Type = 22
    $stream.Open((Join-Path $audioRoot ('{0:D2}.wav' -f $clipIndex)), 3, $false)
    $speaker.AudioOutputStream = $stream
    [void]$speaker.Speak($lesson.story[$clipIndex].text)
    $stream.Close()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($stream)
  }
  Write-Output ($lesson.id + ': ' + $lesson.story.Count + ' Chinese narration segments')
}
