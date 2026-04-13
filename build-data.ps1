# build-data.ps1 - Converts data/mattresses.csv to data/mattresses.json
# Run from repo root: .\build-data.ps1

$csvPath = "data\mattresses.csv"
$jsonPath = "data\mattresses.json"

if (-not (Test-Path $csvPath)) {
    Write-Error "CSV not found at $csvPath"
    exit 1
}

$rows = Import-Csv -Path $csvPath

$result = @{ gold = @(); silver = @(); bronze = @() }

foreach ($row in $rows) {
    $tier = $row.tier.Trim().ToLower()
    if (-not $result.ContainsKey($tier)) {
        Write-Warning "Unknown tier '$tier' for mattress $($row.id) - skipping"
        continue
    }

    # Build features array from pipe-delimited features column (scoring tags)
    # Convert kebab-case to camelCase to match quiz score keys
    $features = @()
    if ($row.features -and $row.features.Trim()) {
        $features = $row.features.Split('|') | ForEach-Object {
            $tag = $_.Trim().ToLower()
            # kebab-case to camelCase: split on hyphens, capitalize subsequent parts
            $parts = $tag.Split('-')
            $camel = $parts[0]
            for ($i = 1; $i -lt $parts.Length; $i++) {
                if ($parts[$i].Length -gt 0) {
                    $camel += $parts[$i].Substring(0,1).ToUpper() + $parts[$i].Substring(1)
                }
            }
            $camel
        }
    }

    # Build tags array from pipe-delimited displayBadges (display chips)
    $tags = @()
    if ($row.displayBadges -and $row.displayBadges.Trim()) {
        $tags = $row.displayBadges.Split('|') | ForEach-Object { $_.Trim() }
    }

    # Build reasons object from reason_* columns
    $reasons = @{}
    $reasonKeys = @(
        @{ csv = "reason_cooling";          json = "cooling" },
        @{ csv = "reason_pressureRelief";   json = "pressureRelief" },
        @{ csv = "reason_motionIsolation";  json = "motionIsolation" },
        @{ csv = "reason_support";          json = "support" },
        @{ csv = "reason_plush";            json = "plush" },
        @{ csv = "reason_medium";           json = "medium" },
        @{ csv = "reason_firm";             json = "firm" },
        @{ csv = "reason_durability";       json = "durability" },
        @{ csv = "reason_default";          json = "default" }
    )
    foreach ($rk in $reasonKeys) {
        $val = $row.($rk.csv)
        if ($val -and $val.Trim()) {
            $reasons[$rk.json] = $val.Trim()
        }
    }

    # Parse firmness score
    $firmness = 5
    if ($row.firmnessScore -and $row.firmnessScore.Trim()) {
        $firmness = [int]$row.firmnessScore.Trim()
    }

    # Parse locally-made to boolean
    $locallyMade = $false
    if ($row.'locally-made' -and $row.'locally-made'.Trim().ToLower() -eq 'yes') {
        $locallyMade = $true
    }

    $subBrand = ""
    if ($row.subBrand -and $row.subBrand.Trim()) { $subBrand = $row.subBrand.Trim() }
    $firmnessLbl = ""
    if ($row.firmnessLabel -and $row.firmnessLabel.Trim()) { $firmnessLbl = $row.firmnessLabel.Trim() }
    $highlight = ""
    if ($row.highlight -and $row.highlight.Trim()) { $highlight = $row.highlight.Trim() }

    $mattress = [ordered]@{
        id            = $row.id.Trim()
        name          = $row.name.Trim()
        brand         = $row.brand.Trim()
        subBrand      = $subBrand
        firmness      = $firmness
        firmnessLabel = $firmnessLbl
        locallyMade   = $locallyMade
        features      = $features
        tags          = $tags
        highlight     = $highlight
        reasons       = $reasons
    }

    $result[$tier] += $mattress
}

# Convert to JSON and write
$json = $result | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($jsonPath, $json, (New-Object System.Text.UTF8Encoding $false))

$counts = "gold: $($result.gold.Count), silver: $($result.silver.Count), bronze: $($result.bronze.Count)"
Write-Host "Built $jsonPath - $counts"
