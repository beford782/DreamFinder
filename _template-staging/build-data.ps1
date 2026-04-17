# build-data.ps1 - Converts data/mattresses.csv to data/mattresses.json
# Run from repo root: .\build-data.ps1
# Uses $PSScriptRoot so it works regardless of the current working directory.
#
# Exit codes:
#   0 = success (possibly with warnings)
#   1 = hard validation failure (duplicate ids, invalid tier, bad firmness, missing required fields)
#   2 = missing input files

$ErrorActionPreference = "Stop"

$csvPath = Join-Path $PSScriptRoot "data\mattresses.csv"
$jsonPath = Join-Path $PSScriptRoot "data\mattresses.json"
$esCsvPath = Join-Path $PSScriptRoot "data\mattresses-es.csv"

if (-not (Test-Path $csvPath)) {
    Write-Error "CSV not found at $csvPath"
    exit 2
}

$rows = Import-Csv -Path $csvPath

# ── Validation ─────────────────────────────────────────────────────────────
$errors = @()
$warnings = @()

$validTiers = @('gold', 'silver', 'bronze')
$requiredFields = @('id', 'name', 'brand', 'tier', 'firmnessScore', 'firmnessLabel', 'highlight', 'reason_default')
$seenIds = @{}

for ($i = 0; $i -lt $rows.Count; $i++) {
    $row = $rows[$i]
    $lineNo = $i + 2  # +1 for header, +1 for 1-indexing
    $rowLabel = "row $lineNo"
    if ($row.id -and $row.id.Trim()) { $rowLabel = "row $lineNo (id=$($row.id.Trim()))" }

    # Required fields
    foreach ($field in $requiredFields) {
        $val = $row.$field
        if (-not $val -or -not $val.Trim()) {
            $errors += "$rowLabel`: missing required field '$field'"
        }
    }

    # Duplicate id check
    if ($row.id -and $row.id.Trim()) {
        $id = $row.id.Trim()
        if ($seenIds.ContainsKey($id)) {
            $errors += "$rowLabel`: duplicate id '$id' (also on row $($seenIds[$id]))"
        } else {
            $seenIds[$id] = $lineNo
        }
    }

    # Tier check
    if ($row.tier -and $row.tier.Trim()) {
        $tier = $row.tier.Trim().ToLower()
        if ($validTiers -notcontains $tier) {
            $errors += "$rowLabel`: invalid tier '$($row.tier)' (must be gold/silver/bronze)"
        }
    }

    # Firmness score 1-10
    if ($row.firmnessScore -and $row.firmnessScore.Trim()) {
        $scoreStr = $row.firmnessScore.Trim()
        $score = 0
        if (-not [int]::TryParse($scoreStr, [ref]$score)) {
            $errors += "$rowLabel`: firmnessScore '$scoreStr' is not an integer"
        } elseif ($score -lt 1 -or $score -gt 10) {
            $errors += "$rowLabel`: firmnessScore $score out of range (must be 1-10)"
        } else {
            # Firmness label consistency (warning only)
            if ($row.firmnessLabel -and $row.firmnessLabel.Trim()) {
                $label = $row.firmnessLabel.Trim().ToLower()
                $expected = ""
                if ($score -le 3) { $expected = "plush" }
                elseif ($score -le 6) { $expected = "medium" }
                else { $expected = "firm" }
                # Allow compound labels like "Medium-Firm", "Plush-Medium"
                if ($label -notlike "*$expected*") {
                    $warnings += "$rowLabel`: firmnessScore $score typically maps to '$expected' but label is '$($row.firmnessLabel)'"
                }
            }
        }
    }

    # locally-made sanity
    if ($row.'locally-made' -and $row.'locally-made'.Trim()) {
        $lm = $row.'locally-made'.Trim().ToLower()
        if ($lm -ne 'yes' -and $lm -ne 'no') {
            $warnings += "$rowLabel`: locally-made '$($row.'locally-made')' is not yes/no"
        }
    }
}

