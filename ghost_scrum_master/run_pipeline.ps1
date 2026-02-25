function Run-GhostPipeline {
    $gitHistoryPath = "ghost_scrum_master/mocks/git_history.json"
    $projectBoardPath = "ghost_scrum_master/mocks/project_board.json"

    if (-not (Test-Path $gitHistoryPath)) {
        Write-Error "Git history not found at $gitHistoryPath"
        return
    }

    $gitHistory = Get-Content $gitHistoryPath | ConvertFrom-Json
    $tickets = Get-Content $projectBoardPath | ConvertFrom-Json

    Write-Host "--- Ghost Scrum Master Pipeline Start ---" -ForegroundColor Cyan
    
    Write-Host "`n[Activity Analysis]" -ForegroundColor Yellow
    Write-Host "## Ghost Stand-up Report"
    foreach ($commit in $gitHistory) {
        Write-Host "- **$($commit.author)** worked on: $($commit.message) (Hash: $($commit.hash.Substring(0,7)))"
    }

    Write-Host "`n[Suggested Board Updates]" -ForegroundColor Yellow
    $updatesFound = $false
    foreach ($commit in $gitHistory) {
        foreach ($ticket in $tickets) {
            if ($commit.message -like "*$($ticket.title)*" -or $commit.message -like "*$($ticket.id)*") {
                $status = "In Progress"
                if ($commit.message -like "*fix*" -or $commit.message -like "*feat*") {
                    $status = "Done"
                }
                Write-Host "Ticket $($ticket.id) -> $status (Mapped from commit: $($commit.message))"
                $updatesFound = $true
            }
        }
    }

    if (-not $updatesFound) {
        Write-Host "No matches found between commits and tickets."
    }

    Write-Host "`n--- Pipeline Complete ---" -ForegroundColor Cyan
}

Run-GhostPipeline
