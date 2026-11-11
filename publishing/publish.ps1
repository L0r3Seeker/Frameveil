param([string]$Repository = 'L0r3Seeker/Frameveil')
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
if ($Repository -notmatch '^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$') { throw 'Invalid repository name' }
if (!(Get-Command gh -ErrorAction SilentlyContinue)) { throw 'Install GitHub CLI from https://cli.github.com/ and run gh auth login first.' }
if (!(Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required for publisher only.' }
& gh auth status --hostname github.com
if ($LASTEXITCODE -ne 0) { throw 'Run gh auth login before publishing.' }
$owner = $Repository.Split('/')[0]
$account = (& gh api user --jq '.login').Trim()
if ($LASTEXITCODE -ne 0 -or $account -ine $owner) { throw 'Authenticated GitHub account does not match target owner.' }
$manifest = Get-Content -LiteralPath (Join-Path $project 'release/SHA256.json') -Raw | ConvertFrom-Json
$assets = @('Frameveil-0.2.0-Windows-x64.zip','Frameveil-0.2.0-source.zip')
foreach ($name in $assets) {
    $path = Join-Path $project "release/$name"
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $manifest.$name.sha256) { throw "Release hash mismatch: $name" }
}
# Never reuse a checkout or remove a computed directory. Every publishing run gets a new staging path.
$stage = Join-Path $project ('release/publish-source-' + [guid]::NewGuid().ToString('N'))
Expand-Archive -LiteralPath (Join-Path $project 'release/Frameveil-0.2.0-source.zip') -DestinationPath $stage
$checkout = Join-Path $stage 'Frameveil-source'
Push-Location -LiteralPath $checkout
try {
    & git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init failed' }
    & git add --all
    if ($LASTEXITCODE -ne 0) { throw 'git add failed' }
    & git -c user.name=$account -c "user.email=$account@users.noreply.github.com" commit -m 'Release Frameveil 0.2.0 and begin Android port'
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
    & gh repo create $Repository --public --description 'Frameveil - local media virtual camera for Windows; Android port in preparation' --source . --remote origin --push
    if ($LASTEXITCODE -ne 0) { throw 'Repository creation/push failed. Existing repositories are not modified by this script.' }
    $portable = Join-Path $project 'release/Frameveil-0.2.0-Windows-x64.zip'
    $source = Join-Path $project 'release/Frameveil-0.2.0-source.zip'
    $checksums = Join-Path $project 'release/SHA256.json'
    & gh release create v0.2.0 $portable $source $checksums --repo $Repository --target main --title 'Frameveil 0.2.0' --notes-file (Join-Path $project 'publishing/RELEASE-v0.2.0.md')
    if ($LASTEXITCODE -ne 0) { throw 'Release upload failed; repository may already be public. Retry upload in GitHub Releases.' }
    & gh release view v0.2.0 --repo $Repository
} finally { Pop-Location }