# Load Spanish translation CSV if it exists
$esLookup = @{}
if (Test-Path $esCsvPath) {
    $esRows = Import-Csv -Path $esCsvPath
    foreach ($esRow in $esRows) {
        if ($esRow.id -and $esRow.id.Trim()) {
            $esLookup[$esRow.id.Trim()] = $esRow
        }
    }
    Write-Host "Loaded $($esLookup.Count) Spanish translations from $esCsvPath"

    # Check for orphans (Spanish ids not in English)
    foreach ($esId in $esLookup.Keys) {
        if (-not $seenIds.ContainsKey($esId)) {
            $warnings += "Spanish CSV has id '$esId' with no matching English row"
        }
    }
    # Check for missing translations
    foreach ($enId in $seenIds.Keys) {
        if (-not $esLookup.ContainsKey($enId)) {
            $warnings += "English id '$enId' has no Spanish translation"
        }
    }
} else {
    Write-Host "No Spanish CSV found at $esCsvPath - skipping Spanish fields"
}

# Report validation results
if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "Warnings ($($warnings.Count)):" -ForegroundColor Yellow
    foreach ($w in $warnings) { Write-Host "  - $w" -ForegroundColor Yellow }
}

if ($errors.Count -gt 0) {
    Write-Host ""
    Write-Host "Errors ($($errors.Count)):" -ForegroundColor Red
    foreach ($e in $errors) { Write-Host "  - $e" -ForegroundColor Red }
    Write-Host ""
    Write-Error "Validation failed. Fix the errors above and re-run."
    exit 1
}

# ── Build JSON ─────────────────────────────────────────────────────────────
$result = @{ gold = @(); silver = @(); bronze = @() }

foreach ($row in $rows) {
    $tier = $row.tier.Trim().ToLower()
    if (-not $result.ContainsKey($tier)) { continue }  # already caught in validation

    # Build features array from pipe-delimited features column (scoring tags)
    # Convert kebab-case to camelCase to match quiz score keys
    $features = @()
    if ($row.features -and $row.features.Trim()) {
        $features = $row.features.Split('|') | ForEach-Object {
            $tag = $_.Trim().ToLower()
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

    $firmness = [int]$row.firmnessScore.Trim()

    $locallyMade = $false
    if ($row.'locally-made' -and $row.'locally-made'.Trim().ToLower() -eq 'yes') {
        $locallyMade = $true
    }

    $subBrand = ""
    if ($row.subBrand -and $row.subBrand.Trim()) { $subBrand = $row.subBrand.Trim() }
    $firmnessLbl = $row.firmnessLabel.Trim()
    $highlight = $row.highlight.Trim()

    # Auto-resolve image URL from images/mattresses/ folder
    $imageUrl = ""
    $imgName = $row.name.Trim().ToLower()
    $imgDir = Join-Path $PSScriptRoot "images\mattresses"
    foreach ($ext in @("webp", "jpg", "png")) {
        if (Test-Path "$imgDir\$imgName.$ext") {
            $imageUrl = "images/mattresses/$imgName.$ext"
            break
        }
    }
    if (-not $imageUrl) {
        Write-Warning "No image found for $($row.id) ($imgName) in $imgDir"
    }

    # Build Spanish fields if translation exists
    $tags_es = @()
    $highlight_es = ""
    $reasons_es = @{}
    $mattressId = $row.id.Trim()
    if ($esLookup.ContainsKey($mattressId)) {
        $esRow = $esLookup[$mattressId]

        if ($esRow.displayBadges -and $esRow.displayBadges.Trim()) {
            $tags_es = $esRow.displayBadges.Split('|') | ForEach-Object { $_.Trim() }
        }
        if ($esRow.highlight -and $esRow.highlight.Trim()) {
            $highlight_es = $esRow.highlight.Trim()
        }
        foreach ($rk in $reasonKeys) {
            $esVal = $esRow.($rk.csv)
            if ($esVal -and $esVal.Trim()) {
                $reasons_es[$rk.json] = $esVal.Trim()
            }
        }
    }

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
        tags_es       = $tags_es
        highlight_es  = $highlight_es
        imageUrl      = $imageUrl
        reasons       = $reasons
        reasons_es    = $reasons_es
    }

    $result[$tier] += $mattress
}

# Convert to JSON and write
$json = $result | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($jsonPath, $json, (New-Object System.Text.UTF8Encoding $false))

$counts = "gold: $($result.gold.Count), silver: $($result.silver.Count), bronze: $($result.bronze.Count)"
Write-Host ""
Write-Host "Built $jsonPath - $counts" -ForegroundColor Green
if ($warnings.Count -gt 0) {
    Write-Host "Completed with $($warnings.Count) warning(s)." -ForegroundColor Yellow
}
