# Import modules using robust paths
. "$PSScriptRoot/core/pr_reviewer.ps1"
. "$PSScriptRoot/core/publisher.ps1"

function Run-SkillDemo {
    Write-Host "--- Ghost Skill: Developer Hero Demo ---" -ForegroundColor Cyan
    
    # 1. Load mock data using robust paths
    $mockBoardPath = "$PSScriptRoot/mocks/project_board.json"
    $gitHistoryPath = "$PSScriptRoot/mocks/git_history.json"

    if (-not (Test-Path $mockBoardPath)) { Write-Error "Board not found: $mockBoardPath"; return }
    if (-not (Test-Path $gitHistoryPath)) { Write-Error "History not found: $gitHistoryPath"; return }

    $mockBoard = Get-Content $mockBoardPath | ConvertFrom-Json
    $gitHistory = Get-Content $gitHistoryPath | ConvertFrom-Json
    $state = @{ tickets = $mockBoard }

    # 2. Simulate PR Opening
    $mockPR = @{ id = 105; title = "[TICKET-101] Fix critical memory leak" }
    
    $reviewResult = Review-PullRequest -PRData $mockPR -ProjectState $state
    Write-Host "Comment Posted on GitHub: '$($reviewResult.comment)'" -ForegroundColor Green

    # 3. Simulate PR without Ticket
    Write-Host "`n---"
    $roguePR = @{ id = 106; title = "Update readme with new logo" }
    $rogueResult = Review-PullRequest -PRData $roguePR -ProjectState $state
    Write-Host "Comment Posted on GitHub: '$($rogueResult.comment)'" -ForegroundColor Red

    # 4. Simulate Daily Stand-up Broadcast
    Write-Host "`n---"
    Write-Host "Triggering Automated Daily Stand-up..." -ForegroundColor Cyan
    
    $standupText = "## Ghost Stand-up Report`n"
    foreach ($commit in $gitHistory) {
        $standupText += "- **$($commit.author)** worked on: $($commit.message)`n"
    }
    
    Publish-DailyStandup -StandupContent $standupText

    Write-Host "`n--- Demo Complete: All 'Invisible' Tasks Handled ---" -ForegroundColor Cyan
}

Run-SkillDemo
